import argparse
import logging

# Configuration et initialisation du logging
logging.basicConfig(filename='log_dev.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Programme externe pour envoyer des emails.')
    parser.add_argument('time_period', type=str, help='Période de temps pour laquelle envoyer des emails (daily, weekly, etc.)')
    parser.add_argument('--mode', type=str, default='normal', help='Mode d\'exécution (test, force, etc.)')

    args = parser.parse_args()
    time_period = args.time_period
    mode = args.mode

    logging.info(f"Programme write_to_db appelé avec période {time_period} et mode {mode}.")

