# 🏦 Pipeline ETL & Monitoring AML — BRF Capital

> Détection automatisée d'anomalies financières (Anti-Money Laundering)  
> Pipeline Python end-to-end : ingestion → transformation → scoring de risque → alertes

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey?logo=sqlite)
![Pandas](https://img.shields.io/badge/Pandas-2.0-purple?logo=pandas)
![Status](https://img.shields.io/badge/Status-Terminé-brightgreen)

---

## 🎯 Contexte du projet

**BRF Capital** institution financière fictive traitait ses rapports de conformité AML **manuellement**, avec un délai de détection des anomalies de **7 jours**.

Ce pipeline automatise intégralement la chaîne de détection :

| Avant | Après |
|---|---|
| Détection manuelle : 7 jours | Détection automatisée : **< 2 secondes** |
| 0 scoring de risque | **4 critères AML** pondérés (score /100) |
| Aucune traçabilité | **Logs horodatés** + export CSV |
| Données en silos | **Base SQLite centralisée** + vues SQL |

---

## 🏗️ Architecture du pipeline

```
┌─────────────────────────────────────────────────────────┐
│                    main.py (orchestrateur)               │
└──────────┬──────────────────────────────────────────────┘
           │
    ┌──────▼──────┐    ┌──────────────┐    ┌───────────────┐
    │  extract.py │ →  │ transform.py │ →  │    load.py    │
    │             │    │              │    │               │
    │ clients.json│    │ Nettoyage    │    │ SQLite DB     │
    │ transactions│    │ Enrichissement│    │ 3 tables      │
    │    .csv     │    │ Flags AML    │    │ 2 vues SQL    │
    └─────────────┘    └──────────────┘    └───────┬───────┘
                                                   │
                                    ┌──────────────▼──────────────┐
                                    │       risk_scoring.py        │
                                    │                              │
                                    │  Score 0–100 par transaction │
                                    │  Seuil statistique (μ+2σ)   │
                                    │  4 critères AML pondérés    │
                                    └──────────────┬──────────────┘
                                                   │
                                    ┌──────────────▼──────────────┐
                                    │          alerts.py           │
                                    │                              │
                                    │  105 alertes CRITIQUES       │
                                    │  1 989 alertes ÉLEVÉES       │
                                    │  Export CSV + logs           │
                                    └─────────────────────────────┘
```

---

## 📊 Résultats obtenus

### Volume de données
| Indicateur | Valeur |
|---|---|
| Transactions générées | **10 000** |
| Clients simulés | **100** |
| Transactions suspectes (ground truth) | **1 519 (15,2%)** |
| Transactions vers pays à risque | **3 739 (37,4%)** |
| Clients en pays à risque | **25** |

### Scoring de risque
| Niveau | Transactions | % | Score |
|---|---|---|---|
| 🔴 CRITIQUE | 105 | 1,1% | 85/100 |
| 🟠 ÉLEVÉ | 1 989 | 19,9% | 48–84/100 |
| 🟡 MODÉRÉ | 3 118 | 31,2% | 20–47/100 |
| 🟢 FAIBLE | 4 788 | 47,9% | 0–19/100 |

### Performance
| Métrique | Valeur |
|---|---|
| ⏱ Durée pipeline complet | **1,63 secondes** |
| 📁 Tables SQLite créées | **3** (clients, transactions, risk_scores) |
| 🔍 Vues SQL créées | **3** (suspectes, résumé client, critiques) |
| 📤 Exports générés | **1 CSV** (2 094 alertes) |

---

## 🧮 Modèle de scoring AML

Chaque transaction reçoit un score de **0 à 100** basé sur 4 critères pondérés :

```python
POIDS = {
    "montant_aberrant":     40,  # montant > μ + 2σ des transactions normales
    "pays_destination":     25,  # vers Panama, Îles Caïmans, Bahamas...
    "client_a_risque":      20,  # client domicilié dans pays à risque
    "transaction_nocturne": 15,  # entre 22h et 6h
}
```

**Seuil statistique appliqué :**
- Montant moyen (transactions normales) : **2 498 €**
- Écart-type : **1 433 €**
- Seuil d'aberration (μ + 2σ) : **5 363 €**

---

## 🗂️ Structure du projet

```
aml_pipeline/
├── data/
│   ├── transactions.csv        # 10 000 transactions simulées
│   ├── clients.json            # 100 profils clients
│   └── alertes_aml.csv         # Export des 2 094 alertes (généré)
├── src/
│   ├── generate_data.py        # Génération des données de test (Faker)
│   ├── extract.py              # Lecture CSV / JSON
│   ├── transform.py            # Nettoyage + enrichissement
│   ├── load.py                 # Insertion SQLite + vues SQL
│   ├── risk_scoring.py         # Calcul des scores de risque (μ+2σ)
│   └── alerts.py               # Génération et export des alertes
├── main.py                     # Orchestrateur du pipeline complet
├── requirements.txt            # Dépendances Python
└── README.md
```

---

## 🚀 Installation et utilisation

### Prérequis
- Python 3.10+
- Git

### Installation

```bash
# Cloner le repo
git clone https://github.com/karl-wilny/aml-pipeline-etl.git
cd aml-pipeline-etl

# Créer et activer l'environnement virtuel
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Installer les dépendances
pip install -r requirements.txt
```

### Lancer le pipeline complet

```bash
python main.py
```

### Lancer les modules individuellement

```bash
python src/generate_data.py   # Régénérer les données
python src/extract.py         # Tester l'extraction seule
python src/transform.py       # Tester la transformation
python src/load.py            # Tester le chargement SQLite
python src/risk_scoring.py    # Tester le scoring seul
python src/alerts.py          # Tester la génération d'alertes
```

---

## 🛠️ Stack technique

| Technologie | Usage |
|---|---|
| **Python 3.10+** | Langage principal |
| **Pandas** | Manipulation et transformation des données |
| **NumPy** | Calculs statistiques (μ, σ, seuils) |
| **SQLAlchemy** | ORM et connexion SQLite |
| **SQLite** | Base de données relationnelle (compatible PostgreSQL) |
| **Faker** | Génération de données fictives réalistes |
| **Logging** | Traçabilité horodatée du pipeline |

---

## 👤 Auteur

**Karl Wilny KOUMBA MOUANDA**  
Élève ingénieur 3ème année — ECAM-EPMI  
Spécialisation : Management des SI & Ingénierie Financière

🔗 [Portfolio](https://karl-wilny.github.io/KOUMBA-MOUANDA.github.io/#)  
🔗 [Application de Réservation Ferroviaire — React.js & Node.js](https://github.com/Karl-Wilny/train-ticket-booking)
💼 [LinkedIn](https://www.linkedin.com/in/karl-koumba/)

---

## 📌 Note

Ce projet est une simulation pédagogique réalisée dans le cadre du développement de compétences en Data Engineering et Conformité Financière. Les données, clients et transactions sont entièrement fictifs.