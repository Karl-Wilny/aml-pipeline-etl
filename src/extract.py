# extract.py
# Lit les données brutes depuis les fichiers CSV et JSON

import pandas as pd
import json
import logging
import os

# ── Configuration du logger ───────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── Extraction des clients (JSON) ─────────────────────────────────────────────
def extract_clients(filepath="data/clients.json"):
    logger.info(f"Extraction clients depuis {filepath}")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            clients = json.load(f)
        df_clients = pd.DataFrame(clients)
        logger.info(f"  → {len(df_clients)} clients extraits")
        return df_clients
    except FileNotFoundError:
        logger.error(f"Fichier introuvable : {filepath}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Erreur de format JSON : {e}")
        raise

# ── Extraction des transactions (CSV) ─────────────────────────────────────────
def extract_transactions(filepath="data/transactions.csv"):
    logger.info(f"Extraction transactions depuis {filepath}")
    try:
        df_transactions = pd.read_csv(filepath, encoding="utf-8")
        logger.info(f"  → {len(df_transactions)} transactions extraites")
        logger.info(f"  → Colonnes : {list(df_transactions.columns)}")
        return df_transactions
    except FileNotFoundError:
        logger.error(f"Fichier introuvable : {filepath}")
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du CSV : {e}")
        raise

# ── Fonction d'orchestration (appelée par main.py) ────────────────────────────
def run_extract():
    df_clients      = extract_clients()
    df_transactions = extract_transactions()
    return df_clients, df_transactions

# ── Point d'entrée pour test ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("EXTRACTION DES DONNÉES — BRF Capital")
    print("=" * 50)

    df_clients      = extract_clients()
    df_transactions = extract_transactions()

    print(f"\nAperçu clients :")
    print(df_clients.head(3).to_string())

    print(f"\nAperçu transactions :")
    print(df_transactions.head(3).to_string())

    print(f"\nExtraction terminée avec succès.")