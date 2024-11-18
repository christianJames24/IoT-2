import os
import paho.mqtt.client as mqtt
import board
import adafruit_dht
import RPi.GPIO as GPIO
import time
import json

GPIO.setmode(GPIO.BCM)
LED_PIN = 18
GPIO.setup(LED_PIN, GPIO.OUT)

dht = adafruit_dht.DHT11(board.D4)  # gpio 4

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_TEMPHUM = "sensor/temphum"
MQTT_TOPIC_LED = "sensor/led"

OFFLINE_DIR = "offline_data"
os.makedirs(OFFLINE_DIR, exist_ok=True)

readings_buffer = []

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC_LED)
    if rc == 0:
        print("Checking offline files...")
        for filename in sorted(os.listdir(OFFLINE_DIR)):
            if filename.endswith('.json'):
                filepath = os.path.join(OFFLINE_DIR, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    client.publish(MQTT_TOPIC_TEMPHUM, json.dumps(data))
                    print(f"Sent offline data: {data}")
                    os.remove(filepath)
                    time.sleep(1)
                except Exception as e:
                    print(f"Error sending {filepath}: {e}")

def on_message(client, userdata, msg):
    if msg.topic == MQTT_TOPIC_LED:
        if msg.payload.decode() == "ON":
            GPIO.output(LED_PIN, GPIO.HIGH)
            print("LED ON")
        else:
            GPIO.output(LED_PIN, GPIO.LOW)
            print("LED OFF")

def save_offline_data(data):
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    offline_file = os.path.join(OFFLINE_DIR, f"reading_{timestamp}.json")
    try:
        with open(offline_file, 'w') as f:
            json.dump(data, f)
        print(f"Saved offline: {offline_file}")
    except Exception as e:
        print(f"Error saving offline data: {e}")

client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    while True:
        try:
            temperature = dht.temperature
            humidity = dht.humidity
            
            if temperature is not None and humidity is not None:
                sensor_data = {
                    "temperature": round(temperature, 2),
                    "humidity": round(humidity, 2),
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                readings_buffer.append(sensor_data)
                
                if len(readings_buffer) >= 5:
                    avg_data = {
                        "temperature": round(sum(r["temperature"] for r in readings_buffer) / 5, 2),
                        "humidity": round(sum(r["humidity"] for r in readings_buffer) / 5, 2),
                        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Save offline data regardless of MQTT connection status
                    save_offline_data(avg_data)
                    
                    # Attempt to publish if MQTT is connected
                    try:
                        client.publish(MQTT_TOPIC_TEMPHUM, json.dumps(avg_data))
                        print(f"Published: {avg_data}")
                    except Exception as e:
                        print(f"MQTT publish error: {e}")
                    
                    readings_buffer = []
            
        except RuntimeError as error:
            print(f"Error reading sensor: {error}")
            
        # Run MQTT loop to handle connections in the background
        client.loop()
        time.sleep(30)

except KeyboardInterrupt:
    print("Exiting...")
    GPIO.cleanup()
    client.loop_stop()
    client.disconnect()

except Exception as e:
    print(f"An error occurred: {e}")
    GPIO.cleanup()
    client.loop_stop()
    client.disconnect()

finally:
    dht.exit()
