import json
import numpy as np
import paho.mqtt.client as mqtt
from sklearn.ensemble import IsolationForest
from dotenv import load_dotenv
import os

load_dotenv()

TOPIC_DEBIT = os.getenv("TOPIC_DEBIT")
TOPIC_QUANTITY = os.getenv("TOPIC_QUANTITY")

client = mqtt.Client()
client.username_pw_set(os.getenv("CONTROLLER_USERNAME"), os.getenv("CONTROLLER_PASSWORD"))
client.tls_set(
    os.getenv("CA_CRT"),
    os.getenv("CONTROLLER_CRT"),
    os.getenv("CONTROLLER_KEY")
)
client.connect(os.getenv("BROKER"), int(os.getenv("PORT")))

model = IsolationForest(contamination=0.1)
data_buffer = []
stop_pumping = False

def on_message(client, userdata, msg):
    global data_buffer, stop_pumping

    data = json.loads(msg.payload)

    print(f"Received on {msg.topic}: {data}")

    if stop_pumping:
        print("⚠️ Pumping stopped due to high level!")
        return

    if msg.topic == TOPIC_DEBIT:
        flow = data["flow_rate"]
        data_buffer.append([flow])
        
        model.fit(data_buffer)
        pred = model.predict([[flow]])



        print(f"data {data}")
        print(f"Anomaly prediction: {pred}")


        if pred[0] == -1:
            print("⚠️ Anomaly detected! Switching fallback")
            command = {"pump_rate": 0}
        else:
            command = {"pump_rate": flow * 0.8}

        client.publish(os.getenv("TOPIC_PUMP_ACC"), json.dumps(command))
    
    if msg.topic == TOPIC_QUANTITY:
        level = data["level"]
        print(f"Current level: {level}")

        if level > 90:
            stop_pumping = True

client.on_message = on_message
client.subscribe(TOPIC_DEBIT)
client.subscribe(TOPIC_QUANTITY)
client.loop_forever()
