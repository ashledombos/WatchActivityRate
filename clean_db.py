import sqlite3
from datetime import datetime, timedelta

def clean_old_data():
    # Calculer la date limite pour la conservation des données
    cutoff_date = datetime.now() - timedelta(days=(365 + 182))  # 1 an + 6 mois
    cutoff_date_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')

    # Connexion à la base de données SQLite
    conn = sqlite3.connect('activity_data.db')
    cursor = conn.cursor()

    # Supprimer les données plus anciennes que la date limite
    cursor.execute("DELETE FROM activity WHERE datetime(end) < ?", (cutoff_date_str,))
    conn.commit()

    # Fermer la connexion
    conn.close()

# Appeler la fonction pour nettoyer les anciennes données
clean_old_data()
