import os
import schedule
import time
import logging

# Configuration et initialisation du logging
logging.basicConfig(filename='orchestrator.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fonction pour exécuter un script
def run_script(script_name):
    try:
        os.system(f"python {script_name}.py")
        logging.info(f"Exécution de {script_name} réussie.")
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de {script_name} : {e}")

# Planification des tâches
schedule.every().day.at("23:59").do(run_script, 'generate_stats')

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)