import json
import time
import logging
import threading
import signal
import os
from pynput import keyboard, mouse
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

from .db_operations import DatabaseManager

def validate_config(config):
    """Valide la configuration en vérifiant la présence des paramètres nécessaires et leurs valeurs."""
    logging.debug("Validation de la configuration.")
    required_params = ['periodic_save_minutes', 'activity_duration_threshold']
    for param in required_params:
        if param not in config:
            raise ValueError(f"Paramètre manquant dans le fichier de configuration : {param}")
    if config['activity_duration_threshold'] > 60 or config['activity_duration_threshold'] < 0:
        raise ValueError("La valeur de activity_duration_threshold doit être comprise entre 0 et 60 (inclus).")

    if 60 % config['periodic_save_minutes'] != 0:
        raise ValueError("La période doit être un diviseur entier de 60.")

class ActivityMonitor:
    """Gère le monitoring des activités clavier et souris."""
    
    def __init__(self, config):
        """Initialise le monitor d'activité.
        
        Note: un événement correspond à un clic, une touche appuyée ou un scroll.
        """
        logging.debug("Chargement du fichier de configuration json.")
        self.config = config
        self.activity_data = []
        self.exit_event = threading.Event()
        self.db_manager = DatabaseManager()
        self.db_manager.configure_db()
        self.event_count = 0    

    def on_key_activity(self, key):
        """Gère les événements liés aux touches du clavier."""
        logging.debug("Activité clavier détectée.")
        if self.event_count >= self.config['activity_duration_threshold']:
            return
        try:
            self.event_count += 1
            logging.debug(f"Nombre total de clics et de scrolls : {self.event_count}.")
        except Exception as e:
            logging.error(f"Erreur lors de l'enregistrement de l'activité : {e}")

    def on_mouse_activity(self, x, y, button, pressed, scroll_x=0, scroll_y=0):
        """Gère les événements liés à la souris, y compris les clics et le défilement."""
        logging.debug("Activité souris détectée.")
        if self.event_count >= self.config['activity_duration_threshold']:
            return
        try:
            if pressed or scroll_x != 0 or scroll_y != 0:
                self.event_count += 1
                logging.debug(f"Nombre total de clics et de scrolls : {self.event_count}.")
        except Exception as e:
            logging.error(f"Erreur lors de l'enregistrement de l'activité souris : {e}")

    def is_valid_activity_for_period(self):
        """Vérifie si une activité est valide pour la période actuelle."""
        return self.event_count >= self.config['activity_duration_threshold']

    def save_data_to_db(self):
        """
        Sauvegarde les données d'activité enregistrées dans la base de données.
        
        Si la durée entre l'instant actuel et la date de fin (`end`) de l'entrée précédente 
        est inférieure ou égale à la période définie, cette méthode fusionne les données de l'activité 
        actuelle avec l'entrée précédente. Sinon, une nouvelle entrée est ajoutée. Cela évite 
        d'avoir des entrées fragmentées lorsque plusieurs périodes consécutives ont des activités valides.
        """
        logging.debug("Tentative de sauvegarde des données dans la base de données.")
        
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        start_time = (datetime.now() - timedelta(minutes=self.config['periodic_save_minutes'])).strftime('%Y-%m-%d %H:%M:%S')
        
        if self.activity_data:
            last_activity = self.activity_data[-1]
            last_end_time = datetime.strptime(last_activity['end'], '%Y-%m-%d %H:%M:%S')
            
            # Si la différence de temps entre la dernière entrée et maintenant est inférieure ou égale à la période
            if (datetime.now() - last_end_time).total_seconds() <= self.config['periodic_save_minutes'] * 60 + 1:  # +1 pour gérer les éventuelles millisecondes de décalage
                # Mettre à jour la fin de la dernière entrée
                last_activity['end'] = current_time
            else:
                self.activity_data.append({
                    'start': start_time,
                    'end': current_time
                })
        else:
            self.activity_data.append({
                'start': start_time,
                'end': current_time
            })
        
        self.db_manager.save_activity_data(self.activity_data)
        self.activity_data = []

    def periodic_save(self):
        """Effectue une sauvegarde périodique des données d'activité dans la base de données si l’activité est valide."""
        logging.debug("Sauvegarde périodique en cours.")
        
        # Calcul du délai initial avant la première sauvegarde pour qu'elle coïncide avec un intervalle régulier
        now = datetime.now()
        minutes_passed = now.minute % self.config['periodic_save_minutes']
        initial_delay = self.config['periodic_save_minutes'] - minutes_passed
        initial_delay_seconds = initial_delay * 60 - now.second  # Ne pas oublier les secondes
        
        time.sleep(initial_delay_seconds)  # Attendre le délai initial
        
        while not self.exit_event.is_set():
            if self.is_valid_activity_for_period():
                self.save_data_to_db()
            self.event_count = 0
            time.sleep(self.config['periodic_save_minutes'] * 60)

    def start_periodic_save(self):
        """Démarre le thread de sauvegarde périodique des données d'activité."""
        logging.debug("Démarrage du thread de sauvegarde périodique.")
        self.save_thread = threading.Thread(target=self.periodic_save)
        self.save_thread.daemon = True
        self.save_thread.start()

    def stop_periodic_save(self):
        """Arrête le thread de sauvegarde périodique."""
        logging.debug("Arrêt du thread de sauvegarde périodique.")
        if self.save_thread:
            self.save_thread.join(timeout=5)

    def start_monitoring(self):
        """Démarre le monitoring des activités clavier et souris."""
        logging.info(f"Démarrage de la surveillance des activités... PID : {os.getpid()}")
        self.k_listener = keyboard.Listener(on_press=self.on_key_activity)
        self.m_listener = mouse.Listener(on_click=self.on_mouse_activity, on_scroll=self.on_mouse_activity)
        self.k_listener.daemon = True
        self.m_listener.daemon = True
        self.k_listener.start()
        self.m_listener.start()

    def stop_monitoring(self):
        """Arrête le monitoring des activités clavier et souris."""
        logging.debug("Arrêt du monitoring des activités clavier et souris.")
        self.k_listener.stop()
        self.m_listener.stop()

# Fonction pour gérer une sortie propre du programme en cas de signal d'interruption
def graceful_exit(signum, frame):
    """Gère une sortie propre du programme en cas de réception d'un signal d'interruption."""
    logging.info("Signal reçu. Arrêt propre...")
    monitor.exit_event.set()
    monitor.stop_periodic_save()
    monitor.stop_monitoring()
    os._exit(0)  # Sortie propre du programme

# Point d'entrée du programme
if __name__ == "__main__":
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)

        log_file = "monitoring.log"
        log_level = logging.DEBUG if config.get('debug_mode') else logging.INFO

        # Créez un handler qui écrit les logs dans un fichier, avec une rotation toutes les 1 Mo et 5 fichiers de sauvegarde.
        handler = RotatingFileHandler(log_file, maxBytes=1e6, backupCount=5)
        handler.setLevel(log_level)

        # Créez un formateur pour le handler
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Configurez le logger
        logging.basicConfig(handlers=[handler])


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
