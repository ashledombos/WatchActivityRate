import json
import time
import logging
import sqlite3
import threading
import signal
import os
from pynput import keyboard, mouse

exit_lock = threading.Lock()

# 1. Configuration et initialisation du logging
logging.basicConfig(filename='monitoring.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 2. Classe ActivityMonitor pour gérer le monitoring
class ActivityMonitor:
    def __init__(self, config):
        self.config = config
        self.activity_data = []
        self.exit_event = threading.Event()

    # 2.1. Callbacks pour les événements clavier et souris
    def on_key_activity(self, key):
        try:
            self.record_activity('keyboard')
        except Exception as e:
            logging.error(f"Error recording keyboard activity: {e}")

    def on_mouse_activity(self, x, y, button, pressed):
        try:
            if pressed:
                self.record_activity('mouse')
        except Exception as e:
            logging.error(f"Error recording mouse activity: {e}")

    # 2.2. Logique pour déterminer si une activité est valide
    def is_valid_activity(self):
        recent_activity = [a for a in self.activity_data if time.time() - time.mktime(time.strptime(a['end'], '%Y-%m-%d %H:%M:%S')) < self.config['sliding_window']]
        return len(recent_activity) > self.config['activity_threshold']

    # 2.3. Enregistrement de l'activité
    def record_activity(self, activity_type):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        if not self.activity_data or self.activity_data[-1]['type'] != activity_type:
            self.activity_data.append({
                'type': activity_type,
                'start': timestamp,
                'end': timestamp
            })
        else:
            inactivity_duration = time.mktime(time.strptime(timestamp, '%Y-%m-%d %H:%M:%S')) - time.mktime(time.strptime(self.activity_data[-1]['end'], '%Y-%m-%d %H:%M:%S'))
            if inactivity_duration <= self.config['pause_threshold']:
                self.activity_data[-1]['end'] = timestamp
            else:
                self.activity_data.append({
                    'type': activity_type,
                    'start': timestamp,
                    'end': timestamp
                })

    # 2.4. Démarrage et arrêt du monitoring
    def start_monitoring(self):
        logging.info(f"Starting activity monitoring... PID: {os.getpid()}")
        print(f"Starting activity monitoring... PID: {os.getpid()}")
        self.k_listener = keyboard.Listener(on_press=self.on_key_activity)
        self.m_listener = mouse.Listener(on_click=self.on_mouse_activity)
        self.k_listener.daemon = True
        self.m_listener.daemon = True
        self.k_listener.start()
        self.m_listener.start()

    def stop_monitoring(self):
        self.k_listener.stop()
        self.m_listener.stop()

    # 2.5. Sauvegarde des données dans SQLite
    def save_data_to_db(self):
        conn = sqlite3.connect('activity_data.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY,
            type TEXT,
            start TEXT,
            end TEXT
        )
        ''')
        for activity in self.activity_data:
            cursor.execute('''
            INSERT INTO activity (type, start, end)
            VALUES (?, ?, ?)
            ''', (activity['type'], activity['start'], activity['end']))
        conn.commit()
        conn.close()

    # 2.6. Méthodes pour la sauvegarde périodique des données
    def periodic_save(self):
        while not self.exit_event.is_set():
            print("Periodic save running.")  # Ajouté pour le débogage
            time.sleep(self.config.get('save_interval', 60))
            self.save_data_to_db()

    def start_periodic_save(self):
        self.save_thread = threading.Thread(target=self.periodic_save)
        self.save_thread.daemon = True
        self.save_thread.start()


    def stop_periodic_save(self):
        if self.save_thread:
            self.save_thread.join(timeout=5)

# 3. Gestion de signal d’interruption
def graceful_exit(signum, frame):
    print("Graceful exit function called.")  # Ajouté pour le débogage
    with exit_lock:
        logging.info("Signal received. Exiting gracefully...")
        monitor.exit_event.set()  # Modification ici
        monitor.stop_periodic_save()
        monitor.stop_monitoring()
        monitor.save_data_to_db()
        os._exit(0)  # instead of exit(0) to handle graceful_exit

# 4. Point d'entrée principal
if __name__ == "__main__":
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)

        monitor = ActivityMonitor(config)
        monitor.start_periodic_save()
        signal.signal(signal.SIGINT, graceful_exit)
        signal.signal(signal.SIGTERM, graceful_exit)
        monitor.start_monitoring()
        #  KeyboardInterrupt
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                graceful_exit(None, None)
    except Exception as e:
        logging.error(f"Error in monitoring module: {e}")
