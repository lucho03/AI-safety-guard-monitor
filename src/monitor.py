import json
import os
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

TOPIC_DEBIT = os.getenv("TOPIC_DEBIT")
TOPIC_QUANTITY = os.getenv("TOPIC_QUANTITY")

client = mqtt.Client()
client.username_pw_set(os.getenv("MONITOR_USERNAME"), os.getenv("MONITOR_PASSWORD"))
client.tls_set(
    ca_certs=os.getenv("CA_CRT"),
    certfile=os.getenv("MONITOR_CRT"),
    keyfile=os.getenv("MONITOR_KEY")
)
client.connect(os.getenv("BROKER"), int(os.getenv("PORT")))

flow_data = []
level_data = []

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)

    if msg.topic == TOPIC_DEBIT:
        flow_data.append(data["flow_rate"])
        print(f"Received flow rate: {flow_data[-1]}")

    elif msg.topic == TOPIC_QUANTITY:
        level_data.append(data["level"])
        print(f"Received tank level: {level_data[-1]}")

client.on_message = on_message
client.subscribe(TOPIC_DEBIT)
client.subscribe(TOPIC_QUANTITY)

plt.ion()

while True:
    client.loop()

    plt.clf()

    plt.subplot(2,1,1)
    plt.title("Flow Rate")
    plt.plot(flow_data[-50:])

    plt.subplot(2,1,2)
    plt.title("Tank Level")
    plt.plot(level_data[-50:])

    plt.pause(1)