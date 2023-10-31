# Système de Monitoring d'Activité Intelligent

## Introduction

Ce système de monitoring d'activité est conçu pour suivre et enregistrer les activités de l'utilisateur sur un ordinateur. Il utilise une approche "intelligente" pour détecter l'activité, en se basant sur plusieurs paramètres et seuils.

## Fonctionnement

### Détection d'Activité

Le système utilise les événements du clavier et de la souris pour détecter l'activité. Chaque fois qu'une touche est pressée ou qu'un clic de souris est effectué, un événement est enregistré.

### Fenêtre Glissante

Le système utilise une "fenêtre glissante" pour évaluer l'activité récente. Cette fenêtre représente une période de temps pendant laquelle le système compte le nombre d'événements enregistrés. Si ce nombre dépasse un certain seuil, l'activité est considérée comme "valide".

### Seuil d'Activité

Le "seuil d'activité" est le nombre minimum d'événements qui doivent être enregistrés dans la fenêtre glissante pour que l'activité soit considérée comme valide. Ce seuil peut être ajusté en fonction des besoins de l'utilisateur.

### Seuil de Pause

Le "seuil de pause" est une durée maximale entre deux événements consécutifs pour qu'ils soient considérés comme faisant partie de la même "session" d'activité. Si la durée entre deux événements dépasse ce seuil, une nouvelle session d'activité est créée.

### Optimisation

Si vous souhaitez optimiser le système pour mieux correspondre à vos besoins, vous pouvez ajuster les paramètres suivants dans le fichier config.json :

- sliding_window: Durée de la fenêtre glissante en secondes.
- activity_threshold: Seuil d'activité, ou nombre minimum d'événements pour une activité valide.
- pause_threshold: Seuil de pause en secondes.
