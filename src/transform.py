# transform.py
# Nettoie, valide et enrichit les données extraites

import pandas as pd
import logging

logger = logging.getLogger(__name__)

# ── Nettoyage des clients ─────────────────────────────────────────────────────
def transform_clients(df_clients):
    logger.info("Transformation des clients...")
    df = df_clients.copy()

    # Supprime les doublons
    nb_avant = len(df)
    df = df.drop_duplicates(subset=["client_id"])
    nb_apres = len(df)
    if nb_avant != nb_apres:
        logger.warning(f"  → {nb_avant - nb_apres} doublons supprimés")

    # Convertit la date d'ouverture en datetime
    df["date_ouverture_compte"] = pd.to_datetime(
        df["date_ouverture_compte"], errors="coerce"
    )

    # Remplace les valeurs manquantes
    df["profession"]      = df["profession"].fillna("Inconnu")
    df["risque_inherent"] = df["risque_inherent"].fillna("Moyen")

    # Ajoute l'ancienneté du compte en années
    df["anciennete_compte"] = (
        pd.Timestamp.now() - df["date_ouverture_compte"]
    ).dt.days / 365

    # Flag pays à risque
    pays_a_risque = ["Panama", "Îles Caïmans", "Russie", "Iran", "Corée du Nord"]
    df["pays_a_risque"] = df["pays"].isin(pays_a_risque)

    logger.info(f"  → {len(df)} clients transformés")
    logger.info(f"  → {df['pays_a_risque'].sum()} clients en pays à risque")
    return df

# ── Nettoyage des transactions ────────────────────────────────────────────────
def transform_transactions(df_transactions):
    logger.info("Transformation des transactions...")
    df = df_transactions.copy()

    # Supprime les doublons
    nb_avant = len(df)
    df = df.drop_duplicates(subset=["transaction_id"])
    logger.info(f"  → {nb_avant - len(df)} doublons supprimés")

    # Convertit la date en datetime
    df["date_transaction"] = pd.to_datetime(
        df["date_transaction"], errors="coerce"
    )

    # Supprime les montants invalides (négatifs ou nuls)
    nb_invalides = (df["montant"] <= 0).sum()
    if nb_invalides > 0:
        logger.warning(f"  → {nb_invalides} montants invalides supprimés")
        df = df[df["montant"] > 0]

    # Supprime les lignes sans date
    nb_sans_date = df["date_transaction"].isna().sum()
    if nb_sans_date > 0:
        logger.warning(f"  → {nb_sans_date} transactions sans date supprimées")
        df = df.dropna(subset=["date_transaction"])

    # Ajoute des colonnes enrichies
    df["heure_transaction"] = df["date_transaction"].dt.hour
    df["jour_semaine"]      = df["date_transaction"].dt.day_name()
    df["mois"]              = df["date_transaction"].dt.month

    # Flag transaction nocturne (entre 23h et 5h)
    df["transaction_nocturne"] = (df["heure_transaction"] >= 22) | (df["heure_transaction"] < 6)

    # Flag pays destination à risque
    pays_a_risque = ["Panama", "Îles Caïmans", "Russie", "Iran", "Corée du Nord"]
    df["destination_a_risque"] = df["pays_destination"].isin(pays_a_risque)

    logger.info(f"  → {len(df)} transactions transformées")
    logger.info(f"  → {df['destination_a_risque'].sum()} transactions vers pays à risque")
    logger.info(f"  → {df['transaction_nocturne'].sum()} transactions nocturnes")
    return df

# ── Fonction d'orchestration (appelée par main.py) ────────────────────────────
def run_transform(df_clients, df_transactions):
    df_clients_clean      = transform_clients(df_clients)
    df_transactions_clean = transform_transactions(df_transactions)
    return df_clients_clean, df_transactions_clean

# ── Point d'entrée pour test ──────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    import logging
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("logs/pipeline.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    from extract import extract_clients, extract_transactions

    print("=" * 50)
    print("TRANSFORMATION DES DONNÉES — BRF Capital")
    print("=" * 50)

    df_clients      = extract_clients()
    df_transactions = extract_transactions()

    df_clients_clean      = transform_clients(df_clients)
    df_transactions_clean = transform_transactions(df_transactions)

    print(f"\nColonnes clients après transformation :")
    print(list(df_clients_clean.columns))

    print(f"\nColonnes transactions après transformation :")
    print(list(df_transactions_clean.columns))

    print(f"\nTransformation terminée avec succès.")

