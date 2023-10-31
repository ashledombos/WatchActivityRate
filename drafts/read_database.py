import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('activity_data.db')

# Création d'un curseur
cursor = conn.cursor()

# Exécution d'une requête SQL pour récupérer toutes les données de la table "activity"
cursor.execute("SELECT * FROM activity")

# Récupération et affichage des données
rows = cursor.fetchall()
for row in rows:
    print(row)

# Fermeture de la connexion
conn.close()
