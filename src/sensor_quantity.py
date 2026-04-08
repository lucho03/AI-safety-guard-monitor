import time
import json
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os

load_dotenv()

client = mqtt.Client()
client.username_pw_set(os.getenv("SECOND_SENSOR_USERNAME"), os.getenv("SECOND_SENSOR_PASSWORD"))
client.tls_set(
    ca_certs=os.getenv("CA_CRT"),
    certfile=os.getenv("SECOND_SENSOR_CRT"),
    keyfile=os.getenv("SECOND_SENSOR_KEY")
)
client.connect(os.getenv("BROKER"), int(os.getenv("PORT")))

# def on_message(client, userdata, msg):
#     global inflow, outflow
#     data = json.loads(msg.payload)

#     if msg.topic == "sensors/debit":
#         inflow = data["flow_rate"]

#     elif msg.topic == "actuator/state":
#         outflow = data["pump_rate"]



# client.on_message = on_message


# client.subscribe("sensors/debit")
# client.subscribe("actuator/state")

capacity = 100.0
current_level = 0.0

inflow = 0.0
outflow = 0.0

while True:
    current_level += inflow * 0.1
    current_level -= outflow * 0.1

    current_level = max(0, min(capacity, current_level))

    payload = {
        "level": round(current_level, 2),
        "timestamp": time.time()
    }

    client.publish(os.getenv("TOPIC_QUANTITY"), json.dumps(payload))
    print("Level:", payload)

    time.sleep(1)