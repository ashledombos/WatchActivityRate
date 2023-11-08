import sqlite3
from datetime import datetime, timedelta

class DatabaseManager:
    """Gestionnaire de la base de données pour l'application de monitoring d'activité.

    Cette classe fournit des méthodes pour configurer, lire et maintenir la base de données SQLite.
    """
    DB_NAME = 'activity_data.db'

class DatabaseManager:
    """Gestionnaire de la base de données pour l'application de monitoring d'activité."""

    def __init__(self, db_name='activity_data.db'):
        """Initialise la base de données en appelant la méthode de configuration."""
        self.DB_NAME = db_name
        self.configure_db()

    def configure_db(self):
        """Configure la base de données.

        Crée la table d'activités si elle n'existe pas déjà.
        """
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY,
                start TEXT,
                end TEXT
            )
            ''')
            conn.commit()

    def save_activity_data(self, activity_data):
        """Sauvegarde les données d'activité dans la base de données SQLite.

        Args:
            activity_data (list): Liste de dictionnaires contenant les données d'activité.
        """
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            for activity in activity_data:
                cursor.execute('''
                INSERT INTO activity (start, end)
                VALUES (?, ?)
                ''', (activity['start'], activity['end']))
            conn.commit()

    def read_data(self, query, params=()):
        """Lit les données de la base de données selon une requête SQL donnée.

        Args:
            query (str): La requête SQL pour lire les données.
            params (tuple, optional): Les paramètres pour la requête SQL. Par défaut à vide.

        Returns:
            list: Liste de dictionnaires contenant les données.
        """
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_last_activity(self):
        """Récupère la dernière entrée d'activité de la base de données."""
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM activity ORDER BY id DESC LIMIT 1")
            last_entry = cursor.fetchone()
            if last_entry:
                return {
                    'id': last_entry[0],
                    'start': last_entry[1],
                    'end': last_entry[2]
                }
            else:
                return None

    def update_activity_end_time(self, activity_id, new_end_time):
        """Mise à jour de l'heure de fin pour une activité donnée."""
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE activity SET end = ? WHERE id = ?", (new_end_time, activity_id))
            conn.commit()

    def clean_old_data(self, age_threshold):
        """Supprime les données plus anciennes qu'un certain seuil.

        Args:
            age_threshold (int): L'âge en jours au-delà duquel les données seront supprimées.
        """
        delete_date = datetime.now() - timedelta(days=age_threshold)
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM activity WHERE start < ?", (delete_date,))
            conn.commit()

    def verify_integrity(self):
        """Vérifie l'intégrité de la base de données.

        Cette méthode peut utiliser des commandes SQLite spécifiques pour vérifier l'intégrité.
        """
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            return cursor.fetchone()[0] == "ok"

    def clean_corrupted_data(self):
        """Nettoie les données corrompues de la base de données.

        Cette méthode identifie et supprime ou corrige les enregistrements corrompus.
        """
        # À implémenter selon les besoins spécifiques de détection et de correction de corruption
