# IoT-2

IoT plant monitoring system that tracks temperature and humidity for indoor plants. Built for a college IoT project.

## What it does

- Reads temperature and humidity from a DHT11 sensor on a Raspberry Pi
- Sends data over MQTT to a Flask web server
- Shows live sensor readings with real-time charts
- Stores historical data in a SQLite database
- Has a web dashboard with login authentication

## Hardware

- Raspberry Pi with DHT11 temperature/humidity sensor (GPIO 4)
- LED indicator (GPIO 18)

## Tech Stack

- **Backend**: Flask, Flask-Login, SQLAlchemy
- **Frontend**: HTML/CSS/JavaScript, Chart.js
- **IoT**: MQTT (Paho), Adafruit DHT library
- **Database**: SQLite

## Features

- Live sensor data visualization
- Historical data table
- Offline data buffering (saves readings when MQTT connection drops)
- Averages readings every 5 samples before publishing
- Login system to protect the dashboard

## Setup

1. Install dependencies on Raspberry Pi
2. Run `publisher.py` on the Pi to start collecting sensor data
3. Run `app.py` on the server to start the web interface
4. Default login: `admin` / `password`

## Team

- Christian (ID: 2232469) - christianvehicle@gmail.com
- Dennis (ID: 2232694) - dkanat822@gmail.com
