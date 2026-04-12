import json
import os
import socket
import json
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((os.getenv("HOST"), int(os.getenv("PIPE_PORT_LISTENING"))))

client = mqtt.Client()
client.username_pw_set(os.getenv("ACTUATOR_USERNAME"), os.getenv("ACTUATOR_PASSWORD"))
client.tls_set(
    ca_certs=os.getenv("CA_CRT"),
    certfile=os.getenv("ACTUATOR_CRT"),
    keyfile=os.getenv("ACTUATOR_KEY")
)
client.connect(os.getenv("BROKER"), int(os.getenv("PORT")))

def on_message(client, userdata, msg):
    global pump_rate
    data = json.loads(msg.payload)
    print("Pump set to:", data["pump_rate"])

    sock.send(json.dumps({
        "pump_rate": data["pump_rate"]
    }).encode())

client.on_message = on_message
client.subscribe(os.getenv("TOPIC_PUMP_ACC"))
client.loop_forever()