# Import des bibliothèques nécessaires
import json
import time
import logging
import threading
import signal
import os
from pynput import keyboard, mouse
from datetime import datetime

# Import de la classe DatabaseManager depuis db_operations.py
from .db_operations import DatabaseManager # Assurez-vous que db_operations.py est dans le même répertoire

# Verrou utilisé pour la sortie propre du programme
#exit_lock = threading.Lock()



def validate_config(config):
    """Valide que tous les paramètres nécessaires sont dans le fichier de configuration.
    
    Args:
        config (dict): Le dictionnaire de configuration chargé depuis le fichier JSON.
        
    Raises:
        ValueError: Si un paramètre nécessaire est manquant.
    """
    required_params = ['sliding_window', 'activity_duration_threshold', 'pause_threshold']
    for param in required_params:
        if param not in config:
            raise ValueError(f"Paramètre manquant dans le fichier de configuration : {param}")

# Classe pour gérer le monitoring des activités
class ActivityMonitor:
    """Gère le monitoring des activités clavier et souris."""
    
    def __init__(self, config):
        """Initialise le monitor d'activité.
        
        Args:
            config (dict): Le dictionnaire de configuration chargé depuis le fichier JSON.
        """
        logging.debug("Chargement du fichier de configuration json.")
        self.config = config
        self.activity_data = []
        self.exit_event = threading.Event()
        self.db_manager = DatabaseManager()
        self.db_manager.configure_db()

    def on_key_activity(self, key):
        """Callback pour les événements du clavier.
        
        Args:
            key: Touche du clavier pressée.
        """
        logging.debug("Activité clavier détectée.")
        try:
            self.record_activity()
        except Exception as e:
            logging.error(f"Erreur lors de l'enregistrement de l'activité : {e}")

    def on_mouse_activity(self, x, y, button, pressed):
        """Callback pour les événements de la souris.
        
        Args:
            x (int): Position x du curseur.
            y (int): Position y du curseur.
            button: Bouton de la souris utilisé.
            pressed (bool): État du bouton (pressé ou relâché).
        """
        logging.debug("Activité souris détectée.")
        try:
            if pressed:
                self.record_activity()
        except Exception as e:
            logging.error(f"Erreur lors de l'enregistrement de l'activité : {e}")

    def is_valid_activity(self):
        """Vérifie si une activité est valide en fonction des critères définis dans la configuration.

        Returns:
            bool: True si l'activité est valide, False sinon.
        """
        logging.debug("Vérification de la validité de l’activité.")
        now = datetime.now()
        recent_activity_duration = sum(
            (datetime.strptime(a['end'], '%Y-%m-%d %H:%M:%S') - 
            datetime.strptime(a['start'], '%Y-%m-%d %H:%M:%S')).total_seconds()
            for a in self.activity_data
            if (now - datetime.strptime(a['end'], '%Y-%m-%d %H:%M:%S')).total_seconds() < self.config['sliding_window']
        )
        return recent_activity_duration > self.config['activity_duration_threshold']

    def merge_activities(self):
        """Fusionne les activités qui se chevauchent ou qui sont proches dans le temps."""
        logging.debug("Tentative de fusion des activités.")
        merged = []
        for activity in sorted(self.activity_data, key=lambda x: x['start']):
            if not merged:
                merged.append(activity)
            else:
                prev = merged[-1]
                # Vérifie si l'activité actuelle commence avant que la précédente ne se termine
                if activity['start'] <= prev['end'] or \
                (datetime.strptime(activity['start'], '%Y-%m-%d %H:%M:%S') - 
                    datetime.strptime(prev['end'], '%Y-%m-%d %H:%M:%S')).total_seconds() <= self.config['pause_threshold']:
                    # Si c'est le cas, fusionnez les deux activités
                    prev['end'] = max(prev['end'], activity['end'])
                else:
                    merged.append(activity)
        self.activity_data = merged


    def record_activity(self):
        """Enregistre une nouvelle activité ou met à jour l'activité en cours."""
        logging.debug("Enregistrement ou mise à jour d'une activité.")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        last_activity = self.activity_data[-1] if self.activity_data else None
        if last_activity:
            elapsed_time_since_last_end = time.mktime(time.strptime(timestamp, '%Y-%m-%d %H:%M:%S')) - \
                                        time.mktime(time.strptime(last_activity['end'], '%Y-%m-%d %H:%M:%S'))

            if elapsed_time_since_last_end <= self.config['pause_threshold']:
                last_activity['end'] = timestamp
            else:
                self.activity_data.append({'start': timestamp, 'end': timestamp})
        else:
            self.activity_data.append({'start': timestamp, 'end': timestamp})

        self.merge_activities()

    def is_valid_activity_for_entry(self, entry):
        """Vérifie si une entrée d'activité est valide en fonction des critères définis dans la configuration."""
        logging.debug("Autre vérification de validité.")
        duration = (datetime.strptime(entry['end'], '%Y-%m-%d %H:%M:%S') - 
                    datetime.strptime(entry['start'], '%Y-%m-%d %H:%M:%S')).total_seconds()
        return duration > self.config['activity_duration_threshold']

    def start_monitoring(self):
        """Démarre le monitoring des activités clavier et souris."""
        logging.info(f"Démarrage de la surveillance des activités... PID : {os.getpid()}")
        self.k_listener = keyboard.Listener(on_press=self.on_key_activity)
        self.m_listener = mouse.Listener(on_click=self.on_mouse_activity)
        self.k_listener.daemon = True
        self.m_listener.daemon = True
        self.k_listener.start()
        self.m_listener.start()

    def stop_monitoring(self):
        """Arrête le monitoring des activités clavier et souris."""
        logging.debug("Arrêt du monitoring.")
        self.k_listener.stop()
        self.m_listener.stop()

    def save_data_to_db(self):
        """Sauvegarde les données d'activité dans la base de données en utilisant DatabaseManager."""
        logging.debug("Sauvegarde d’activité via DatabaseManager.")
        if not self.activity_data:
            return
        self.db_manager.save_activity_data(self.activity_data)

    def periodic_save(self):
        """Effectue une sauvegarde périodique des données d'activité dans la base de données si l’activité est valide."""
        logging.debug("Sauvegarde périodique en cours.")
        while not self.exit_event.is_set():
            time.sleep(self.config.get('save_interval'))

            # Mettre à jour la fin de l'activité en cours
            self.activity_data[-1]['end'] = time.strftime('%Y-%m-%d %H:%M:%S')

            # Filtrer les activités non valides
            valid_activities = [a for a in self.activity_data if self.is_valid_activity_for_entry(a)]

            # Si des activités valides sont présentes, sauvegarder dans la base de données
            if valid_activities:
                self.save_data_to_db()

            # Remplacer self.activity_data par les activités valides
            self.activity_data = valid_activities

    def start_periodic_save(self):
        """Démarre le thread de sauvegarde périodique."""
        logging.debug("Démarrage de la sauvegarde périodique.")
        self.save_thread = threading.Thread(target=self.periodic_save)
        self.save_thread.daemon = True
        self.save_thread.start()

    def stop_periodic_save(self):
        """Arrête le thread de sauvegarde périodique."""
        logging.debug("Arrêt de la sauvegarde périodique.")
        if self.save_thread:
            self.save_thread.join(timeout=5)

# Fonction pour gérer une sortie propre du programme en cas de signal d'interruption
def graceful_exit(signum, frame):
    logging.info("Fonction de sortie propre appelée.")
    #with exit_lock:
    logging.info("Signal reçu. Arrêt propre...")
    monitor.exit_event.set()
    monitor.stop_periodic_save()
    monitor.stop_monitoring()
    monitor.save_data_to_db()
    os._exit(0)  # Sortie propre du programme

# Point d'entrée du programme
if __name__ == "__main__":
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Configuration du système de journalisation
        log_level = logging.DEBUG if config.get('debug_mode') else logging.INFO
        logging.basicConfig(
            filename='monitoring.log', 
            level=log_level, 
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        # Valide le fichier de configuration
        validate_config(config)
        
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
                
    except json.JSONDecodeError:
        logging.error("Erreur de décodage JSON. Vérifiez le fichier de configuration.")
    except FileNotFoundError:
        logging.error("Fichier de configuration non trouvé.")
    except Exception as e:
        logging.error(f"Erreur inattendue : {e}")