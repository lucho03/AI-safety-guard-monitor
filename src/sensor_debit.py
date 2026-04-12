import time
import json
import socket
import json
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((os.getenv("HOST"), int(os.getenv("PIPE_PORT_FLOW"))))

client = mqtt.Client()
client.username_pw_set(os.getenv("FIRST_SENSOR_USERNAME"), os.getenv("FIRST_SENSOR_PASSWORD"))
client.tls_set(
    ca_certs=os.getenv("CA_CRT"),
    certfile=os.getenv("FIRST_SENSOR_CRT"),
    keyfile=os.getenv("FIRST_SENSOR_KEY")
)
client.connect(os.getenv("BROKER"), int(os.getenv("PORT")))

while True:
    data = sock.recv(1024)
    msg = json.loads(data.decode())

    flow = msg["flow_rate"]

    payload = {
        "flow_rate": round(flow, 2),
        "timestamp": time.time()
    }

    client.publish(os.getenv("TOPIC_DEBIT"), json.dumps(payload))
    print("Debit:", payload)

    time.sleep(1)