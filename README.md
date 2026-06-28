# Projet 1 — DHT22 → ThingsBoard (Dakar)

## Deux façons d'envoyer des données

| Mode | Source des mesures |
|------|-------------------|
| **Wokwi / ESP32** | Capteur **DHT22** (mesures réelles du simulateur) |
| **Script Python** | Fichier `data/simulated_sensor.txt` (simulation **sans carte**) |

## Script Python (simulation locale PC)

```cmd
python scripts/generate_simulated_dataset.py -n 120
python scripts/send_simulated_data.py --reset
```

## Wokwi

Importer le dossier, ajouter `secrets.h`, lancer la simulation.  
Le firmware lit le **DHT22** et envoie par **MQTT**.

Documentation : `readme/README_chapitre3.md`
