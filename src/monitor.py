import json
import os
import paho.mqtt.client as mqtt
from flask import Flask, render_template
from flask_socketio import SocketIO
from queue import Queue
from dotenv import load_dotenv

load_dotenv()

TOPIC_DEBIT = os.getenv("TOPIC_DEBIT")
TOPIC_QUANTITY = os.getenv("TOPIC_QUANTITY")

message_queue = Queue()

# ---------- MQTT ----------
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT")
    client.subscribe(TOPIC_DEBIT)
    client.subscribe(TOPIC_QUANTITY)

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)

    if msg.topic == TOPIC_DEBIT:
        message_queue.put(("flow_update", data["flow_rate"]))

    if msg.topic == TOPIC_QUANTITY:
        message_queue.put(("level_update", data["level"]))

def create_mqtt():
    client = mqtt.Client()
    client.username_pw_set(os.getenv("MONITOR_USERNAME"), os.getenv("MONITOR_PASSWORD"))
    client.tls_set(
        ca_certs=os.getenv("CA_CRT"),
        certfile=os.getenv("MONITOR_CRT"),
        keyfile=os.getenv("MONITOR_KEY")
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(os.getenv("BROKER"), int(os.getenv("PORT")))
    return client

mqtt_client = create_mqtt()
mqtt_client.loop_start()

# ---------- Flask ----------
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on("connect")
def handle_connect():
    print("Client connected")
    print("Clients:", socketio.server.manager.rooms)

def socket_worker():
    while True:
        event, value = message_queue.get()
        print("Sending to control panel:", event, value)
        socketio.emit(event, {"value": value}, namespace="/")
        socketio.sleep(0)

socketio.start_background_task(socket_worker)

@app.route("/")
def index():
    return render_template("dashboard.html")

# ---------- Run ----------
if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000)