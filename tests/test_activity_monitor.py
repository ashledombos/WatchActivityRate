import unittest
from src.package.monitoring import ActivityMonitor  # Ajustez l'import selon la structure de votre projet

class TestActivityMonitor(unittest.TestCase):

    def setUp(self):
        self.config = {
            "sliding_window": 300,
            "activity_duration_threshold": 10,
            "pause_threshold": 5,
            "save_interval": 60
        }
        self.monitor = ActivityMonitor(self.config)

    def test_is_valid_activity(self):
        # Teste le cas où l'activité est valide
        self.monitor.activity_data = [
            {'start': '2023-01-01 12:00:00', 'end': '2023-01-01 12:05:00'},
            {'start': '2023-01-01 12:10:00', 'end': '2023-01-01 12:20:00'}
        ]
        self.assertTrue(self.monitor.is_valid_activity())

    def test_short_duration(self):
        # Teste le cas où la durée de l'activité est trop courte pour être valide
        self.monitor.activity_data = [
            {'start': '2023-01-01 12:00:00', 'end': '2023-01-01 12:01:00'}
        ]
        self.assertFalse(self.monitor.is_valid_activity())

    #def test_pause_threshold(self):
        # À remplir : Teste le cas où une nouvelle activité commence avant que pause_threshold ne soit atteint

    #def test_record_activity(self):
        # À remplir : Teste la méthode record_activity pour vérifier si elle fonctionne comme prévu

if __name__ == '__main__':
    unittest.main()
