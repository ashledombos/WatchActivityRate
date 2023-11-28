import sqlite3
import argparse
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name='data/ab.db'):
        self.db_name = db_name

    def is_activity_present(self, start_time, end_time):
        """ Vérifie si une activité est présente dans la plage de temps donnée. """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # La requête sélectionne toutes les activités qui se chevauchent avec la période donnée
            cursor.execute(''' 
            SELECT COUNT(*) FROM activity 
            WHERE (start < ? AND end > ?) OR (start BETWEEN ? AND ?) OR (end BETWEEN ? AND ?)
            ''', (end_time, start_time, start_time, end_time, start_time, end_time))
            return 1 if cursor.fetchone()[0] > 0 else 0

def parse_date(date_string):
    """ Convertit une chaîne de date en objet datetime. """
    return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')

def main():
    parser = argparse.ArgumentParser(description='Script pour vérifier la présence d\'activité dans une plage horaire.')
    parser.add_argument('--start', help='Heure de début (format YYYY-MM-DD HH:MM:SS)', required=True)
    parser.add_argument('--end', help='Heure de fin (format YYYY-MM-DD HH:MM:SS)', required=True)
    args = parser.parse_args()

    start_time = parse_date(args.start)
    end_time = parse_date(args.end)

    db_manager = DatabaseManager()
    activity_present = db_manager.is_activity_present(start_time, end_time)
    print(activity_present)

if __name__ == '__main__':
    main()