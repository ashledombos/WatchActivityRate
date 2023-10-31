import json
import time
import logging
import sqlite3
import threading
import signal
import os
from pynput import keyboard, mouse

exit_lock = threading.Lock()

# Configuration et initialisation du logging
logging.basicConfig(
    filename='monitoring.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Classe DatabaseManager pour gérer la configuration de la base de données
# Axe d'amélioration 1 et 2: Abstraction de la base de données et optimisation des requêtes SQL.
class DatabaseManager:
    DB_NAME = 'activity_data.db'

    # Utilisation d'un constructeur pour initialiser la connexion à la base de données
    def __init__(self):
        self.conn = sqlite3.connect(self.DB_NAME)
        self.configure_db()

    # Configuration initiale de la base de données
    def configure_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY,
            type TEXT,
            start TEXT,
            end TEXT
        )
        ''')
        self.conn.commit()

    # Méthode pour insérer des données
    def insert_activity(self, activity):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO activity (type, start, end)
        VALUES (?, ?, ?)
        ''', (activity['type'], activity['start'], activity['end']))
        self.conn.commit()

# Classe ActivityMonitor pour gérer le monitoring
class ActivityMonitor:
    # Axe d'amélioration 4: Vérification de la configuration.
    def __init__(self, config):
        if not all(key in config for key in ['sliding_window', 'activity_threshold', 'pause_threshold']):
            logging.error("Configuration incomplète. Vérifiez le fichier config.json.")
            raise ValueError("Configuration incomplète")

        self.config = config
        self.activity_data = []
        self.exit_event = threading.Event()
        self.db_manager = DatabaseManager()

    # Axe d'amélioration 3: Ajout de docstrings pour la documentation.
    def on_key_activity(self, key):
        """Callback pour les activités du clavier."""
        try:
            self.record_activity('keyboard')
        except Exception as e:
            logging.error(f"Erreur lors de l'enregistrement de l'activité clavier : {e}")

    def on_mouse_activity(self, x, y, button, pressed):
        """Callback pour les activités de la souris."""
        try:
            if pressed:
                self.record_activity('mouse')
        except Exception as e:
            logging.error(f"Erreur lors de l'enregistrement de l'activité souris : {e}")

    def is_valid_activity(self):
        """Vérifie si l'activité récente dépasse un certain seuil."""
        recent_activity = [
            a for a in self.activity_data
            if time.time() - time.mktime(time.strptime(a['end'], '%Y-%m-%d %H:%M:%S')) < self.config['sliding_window']
        ]
        return len(recent_activity) > self.config['activity_threshold']

    def record_activity(self, activity_type):
        """Enregistre une activité du type spécifié."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        activity = {'type': activity_type, 'start': timestamp, 'end': timestamp}

        if not self.activity_data or self.activity_data[-1]['type'] != activity_type:
            self.activity_data.append(activity)
        else:
            last_activity = self.activity_data[-1]
            inactivity_duration = time.mktime(time.strptime(timestamp, '%Y-%m-%d %H:%M:%S')) - time.mktime(time.strptime(last_activity['end'], '%Y-%m-%d %H:%M:%S'))

            if inactivity_duration <= self.config['pause_threshold']:
                last_activity['end'] = timestamp
            else:
                self.activity_data.append(activity)

        # Utilisation de la méthode insert_activity du DatabaseManager pour insérer l'activité
        self.db_manager.insert_activity(activity)

    def start_monitoring(self):
        """Démarre la surveillance des activités."""
        logging.info(f"Démarrage de la surveillance des activités... PID : {os.getpid()}")
        self.k_listener = keyboard.Listener(on_press=self.on_key_activity)
        self.m_listener = mouse.Listener(on_click=self.on_mouse_activity)
        self.k_listener.daemon = True
        self.m_listener.daemon = True
        self.k_listener.start()
        self.m_listener.start()

    def stop_monitoring(self):
        """Arrête la surveillance des activités."""
        self.k_listener.stop()
        self.m_listener.stop()

    def save_data_to_db(self):
        """Sauvegarde toutes les données d'activité en mémoire dans la base de données."""
        if not self.activity_data:
            return

        for activity in self.activity_data:
            self.db_manager.insert_activity(activity)

    def periodic_save(self):
        """Sauvegarde périodique des données."""
        while not self.exit_event.is_set():
            logging.debug("Sauvegarde périodique en cours.")
            time.sleep(self.config.get('save_interval', 60))
            self.save_data_to_db()

    def start_periodic_save(self):
        """Démarre la sauvegarde périodique."""
        self.save_thread = threading.Thread(target=self.periodic_save)
        self.save_thread.daemon = True
        self.save_thread.start()

    def stop_periodic_save(self):
        """Arrête la sauvegarde périodique."""
        if self.save_thread:
            self.save_thread.join(timeout=5)

# Gestion des signaux pour une sortie propre
def graceful_exit(signum, frame):
    logging.info("Fonction de sortie propre appelée.")
    with exit_lock:
        logging.info("Signal reçu. Arrêt propre...")
        monitor.exit_event.set()
        monitor.stop_periodic_save()
        monitor.stop_monitoring()
        monitor.save_data_to_db()
        os._exit(0)

# Point d'entrée principal
if __name__ == "__main__":
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)

        monitor = ActivityMonitor(config)
        monitor.start_periodic_save()
        signal.signal(signal.SIGINT, graceful_exit)
        signal.signal(signal.SIGTERM, graceful_exit)
        monitor.start_monitoring()

        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                graceful_exit(None, None)
    except Exception as e:
        logging.error(f"Erreur dans le module de surveillance : {e}")
