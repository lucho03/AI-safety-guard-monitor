import time
import json
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os

import random

load_dotenv()

client = mqtt.Client()
client.username_pw_set(os.getenv("FIRST_SENSOR_USERNAME"), os.getenv("FIRST_SENSOR_PASSWORD"))
client.tls_set(
    ca_certs=os.getenv("CA_CRT"),
    certfile=os.getenv("FIRST_SENSOR_CRT"),
    keyfile=os.getenv("FIRST_SENSOR_KEY")
)
client.connect(os.getenv("BROKER"), int(os.getenv("PORT")))

# initial flow rate
flow_rate = 0.0

while True:
    # симулиране на шум
    flow_rate += random.uniform(-0.5, 0.5)

    payload = {
        "flow_rate": round(flow_rate, 2),
        "timestamp": time.time()
    }

    client.publish(os.getenv("TOPIC_DEBIT"), json.dumps(payload))
    print("Debit:", payload)

    time.sleep(1)