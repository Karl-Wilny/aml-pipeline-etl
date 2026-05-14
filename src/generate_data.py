# generate_data.py
# Génère des données fictives de transactions bancaires pour le pipeline AML

import pandas as pd
import json
import random
from faker import Faker
from datetime import datetime, timedelta
import os

fake = Faker('fr_FR')
random.seed(42)

# ── Paramètres ────────────────────────────────────────────────────────────────
NB_CLIENTS      = 100
NB_TRANSACTIONS = 10000
ANOMALY_RATE    = 0.15  # 15% de transactions suspectes

# ── Génération des clients ────────────────────────────────────────────────────
def generate_clients():
    print("Génération des clients...")
    clients = []
    for i in range(NB_CLIENTS):
        clients.append({
            "client_id"  : f"CLT-{i+1:04d}",
            "nom"        : fake.last_name(),
            "prenom"     : fake.first_name(),
            "pays"       : random.choice([
                              "France", "France", "France",
                              "Allemagne", "Espagne", "Italie",
                              "Panama", "Îles Caïmans", "Suisse"
                           ]),
            "profession" : random.choice([
                              "Salarié", "Dirigeant", "Étudiant",
                              "Retraité", "Indépendant", "Inconnu"
                           ]),
            "date_ouverture_compte" : fake.date_between(
                              start_date="-10y", end_date="-1y"
                           ).isoformat(),
            "risque_inherent" : random.choice(["Faible", "Moyen", "Élevé"])
        })
    return clients

# ── Génération des transactions ───────────────────────────────────────────────
def generate_transactions(clients):
    print("Génération des transactions...")
    transactions = []
    client_ids = [c["client_id"] for c in clients]

    for i in range(NB_TRANSACTIONS):
        is_anomaly = random.random() < ANOMALY_RATE

        # Montant normal : entre 10€ et 5 000€
        # Montant suspect : entre 8 000€ et 95 000€
        if is_anomaly:
            montant = round(random.uniform(8000, 95000), 2)
        else:
            montant = round(random.uniform(10, 5000), 2)

        # Date aléatoire sur les 12 derniers mois
        date_transaction = datetime.now() - timedelta(
            days=random.randint(0, 365)
        )

        transactions.append({
            "transaction_id"   : f"TXN-{i+1:06d}",
            "client_id"        : random.choice(client_ids),
            "date_transaction" : date_transaction.strftime("%Y-%m-%d %H:%M:%S"),
            "montant"          : montant,
            "devise"           : "EUR",
            "type_transaction" : random.choice([
                                    "Virement", "Retrait", "Dépôt",
                                    "Paiement carte", "Virement international"
                                 ]),
            "pays_destination" : random.choice([
                                    "France", "France", "France",
                                    "Allemagne", "Espagne",
                                    "Panama", "Îles Caïmans", "Russie"
                                 ]),
            "est_suspecte"     : is_anomaly
        })

    return transactions

# ── Sauvegarde des fichiers ───────────────────────────────────────────────────
def save_data(clients, transactions):
    print("Sauvegarde des fichiers...")

    # Crée le dossier data s'il n'existe pas
    os.makedirs("data", exist_ok=True)

    # Clients → JSON
    with open("data/clients.json", "w", encoding="utf-8") as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)
    print(f"  → data/clients.json créé ({len(clients)} clients)")

    # Transactions → CSV
    df = pd.DataFrame(transactions)
    df.to_csv("data/transactions.csv", index=False, encoding="utf-8")
    print(f"  → data/transactions.csv créé ({len(transactions)} transactions)")

    # Statistiques rapides
    nb_suspectes = df["est_suspecte"].sum()
    print(f"\nSTATISTIQUES :")
    print(f"  Transactions normales  : {NB_TRANSACTIONS - nb_suspectes}")
    print(f"  Transactions suspectes : {nb_suspectes}")
    print(f"  Taux d'anomalie réel   : {nb_suspectes/NB_TRANSACTIONS*100:.1f}%")
    print(f"  Montant moyen normal   : {df[~df['est_suspecte']]['montant'].mean():.2f}€")
    print(f"  Montant moyen suspect  : {df[df['est_suspecte']]['montant'].mean():.2f}€")

# ── Point d'entrée ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("GÉNÉRATION DES DONNÉES AML — BRF Capital")
    print("=" * 50)

    clients      = generate_clients()
    transactions = generate_transactions(clients)
    save_data(clients, transactions)

    print("\nDonnées générées avec succès.")