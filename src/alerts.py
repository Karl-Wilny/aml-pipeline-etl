# =============================================================
# alerts.py — Génération des alertes AML
# BRF Capital — Pipeline ETL & Monitoring AML
# =============================================================

import sqlite3
import pandas as pd
import logging
import os
from datetime import datetime

# ── Configuration du logger ───────────────────────────────────
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

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
DB_PATH    = "database/aml_database.db"
ALERT_CSV  = "data/alertes_aml.csv"
SEUIL_ALERTE = ["CRITIQUE", "ÉLEVÉ"]   # niveaux déclenchant une alerte


def charger_scores(conn: sqlite3.Connection) -> pd.DataFrame:
    """Charge la table risk_scores depuis SQLite."""
    df = pd.read_sql_query("SELECT * FROM risk_scores", conn)
    log.info(f"  → {len(df)} scores chargés depuis 'risk_scores'")
    return df


def filtrer_alertes(df: pd.DataFrame) -> pd.DataFrame:
    """Conserve uniquement les transactions nécessitant une alerte."""
    df_alertes = df[df["niveau_risque"].isin(SEUIL_ALERTE)].copy()
    df_alertes = df_alertes.sort_values("score_risque", ascending=False)
    df_alertes["horodatage_alerte"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df_alertes["statut_alerte"] = "OUVERTE"
    log.info(f"  → {len(df_alertes)} alertes générées")
    return df_alertes


def logger_alertes(df_alertes: pd.DataFrame) -> None:
    """Logue chaque alerte CRITIQUE individuellement, résumé pour ÉLEVÉ."""

    critiques = df_alertes[df_alertes["niveau_risque"] == "CRITIQUE"]
    eleves    = df_alertes[df_alertes["niveau_risque"] == "ÉLEVÉ"]

    log.warning(f"{'='*50}")
    log.warning(f"  RAPPORT D'ALERTES AML — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.warning(f"{'='*50}")

    # Détail ligne par ligne pour les CRITIQUES
    log.warning(f"  🔴 {len(critiques)} ALERTES CRITIQUES :")
    for _, row in critiques.iterrows():
        log.warning(
            f"     TXN {row['transaction_id']} | "
            f"Client {row['client_id']} | "
            f"Montant {row['montant']:>10,.0f} € | "
            f"Dest. {row['pays_destination']:<15} | "
            f"Score {row['score_risque']}/100"
        )

    # Résumé agrégé pour les ÉLEVÉS
    log.warning(f"  🟠 {len(eleves)} ALERTES ÉLEVÉES (top 5) :")
    for _, row in eleves.head(5).iterrows():
        log.warning(
            f"     TXN {row['transaction_id']} | "
            f"Montant {row['montant']:>10,.0f} € | "
            f"Score {row['score_risque']}/100"
        )
    if len(eleves) > 5:
        log.warning(f"     ... et {len(eleves) - 5} alertes ÉLEVÉES supplémentaires")

    log.warning(f"{'='*50}")


def sauvegarder_alertes(df_alertes: pd.DataFrame, conn: sqlite3.Connection) -> None:
    """Sauvegarde les alertes en base SQLite ET en CSV."""

    # Table SQLite
    df_alertes.to_sql("alertes", conn, if_exists="replace", index=False)
    conn.commit()
    log.info(f"  → Table 'alertes' créée en base ({len(df_alertes)} lignes)")

    # Export CSV
    df_alertes.to_csv(ALERT_CSV, index=False, encoding="utf-8-sig")
    log.info(f"  → Export CSV : {ALERT_CSV}")


def afficher_stats(df_alertes: pd.DataFrame) -> None:
    """Affiche un résumé statistique des alertes."""

    print("\n" + "=" * 50)
    print("  RÉSUMÉ DES ALERTES AML")
    print("=" * 50)

    total = len(df_alertes)
    for niveau in ["CRITIQUE", "ÉLEVÉ"]:
        subset = df_alertes[df_alertes["niveau_risque"] == niveau]
        if len(subset) == 0:
            continue
        print(f"\n  {'🔴' if niveau == 'CRITIQUE' else '🟠'} {niveau} — {len(subset)} alertes")
        print(f"     Montant moyen  : {subset['montant'].mean():>12,.0f} €")
        print(f"     Montant max    : {subset['montant'].max():>12,.0f} €")
        print(f"     Score moyen    : {subset['score_risque'].mean():>12.1f} / 100")

        top_pays = subset["pays_destination"].value_counts().head(3)
        print(f"     Top destinations : {', '.join(top_pays.index.tolist())}")

    print(f"\n  Total alertes ouvertes : {total}")
    print(f"  Export CSV : {ALERT_CSV}")
    print("=" * 50)


def run_alerts() -> pd.DataFrame:
    """Point d'entrée principal du module."""
    print("=" * 50)
    print("GÉNÉRATION DES ALERTES AML — BRF Capital")
    print("=" * 50)

    conn = sqlite3.connect(DB_PATH)

    try:
        # 1. Chargement des scores
        log.info("Chargement des scores de risque...")
        df_scores = charger_scores(conn)

        # 2. Filtrage des alertes
        log.info("Filtrage des transactions à alerter...")
        df_alertes = filtrer_alertes(df_scores)

        # 3. Log détaillé des alertes critiques
        logger_alertes(df_alertes)

        # 4. Sauvegarde base + CSV
        log.info("Sauvegarde des alertes...")
        sauvegarder_alertes(df_alertes, conn)

        # 5. Résumé console
        afficher_stats(df_alertes)

        return df_alertes

    finally:
        conn.close()


# ── Exécution directe ────────────────────────────────────────
if __name__ == "__main__":
    run_alerts()