# =============================================================
# main.py — Orchestrateur du Pipeline ETL & Monitoring AML
# BRF Capital — Détection d'anomalies Anti-Money Laundering
# =============================================================

import logging
import os
import time
from datetime import datetime

# ── Configuration du logger principal ────────────────────────
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

# ── Import des modules du pipeline ───────────────────────────
from src.extract   import run_extract
from src.transform import run_transform
from src.load      import run_load
from src.risk_scoring import run_risk_scoring
from src.alerts    import run_alerts


def afficher_banniere() -> None:
    print("\n" + "=" * 60)
    print("   PIPELINE ETL & MONITORING AML — BRF Capital")
    print("   Détection d'anomalies Anti-Money Laundering")
    print(f"   Démarrage : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")


def afficher_etape(numero: int, titre: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  ÉTAPE {numero}/5 — {titre}")
    print(f"{'─' * 60}")


def afficher_bilan(resultats: dict, duree_totale: float) -> None:
    print("\n" + "=" * 60)
    print("   BILAN DU PIPELINE")
    print("=" * 60)
    print(f"  ✅ Transactions extraites  : {resultats['transactions']:>8,}")
    print(f"  ✅ Clients extraits        : {resultats['clients']:>8,}")
    print(f"  ✅ Transactions en base    : {resultats['transactions']:>8,}")
    print(f"  ✅ Scores calculés         : {resultats['transactions']:>8,}")
    print(f"  🔴 Alertes CRITIQUES       : {resultats['critiques']:>8,}")
    print(f"  🟠 Alertes ÉLEVÉES         : {resultats['elevees']:>8,}")
    print(f"  📁 Base SQLite             : database/aml_database.db")
    print(f"  📁 Export alertes CSV      : data/alertes_aml.csv")
    print(f"  📁 Logs                    : logs/pipeline.log")
    print(f"\n  ⏱  Durée totale            : {duree_totale:.2f} secondes")
    print("=" * 60 + "\n")


def run_pipeline() -> None:
    """Exécute le pipeline complet ETL + Scoring + Alertes."""

    afficher_banniere()
    debut = time.time()
    resultats = {}

    try:
        # ── ÉTAPE 1 : Extraction ─────────────────────────────
        afficher_etape(1, "EXTRACTION")
        t0 = time.time()
        df_clients, df_transactions = run_extract()
        resultats["clients"]      = len(df_clients)
        resultats["transactions"] = len(df_transactions)
        log.info(f"Étape 1 terminée en {time.time() - t0:.2f}s")

        # ── ÉTAPE 2 : Transformation ─────────────────────────
        afficher_etape(2, "TRANSFORMATION")
        t0 = time.time()
        df_clients_t, df_transactions_t = run_transform(df_clients, df_transactions)
        log.info(f"Étape 2 terminée en {time.time() - t0:.2f}s")

        # ── ÉTAPE 3 : Chargement en base ─────────────────────
        afficher_etape(3, "CHARGEMENT EN BASE")
        t0 = time.time()
        run_load(df_clients_t, df_transactions_t)
        log.info(f"Étape 3 terminée en {time.time() - t0:.2f}s")

        # ── ÉTAPE 4 : Scoring de risque ──────────────────────
        afficher_etape(4, "SCORING DE RISQUE")
        t0 = time.time()
        df_scores = run_risk_scoring()
        log.info(f"Étape 4 terminée en {time.time() - t0:.2f}s")

        # ── ÉTAPE 5 : Génération des alertes ─────────────────
        afficher_etape(5, "GÉNÉRATION DES ALERTES")
        t0 = time.time()
        df_alertes = run_alerts()
        resultats["critiques"] = len(df_alertes[df_alertes["niveau_risque"] == "CRITIQUE"])
        resultats["elevees"]   = len(df_alertes[df_alertes["niveau_risque"] == "ÉLEVÉ"])
        log.info(f"Étape 5 terminée en {time.time() - t0:.2f}s")

        # ── Bilan final ──────────────────────────────────────
        duree_totale = time.time() - debut
        afficher_bilan(resultats, duree_totale)
        log.info(f"Pipeline AML terminé avec succès en {duree_totale:.2f}s")

    except Exception as e:
        log.error(f"ERREUR PIPELINE : {e}", exc_info=True)
        raise


# ── Point d'entrée ───────────────────────────────────────────
if __name__ == "__main__":
    run_pipeline()