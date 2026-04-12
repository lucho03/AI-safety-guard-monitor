import time
import json
import socket
import json
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((os.getenv("HOST"), int(os.getenv("PIPE_PORT_LEVEL"))))

client = mqtt.Client()
client.username_pw_set(os.getenv("SECOND_SENSOR_USERNAME"), os.getenv("SECOND_SENSOR_PASSWORD"))
client.tls_set(
    ca_certs=os.getenv("CA_CRT"),
    certfile=os.getenv("SECOND_SENSOR_CRT"),
    keyfile=os.getenv("SECOND_SENSOR_KEY")
)
client.connect(os.getenv("BROKER"), int(os.getenv("PORT")))

while True:
    data = sock.recv(1024)
    msg = json.loads(data.decode())

    level = msg["level"]

    payload = {
        "level": round(level, 2),
        "timestamp": time.time()
    }

    client.publish(os.getenv("TOPIC_QUANTITY"), json.dumps(payload))
    print("Level:", payload)

    time.sleep(1)