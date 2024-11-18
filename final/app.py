from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///planterator.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# MQTT setup
MQTT_BROKER = "rpi2024"
MQTT_PORT = 1883
MQTT_TOPIC_TEMPHUM = "sensor/temphum"
MQTT_TOPIC_MOISTURE = "sensor/moisture"
MQTT_TOPIC_LIGHT = "sensor/light"

# Live data storage
sensor_data = {
    "timestamps": [],
    "temperature": [],
    "humidity": [],
    "moisture": [],
    "light": []
}

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class SensorReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.utcnow() - timedelta(hours=5))  # EST conversion
    sensor_type = db.Column(db.String(50))
    value = db.Column(db.Float)
    file_path = db.Column(db.String(200))

def save_to_daily_file(data):
    today = datetime.now().strftime('%Y%m%d')
    filename = f'daily_readings/{today}.json'
    os.makedirs('daily_readings', exist_ok=True)
    
    with open(filename, 'a') as f:
        f.write(json.dumps(data) + '\n')
    return filename

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def on_mqtt_message(client, userdata, msg):
    try:
        with app.app_context():
            data = json.loads(msg.payload.decode())
            msg_timestamp = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
            
            # Check if reading already exists
            existing = SensorReading.query.filter(
                SensorReading.timestamp == msg_timestamp,
                SensorReading.sensor_type.in_(['temperature', 'humidity'])
            ).first()
            
            if not existing:  # Only save if no reading exists
                file_path = save_to_daily_file(data)
                
                if msg.topic == MQTT_TOPIC_TEMPHUM:
                    sensor_data["timestamps"].append(data['timestamp'])
                    sensor_data["temperature"].append(data["temperature"])
                    sensor_data["humidity"].append(data["humidity"])
                    
                    db.session.add(SensorReading(
                        timestamp=msg_timestamp,
                        sensor_type="temperature",
                        value=data["temperature"],
                        file_path=file_path
                    ))
                    db.session.add(SensorReading(
                        timestamp=msg_timestamp,
                        sensor_type="humidity",
                        value=data["humidity"],
                        file_path=file_path
                    ))
                    db.session.commit()
                    print(f"Saved new reading from {msg_timestamp}")
            else:
                print(f"Skipping duplicate reading from {msg_timestamp}")
                
    except Exception as e:
        print(f"Error processing message: {e}")
        db.session.rollback()

client = mqtt.Client()
client.on_message = on_mqtt_message
client.on_connect = lambda client, userdata, flags, rc: client.subscribe([
    (MQTT_TOPIC_TEMPHUM, 0),
    (MQTT_TOPIC_MOISTURE, 0),
    (MQTT_TOPIC_LIGHT, 0)
])

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/live')
@login_required
def live():
    return render_template('live.html')

@app.route('/historical')
@login_required
def historical():
    readings = SensorReading.query.order_by(SensorReading.timestamp.desc()).limit(100).all()
    return render_template('historical.html', readings=readings)

@app.route('/sensor-data')
@login_required
def get_sensor_data():
    return jsonify(sensor_data)

@app.route('/test-db')
def test_db():
    try:
        # Add test reading
        test_reading = SensorReading(
            timestamp=datetime.now(),
            sensor_type="temperature",
            value=25.0,
            file_path="test.json"
        )
        db.session.add(test_reading)
        db.session.commit()
        return "Test data added!"
    except Exception as e:
        return f"Error: {e}"

def process_stored_files():
    daily_readings_dir = 'daily_readings'
    if os.path.exists(daily_readings_dir):
        for filename in os.listdir(daily_readings_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(daily_readings_dir, filename)
                with open(filepath, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            # Process data like in on_mqtt_message
                            with app.app_context():
                                est_time = datetime.utcnow() - timedelta(hours=5)
                                db.session.add(SensorReading(
                                    timestamp=est_time,
                                    sensor_type="temperature",
                                    value=data["temperature"],
                                    file_path=filepath
                                ))
                                db.session.add(SensorReading(
                                    sensor_type="humidity",
                                    value=data["humidity"],
                                    file_path=filepath
                                ))
                                db.session.commit()
                                print(f"Processed stored reading: {data}")
                        except Exception as e:
                            print(f"Error processing stored data: {e}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='password'))
            db.session.commit()
        #process_stored_files()
    
    # Connect to MQTT
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
    except:
        print("Could not connect to MQTT broker")
    
    app.run(debug=True, host='0.0.0.0')