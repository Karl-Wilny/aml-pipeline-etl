# load.py
# Crée la base SQLite et insère les données transformées

import pandas as pd
from sqlalchemy import create_engine, text
import logging
import os

logger = logging.getLogger(__name__)

# ── Connexion à la base SQLite ────────────────────────────────────────────────
def get_engine(db_path="database/aml_database.db"):
    os.makedirs("database", exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")
    logger.info(f"Connexion SQLite établie : {db_path}")
    return engine

# ── Chargement des clients ────────────────────────────────────────────────────
def load_clients(df_clients, engine):
    logger.info("Chargement des clients en base...")
    df = df_clients.copy()

    # Convertit les booléens pour SQLite
    df["pays_a_risque"] = df["pays_a_risque"].astype(int)

    # Convertit les dates en string pour SQLite
    df["date_ouverture_compte"] = df["date_ouverture_compte"].astype(str)

    df.to_sql(
        name="clients",
        con=engine,
        if_exists="replace",
        index=False
    )
    logger.info(f"  → {len(df)} clients chargés dans la table 'clients'")

# ── Chargement des transactions ───────────────────────────────────────────────
def load_transactions(df_transactions, engine):
    logger.info("Chargement des transactions en base...")
    df = df_transactions.copy()

    # Convertit les booléens pour SQLite
    df["est_suspecte"]        = df["est_suspecte"].astype(int)
    df["transaction_nocturne"] = df["transaction_nocturne"].astype(int)
    df["destination_a_risque"] = df["destination_a_risque"].astype(int)

    # Convertit les dates en string pour SQLite
    df["date_transaction"] = df["date_transaction"].astype(str)

    df.to_sql(
        name="transactions",
        con=engine,
        if_exists="replace",
        index=False
    )
    logger.info(f"  → {len(df)} transactions chargées dans la table 'transactions'")

# ── Création des vues SQL ─────────────────────────────────────────────────────
def create_views(engine):
    logger.info("Création des vues SQL...")

    with engine.connect() as conn:

        # Vue 1 — Transactions suspectes avec infos client
        conn.execute(text("""
            CREATE VIEW IF NOT EXISTS v_transactions_suspectes AS
            SELECT
                t.transaction_id,
                t.client_id,
                c.nom,
                c.prenom,
                c.pays,
                c.risque_inherent,
                t.date_transaction,
                t.montant,
                t.type_transaction,
                t.pays_destination,
                t.destination_a_risque
            FROM transactions t
            JOIN clients c ON t.client_id = c.client_id
            WHERE t.est_suspecte = 1
            ORDER BY t.montant DESC
        """))
        logger.info("  → Vue 'v_transactions_suspectes' créée")

        # Vue 2 — Résumé par client
        conn.execute(text("""
            CREATE VIEW IF NOT EXISTS v_resume_client AS
            SELECT
                c.client_id,
                c.nom,
                c.prenom,
                c.pays,
                c.risque_inherent,
                COUNT(t.transaction_id)              AS nb_transactions,
                ROUND(SUM(t.montant), 2)             AS volume_total,
                ROUND(AVG(t.montant), 2)             AS montant_moyen,
                ROUND(MAX(t.montant), 2)             AS montant_max,
                SUM(t.est_suspecte)                  AS nb_suspectes,
                SUM(t.destination_a_risque)          AS nb_destinations_risque
            FROM clients c
            LEFT JOIN transactions t ON c.client_id = t.client_id
            GROUP BY c.client_id
            ORDER BY nb_suspectes DESC
        """))
        logger.info("  → Vue 'v_resume_client' créée")

        conn.commit()

# ── Vérification du chargement ────────────────────────────────────────────────
def verify_load(engine):
    logger.info("Vérification du chargement...")
    with engine.connect() as conn:
        nb_clients = conn.execute(
            text("SELECT COUNT(*) FROM clients")
        ).scalar()
        nb_transactions = conn.execute(
            text("SELECT COUNT(*) FROM transactions")
        ).scalar()
        nb_suspectes = conn.execute(
            text("SELECT COUNT(*) FROM transactions WHERE est_suspecte = 1")
        ).scalar()

    logger.info(f"  → {nb_clients} clients en base")
    logger.info(f"  → {nb_transactions} transactions en base")
    logger.info(f"  → {nb_suspectes} transactions suspectes")
    return nb_clients, nb_transactions, nb_suspectes

# ── Fonction d'orchestration (appelée par main.py) ────────────────────────────
def run_load(df_clients_clean, df_transactions_clean):
    engine = get_engine()
    load_clients(df_clients_clean, engine)
    load_transactions(df_transactions_clean, engine)
    create_views(engine)
    verify_load(engine)

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
    from transform import transform_clients, transform_transactions

    print("=" * 50)
    print("CHARGEMENT EN BASE — BRF Capital")
    print("=" * 50)

    df_clients      = extract_clients()
    df_transactions = extract_transactions()

    df_clients_clean      = transform_clients(df_clients)
    df_transactions_clean = transform_transactions(df_transactions)

    engine = get_engine()
    load_clients(df_clients_clean, engine)
    load_transactions(df_transactions_clean, engine)
    create_views(engine)
    verify_load(engine)

    print(f"\nChargement terminé — base SQLite créée dans database/aml_database.db")