# WatchActivityRate

# Projet de Monitoring d'Activités

Ce projet vise à surveiller les activités sur un ordinateur, telles que les mouvements de la souris et les frappes au clavier. Les données collectées sont ensuite sauvegardées dans une base de données SQLite pour une analyse ultérieure.

## Structure du Projet

Le projet est composé des fichiers suivants :

- `monitoring.py`: Ce fichier contient le code pour surveiller les activités de l'utilisateur sur l'ordinateur. Il utilise la librairie `pynput` pour écouter les événements de la souris et du clavier.
- `db_operations.py`: Ce fichier contient la classe `DatabaseManager` qui gère toutes les opérations liées à la base de données SQLite.
- `data_processing.py`: Ce fichier contient le code pour traiter les données d'activités stockées dans la base de données. Il calcule des métriques sur ces données et les sauvegarde dans des fichiers CSV.
- `config.json`: Ce fichier contient les paramètres de configuration qui sont utilisés dans `monitoring.py` et `data_processing.py`.

## Configuration

Le fichier `config.json` contient les paramètres suivants :

- `sliding_window`: Fenêtre temporelle pour considérer les activités récentes (en secondes).
- `activity_threshold`: Nombre minimum d'événements d'activité pour considérer une période comme active.
- `pause_threshold`: Durée maximum d'inactivité pour considérer deux événements comme faisant partie de la même session (en secondes).

### Exemple de `config.json`

```json
{
    "sliding_window": 300,
    "activity_threshold": 5,
    "pause_threshold": 60
}
```

## Utilisation

1. Assurez-vous que Python est installé sur votre système.
2. Installez les dépendances en exécutant `pip install -r requirements.txt`.
3. Exécutez `python monitoring.py` pour démarrer le monitoring des activités.
4. Exécutez `python data_processing.py` pour traiter les données et générer les métriques.
