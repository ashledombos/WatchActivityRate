import toml
import time
import logging
import threading
import signal
import os
from pynput import keyboard, mouse
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

from ..package.db_operations import DatabaseManager

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

    if config['periodic_save_minutes'] <= 0:
        raise ValueError("La valeur de periodic_save_minutes doit être un nombre positif.")

class ActivityMonitor:
    """Gère le monitoring des activités clavier et souris."""
    
    def __init__(self, config):
        """Initialise le monitor d'activité.
        
        Note: un événement correspond à un clic, une touche appuyée ou un scroll.
        """
        logging.debug("Chargement du fichier de configuration toml.")
        self.config = config
        self.activity_data = []
        self.exit_event = threading.Event()
        self.db_manager = DatabaseManager()
        self.db_manager.configure_db()
        self.event_count = 0    

    def on_key_activity(self, key):
        """Gère les événements liés aux touches du clavier."""
        logging.debug("Activité clavier détectée.")
        try:
            self.event_count += 1
            logging.debug(f"Nombre total de clics et de touches : {self.event_count}.")
        except Exception as e:
            logging.error(f"Erreur lors de l'enregistrement de l'activité : {e}")

    def on_mouse_activity(self, x, y, button, pressed, scroll_x=0, scroll_y=0):
        """Gère les événements liés à la souris, y compris les clics et le défilement."""
        logging.debug("Activité souris détectée.")
        try:
            if pressed or scroll_x != 0 or scroll_y != 0:
                self.event_count += 1
                logging.debug(f"Nombre total de clics et de scrolls : {self.event_count}.")
        except Exception as e:
            logging.error(f"Erreur lors de l'enregistrement de l'activité souris : {e}")

    def is_valid_activity_for_period(self):
        """Vérifie si une activité est valide pour la période actuelle."""
        # Multiplier le seuil par le nombre de minutes dans la période
        threshold_events = self.config['activity_duration_threshold'] * self.config['periodic_save_minutes']
        if self.event_count >= threshold_events:
            logging.debug(f"Période de {self.config['periodic_save_minutes']} minutes, seuil de {threshold_events} évènements. "
                        f"Nombre total d'évènements pendant la période d'activité : {self.event_count}. "
                        "Minimum requis atteint. Activité valide pour la période.")
            return True
        else:
            logging.debug(f"Période de {self.config['periodic_save_minutes']} minutes, seuil de {threshold_events} évènements. "
                        f"Nombre total d'évènements pendant la période d'activité : {self.event_count}. "
                        f"Minimum requis de {threshold_events} non atteint. Activité invalide pour la période.")
            return False

    def save_data_to_db(self):
        logging.debug("Sauvegarde des données dans la base de données.")

        # Calcul de l'heure actuelle arrondie et de l'heure de début
        current_time = datetime.now()
        rounded_current_time = current_time - timedelta(seconds=current_time.second, microseconds=current_time.microsecond)
        current_time_str = rounded_current_time.strftime('%Y-%m-%d %H:%M:%S')

        # Récupération de la dernière activité de la base de données
        last_activity = self.db_manager.get_last_activity()
        
        if last_activity:
            last_end_time = datetime.strptime(last_activity['end'], '%Y-%m-%d %H:%M:%S')
            elapsed_time = (rounded_current_time - last_end_time).total_seconds()
            merge_threshold = self.config['periodic_save_minutes'] * 60 * 1.5

            logging.debug(f"Temps écoulé depuis la dernière entrée : {elapsed_time} secondes ; Seuil pour la fusion : {merge_threshold} secondes.")

            # Si le temps écoulé est inférieur au seuil, fusionnez les entrées
            if elapsed_time <= merge_threshold:
                self.db_manager.update_activity_end_time(last_activity['id'], current_time_str)
                logging.debug(f"Les conditions pour la fusion sont remplies. Mise à jour de l'heure de fin de la dernière entrée à {current_time_str}.")
            # Sinon, créez une nouvelle entrée avec le 'start' ajusté
            else:
                new_start_time = (rounded_current_time - timedelta(minutes=self.config['periodic_save_minutes'])).strftime('%Y-%m-%d %H:%M:%S')
                self.db_manager.save_activity_data([{
                    'start': new_start_time,
                    'end': current_time_str
                }])
                logging.debug(f"Création d'une nouvelle entrée avec heure de début {new_start_time} et heure de fin {current_time_str}.")
        else:
            # S'il n'y a pas d'entrée précédente, créez la première entrée avec un start_time calculé
            start_time = (rounded_current_time - timedelta(minutes=self.config['periodic_save_minutes'])).strftime('%Y-%m-%d %H:%M:%S')
            self.db_manager.save_activity_data([{
                'start': start_time,
                'end': current_time_str
            }])
            logging.debug(f"Création de la première entrée avec heure de début {start_time} et heure de fin {current_time_str}.")

        # Réinitialiser les données d'activité en mémoire, si nécessaire
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
            self.event_count = 0  # Réinitialiser le compteur d'événements pour la nouvelle période
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
        with open('config/config.toml', 'r') as f:
            config = toml.load(f)

        log_file = "logs/ab.log"
        log_level = logging.DEBUG if config.get('debug_mode') else logging.INFO
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Essayer de configurer le logging et attraper toute exception
        try:
            # Créez un handler qui écrit les logs dans un fichier, avec une rotation toutes les 1 Mo et 5 fichiers de sauvegarde.
            handler = RotatingFileHandler(log_file, maxBytes=1e6, backupCount=5)
            handler.setLevel(log_level)

            # Créez un formateur pour le handler
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)

            # Obtenez le logger par défaut et configurez-le
            logger = logging.getLogger()
            logger.setLevel(log_level)
            logger.addHandler(handler)
            
        except Exception as e:
            print(f"Erreur lors de la configuration de logging: {e}")
            exit(1)

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
                
    except toml.TomlDecodeError:
        print("Erreur de décodage TOML. Vérifiez le fichier de configuration.")
    except FileNotFoundError:
        print("Fichier de configuration non trouvé.")
    except Exception as e:
        print(f"Erreur inattendue : {e}")