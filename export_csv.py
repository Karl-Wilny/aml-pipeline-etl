import sqlite3
import pandas as pd

conn = sqlite3.connect('database/aml_database.db')

df_risk = pd.read_sql_query('SELECT * FROM risk_scores', conn)
df_alertes = pd.read_sql_query('SELECT * FROM alertes', conn)
df_clients = pd.read_sql_query('SELECT * FROM clients', conn)

df_risk.to_csv('data/risk_scores.csv', index=False, encoding='utf-8-sig', decimal=',', sep=';')
df_alertes.to_csv('data/alertes_aml.csv', index=False, encoding='utf-8-sig', decimal=',', sep=';')
df_clients.to_csv('data/clients.csv', index=False, encoding='utf-8-sig', decimal=',', sep=';')

conn.close()
print('Export terminé')