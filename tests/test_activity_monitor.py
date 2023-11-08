import unittest
from datetime import datetime, timedelta

# Assurez-vous d'ajuster l'import selon la structure réelle de votre projet
from src.package.monitoring import ActivityMonitor

class TestActivityMonitor(unittest.TestCase):

    def setUp(self):
        self.config = {
            "periodic_save_minutes": 1,  # Supposons que la sauvegarde se fait toutes les minutes
            "activity_duration_threshold": 1  # Supposons qu'une activité est valide si au moins un événement est détecté
        }
        self.monitor = ActivityMonitor(self.config)
        self.db_manager = DatabaseManager(db_name=':memory:')  # Utilise une base de données en mémoire pour les tests
        self.monitor.db_manager = self.db_manager  # Remplace l'instance de db_manager dans le monitor par celle pour les tests

    def test_is_valid_activity_for_period(self):
        # Teste le cas où l'activité est valide pour la période
        self.monitor.event_count = self.config['activity_duration_threshold']
        self.assertTrue(self.monitor.is_valid_activity_for_period())

    def test_short_duration(self):
        # Teste le cas où la durée de l'activité est trop courte pour être valide
        self.monitor.event_count = 0
        self.assertFalse(self.monitor.is_valid_activity_for_period())

    def test_pause_threshold(self):
        # Teste le cas où une nouvelle activité commence après que pause_threshold soit atteint
        self.monitor.event_count = self.config['activity_duration_threshold']
        self.assertTrue(self.monitor.is_valid_activity_for_period())
        # Simuler une pause
        self.monitor.event_count = 0
        time_to_wait = self.config['activity_duration_threshold'] + 1
        time.sleep(time_to_wait)
        self.assertFalse(self.monitor.is_valid_activity_for_period())

    def test_save_data_to_db(self):
        # Teste la méthode save_data_to_db pour vérifier si elle fusionne correctement les données
        self.monitor.activity_data = [
            {'start': '2023-01-01 12:00:00', 'end': '2023-01-01 12:01:00'}
        ]
        self.monitor.event_count = self.config['activity_duration_threshold']
        # Simuler une période consécutive valide
        new_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_end_time = (datetime.now() + timedelta(minutes=self.config['periodic_save_minutes'])).strftime('%Y-%m-%d %H:%M:%S')
        self.monitor.save_data_to_db()
        self.assertEqual(len(self.monitor.activity_data), 1)
        self.assertEqual(self.monitor.activity_data[0]['end'], new_end_time)

if __name__ == '__main__':
    unittest.main()
