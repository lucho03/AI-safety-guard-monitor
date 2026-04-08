import json
import os

import time
import threading

# from requests import request

from queue import Queue

# import ssl
from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='./')
socketio = SocketIO(app, cors_allowed_origins="*")

TOPIC_DEBIT = os.getenv("TOPIC_DEBIT")
TOPIC_QUANTITY = os.getenv("TOPIC_QUANTITY")

flow_data = []
level_data = []
message_queue = Queue()

# ---------- MQTT ----------
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT")
    client.subscribe(TOPIC_DEBIT)
    client.subscribe(TOPIC_QUANTITY)

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)

    if msg.topic == TOPIC_DEBIT:
        flow = data["flow_rate"]
        flow_data.append(flow)

        print(f"Received flow rate: {data['flow_rate']} timestamp: {data['timestamp']}")
        message_queue.put(("flow_update", flow))

        # socketio.emit("flow_update", {
        #     "value": flow
        # })


        # socketio.emit(
        #     "flow_update",
        #     {"value": flow},
        #     namespace="/"
        # )

    if msg.topic == TOPIC_QUANTITY:
        level = data["level"]
        level_data.append(level)

        print(f"Received tank level: {data['level']} timestamp: {data['timestamp']}")
        message_queue.put(("level_update", level))

        # socketio.emit("level_update", {
        #     "value": level
        # })

        # socketio.emit(
        #     "level_update",
        #     {"value": level},
        #     namespace="/"
        # )

def create_mqtt():
    client = mqtt.Client()
    client.username_pw_set(
        os.getenv("MONITOR_USERNAME"),
        os.getenv("MONITOR_PASSWORD")
    )

    client.tls_set(
        ca_certs=os.getenv("CA_CRT"),
        certfile=os.getenv("MONITOR_CRT"),
        keyfile=os.getenv("MONITOR_KEY"),
        # tls_version=ssl.PROTOCOL_TLS
    )

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(os.getenv("BROKER"), int(os.getenv("PORT")))
    return client

# mqtt_client = create_mqtt()

# # MQTT loop в background thread
# def mqtt_thread():
#     mqtt_client.loop_forever()

# socketio.start_background_task(mqtt_thread)

mqtt_client = create_mqtt()
mqtt_client.loop_start()



# def proba():
#     i = 10
#     while True:
#         socketio.emit(
#                 "level_update",
#                 {"value": 32},
#                 namespace="/"
#             )
#         print(f"Emitted level update: {i}")
#         i += 1
#         time.sleep(1)

# thread = threading.Thread(target=proba, daemon=True)
# thread.start()

@socketio.on("connect")
def handle_connect():
    print("Client connected")
    print("Clients:", socketio.server.manager.rooms)
    # socketio.emit("level_update", {"value": 29})

def socket_worker():
    while True:
        event, value = message_queue.get()

        print("Sending to frontend:", event, value)

        socketio.emit(
            event,
            {"value": value},
            namespace="/"
        )

        socketio.sleep(0)  # важно за eventlet

socketio.start_background_task(socket_worker)

# ---------- Flask routes ----------
@app.route("/")
def index():
    return render_template("dashboard.html")

# ---------- Run ----------
if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000)
