import subprocess
import argparse
import logging

# Configuration et initialisation du logging
logging.basicConfig(filename='generate_stats.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fonction pour exécuter un programme externe
def run_external_program(program_name, time_period, mode=""):
    try:
        subprocess.run(["python3", f"{program_name}.py", f"{time_period}", f"--mode", f"{mode}"])
        logging.info(f"Exécution de {program_name} avec période {time_period} et mode {mode} réussie.")
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de {program_name} : {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Générer des statistiques.')
    parser.add_argument('time_period', type=str, help='Période de temps pour laquelle générer des statistiques (daily, weekly, etc.)')
    parser.add_argument('--mode', type=str, default="", help='Mode d\'exécution (test, force, etc.)')

    args = parser.parse_args()
    time_period = args.time_period
    mode = args.mode

    # Appel aux programmes externes
    run_external_program("write_to_db", time_period, mode)
    run_external_program("export_to_csv", time_period, mode)
    run_external_program("generate_graphs", time_period, mode)
    run_external_program("local_archive", time_period, mode)
    run_external_program("send_email", time_period, mode)

    logging.info("Génération des statistiques et exécution des programmes externes réussies.")
