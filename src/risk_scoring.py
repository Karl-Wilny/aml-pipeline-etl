# =============================================================
# risk_scoring.py — Calcul des scores de risque AML
# BRF Capital — Pipeline ETL & Monitoring AML
# =============================================================

import sqlite3
import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime

# ── Configuration du logger ───────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────
DB_PATH = "database/aml_database.db"

PAYS_A_RISQUE = [
    "Panama", "Îles Caïmans", "Bahamas", "Belize",
    "Seychelles", "Vanuatu", "Samoa", "Nauru"
]

# Poids de chaque critère (total possible = 100)
POIDS = {
    "montant_aberrant":     40,   # montant > moyenne + 2*écart-type
    "pays_destination":     25,   # transaction vers pays à risque
    "client_a_risque":      20,   # client domicilié dans pays à risque
    "transaction_nocturne": 15,   # heure entre 22h et 6h
}


def charger_donnees(conn: sqlite3.Connection) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Charge les tables clients et transactions depuis SQLite."""
    log.info("Chargement des données depuis la base SQLite...")

    df_transactions = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_clients = pd.read_sql_query("SELECT * FROM clients", conn)

    log.info(f"  → {len(df_transactions)} transactions chargées")
    log.info(f"  → {len(df_clients)} clients chargés")

    return df_transactions, df_clients


def calculer_seuil_montant(df: pd.DataFrame) -> tuple[float, float]:
    """Calcule moyenne et écart-type des montants pour détection d'aberration."""
    montants_normaux = df[df["est_suspecte"] == False]["montant"]
    moyenne = montants_normaux.mean()
    ecart_type = montants_normaux.std()
    seuil = moyenne + 2 * ecart_type

    log.info(f"  → Montant moyen (normal) : {moyenne:,.0f} €")
    log.info(f"  → Écart-type             : {ecart_type:,.0f} €")
    log.info(f"  → Seuil aberration (μ+2σ): {seuil:,.0f} €")

    return moyenne, seuil


def calculer_heure(date_str: str) -> int:
    """Extrait l'heure depuis une chaîne datetime."""
    try:
        return pd.to_datetime(date_str).hour
    except Exception:
        return 12  # valeur par défaut si parsing échoue


def scorer_transactions(
    df_transactions: pd.DataFrame,
    df_clients: pd.DataFrame,
    seuil_montant: float
) -> pd.DataFrame:
    """Calcule le score de risque (0–100) pour chaque transaction."""

    log.info("Calcul des scores de risque...")

    # Merge pour récupérer le pays du client
    df = df_transactions.merge(
        df_clients[["client_id", "pays"]].rename(columns={"pays": "pays_client"}),
        on="client_id",
        how="left"
    )

    # ── Critère 1 : Montant aberrant ─────────────────────────
    df["score_montant"] = np.where(
        df["montant"] > seuil_montant,
        POIDS["montant_aberrant"],
        0
    )

    # ── Critère 2 : Pays de destination à risque ─────────────
    df["score_pays_destination"] = np.where(
        df["pays_destination"].isin(PAYS_A_RISQUE),
        POIDS["pays_destination"],
        0
    )

    # ── Critère 3 : Client en pays à risque ──────────────────
    df["score_client"] = np.where(
        df["pays_client"].isin(PAYS_A_RISQUE),
        POIDS["client_a_risque"],
        0
    )

    # ── Critère 4 : Transaction nocturne (22h–6h) ────────────
    df["heure"] = pd.to_datetime(df["date_transaction"]).dt.hour
    df["score_nocturne"] = np.where(
        (df["heure"] >= 22) | (df["heure"] < 6),
        POIDS["transaction_nocturne"],
        0
    )

    # ── Score total ──────────────────────────────────────────
    df["score_risque"] = (
        df["score_montant"] +
        df["score_pays_destination"] +
        df["score_client"] +
        df["score_nocturne"]
    )

    # ── Niveau de risque ─────────────────────────────────────
    def niveau(score):
        if score >= 70:
            return "CRITIQUE"
        elif score >= 40:
            return "ÉLEVÉ"
        elif score >= 20:
            return "MODÉRÉ"
        else:
            return "FAIBLE"

    df["niveau_risque"] = df["score_risque"].apply(niveau)

    # ── Statistiques ─────────────────────────────────────────
    log.info("  → Distribution des scores :")
    for niveau_label in ["CRITIQUE", "ÉLEVÉ", "MODÉRÉ", "FAIBLE"]:
        count = (df["niveau_risque"] == niveau_label).sum()
        pct = count / len(df) * 100
        log.info(f"     {niveau_label:<10} : {count:>5} transactions ({pct:.1f}%)")

    return df[[
        "transaction_id", "client_id", "montant", "pays_destination",
        "pays_client", "heure", "est_suspecte",
        "score_montant", "score_pays_destination", "score_client", "score_nocturne",
        "score_risque", "niveau_risque"
    ]]


def sauvegarder_scores(df_scores: pd.DataFrame, conn: sqlite3.Connection) -> None:
    """Insère les scores dans la table risk_scores (remplace si existante)."""
    df_scores["date_calcul"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df_scores.to_sql("risk_scores", conn, if_exists="replace", index=False)
    log.info(f"  → {len(df_scores)} scores sauvegardés dans la table 'risk_scores'")

    # Vue SQL des transactions critiques
    conn.execute("DROP VIEW IF EXISTS v_transactions_critiques")
    conn.execute("""
        CREATE VIEW v_transactions_critiques AS
        SELECT *
        FROM risk_scores
        WHERE niveau_risque = 'CRITIQUE'
        ORDER BY score_risque DESC
    """)
    conn.commit()
    log.info("  → Vue 'v_transactions_critiques' créée")


def run_risk_scoring() -> pd.DataFrame:
    """Point d'entrée principal du module."""
    print("=" * 50)
    print("SCORING DE RISQUE AML — BRF Capital")
    print("=" * 50)

    conn = sqlite3.connect(DB_PATH)

    try:
        # 1. Chargement
        df_transactions, df_clients = charger_donnees(conn)

        # 2. Calcul du seuil statistique
        log.info("Calcul du seuil de montant aberrant...")
        _, seuil = calculer_seuil_montant(df_transactions)

        # 3. Scoring
        df_scores = scorer_transactions(df_transactions, df_clients, seuil)

        # 4. Sauvegarde
        log.info("Sauvegarde des scores en base...")
        sauvegarder_scores(df_scores, conn)

        print(f"\nScoring terminé — {len(df_scores)} transactions scorées")
        print(f"Résultats dans la table 'risk_scores' et vue 'v_transactions_critiques'")

        return df_scores

    finally:
        conn.close()


# ── Exécution directe ────────────────────────────────────────
if __name__ == "__main__":
    run_risk_scoring()