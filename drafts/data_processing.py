## Ce fichier va 

import sqlite3
import csv
import logging
import schedule
import time
from datetime import datetime
from collections import defaultdict

# Configuration et initialisation du logging
logging.basicConfig(filename='data_processing.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fonction pour récupérer les données brutes de la base de données SQLite
def fetch_raw_data():
    try:
        conn = sqlite3.connect('activity_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activity")
        data = cursor.fetchall()
        conn.close()
        return data
    except Exception as e:
        logging.error(f"Error fetching data from SQLite: {e}")
        return None

# Fonction pour calculer les métriques
def calculate_metrics(raw_data):
    daily_metrics = defaultdict(int)
    weekly_metrics = defaultdict(int)
    monthly_metrics = defaultdict(int)
    yearly_metrics = defaultdict(int)

    try:
        for record in raw_data:
            activity_type = record[1]
            timestamp_str = record[2]  # Assuming the 'start' timestamp is in the 3rd column
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

            day_key = timestamp.strftime('%Y-%m-%d')
            week_key = f"{timestamp.year}-W{timestamp.isocalendar()[1]}"
            month_key = timestamp.strftime('%Y-%m')
            year_key = str(timestamp.year)

            if activity_type == 'mouse':
                daily_metrics[day_key] += 1
                weekly_metrics[week_key] += 1
                monthly_metrics[month_key] += 1
                yearly_metrics[year_key] += 1
            elif activity_type == 'keyboard':
                daily_metrics[day_key] += 1
                weekly_metrics[week_key] += 1
                monthly_metrics[month_key] += 1
                yearly_metrics[year_key] += 1

        return daily_metrics, weekly_metrics, monthly_metrics, yearly_metrics
    except Exception as e:
        logging.error(f"Error calculating metrics: {e}")
        return None

# Fonction pour sauvegarder les métriques dans un fichier CSV
def save_metrics_to_csv(metrics, filename):
    try:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['Time Period', 'Activity Count']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for key, value in metrics.items():
                writer.writerow({'Time Period': key, 'Activity Count': value})
    except Exception as e:
        logging.error(f"Error saving metrics to CSV: {e}")

if __name__ == "__main__":
    raw_data = fetch_raw_data()
    if raw_data:
        daily_metrics, weekly_metrics, monthly_metrics, yearly_metrics = calculate_metrics(raw_data)
        if daily_metrics:
            save_metrics_to_csv(daily_metrics, 'daily_metrics.csv')
            save_metrics_to_csv(weekly_metrics, 'weekly_metrics.csv')
            save_metrics_to_csv(monthly_metrics, 'monthly_metrics.csv')
            save_metrics_to_csv(yearly_metrics, 'yearly_metrics.csv')
            logging.info("Data processing completed successfully.")

def run_scheduled_tasks(test_mode=False):
    if not test_mode:
        # Planifiez les tâches pour des moments spécifiques
        schedule.every().monday.at("09:00").do(run_tasks, 'weekly')
        schedule.every().day.at("23:59").do(run_tasks, 'daily')
        schedule.every(1).to(31).day.at("23:59").do(run_tasks, 'monthly')
        schedule.every().year.at("2023-01-01 00:00").do(run_tasks, 'yearly')

        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        # Mode test : exécutez toutes les tâches immédiatement
        run_tasks('daily')
        run_tasks('weekly')
        run_tasks('monthly')
        run_tasks('yearly')

# Fonction pour exécuter les tâches
def run_tasks(time_period):
    logging.info(f"Running {time_period} tasks.")
    raw_data = fetch_raw_data()
    if raw_data:
        daily_metrics, weekly_metrics, monthly_metrics, yearly_metrics = calculate_metrics(raw_data)
        if daily_metrics:
            save_metrics_to_csv(daily_metrics, f'{time_period}_metrics.csv')
            logging.info(f"{time_period.capitalize()} data processing completed successfully.")

if __name__ == "__main__":
    test_mode = True  # Mettez cette variable à True pour activer le mode test
    run_scheduled_tasks(test_mode)
