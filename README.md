# IoT-2

IoT plant monitoring system for tracking temperature and humidity. This is the IndoorPlanterator+ project for our college IoT class.

## What it does

Monitors indoor plant conditions using sensors connected to a Raspberry Pi. Data gets sent over MQTT to a Flask web server where you can view live readings and historical data through a web dashboard.

- Reads temp/humidity from DHT11 sensor every 30 seconds
- Averages readings over 5 cycles before publishing to MQTT
- Real-time charts showing sensor data
- Historical data stored in SQLite database
- Login-protected web interface
- Offline data buffering (saves readings locally when MQTT drops, sends them when connection restores)

## Hardware Setup

- Raspberry Pi 4 (GPIO 4 for DHT11 sensor)
- DHT11 Temperature/Humidity Sensor
- LED indicator on GPIO 18
- MQTT Broker running on "rpi2024"

## Tech Stack

**Backend:**
- Flask with Flask-Login for auth
- SQLAlchemy + SQLite for data storage
- Paho MQTT for sensor communication

**Frontend:**
- HTML/CSS with Chart.js for visualizations
- JavaScript for live updates

**IoT:**
- Python with Adafruit DHT library
- RPi.GPIO for hardware control
- MQTT publish/subscribe pattern

## Project Structure

- `publisher.py` - Runs on the Pi, reads sensors and publishes to MQTT
- `app.py` - Flask web server that receives MQTT data and serves the dashboard
- `base.html`, `login.html`, `live.html`, `historical.html` - Web interface templates
- `style.css` - Dashboard styling
- `daily_readings/` - Stores JSON files with sensor readings

## How to Run

**On the Raspberry Pi:**
```bash
python3 publisher.py
