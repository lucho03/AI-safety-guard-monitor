import json
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

client = mqtt.Client()
client.username_pw_set(os.getenv("ACTUATOR_USERNAME"), os.getenv("ACTUATOR_PASSWORD"))
client.tls_set(
    ca_certs=os.getenv("CA_CRT"),
    certfile=os.getenv("ACTUATOR_CRT"),
    keyfile=os.getenv("ACTUATOR_KEY")
)
client.connect(os.getenv("BROKER"), int(os.getenv("PORT")))

pump_rate = 1.0

def on_message(client, userdata, msg):
    global pump_rate
    data = json.loads(msg.payload)

    pump_rate += data["pump_rate"]

    print("Pump set to:", pump_rate)

    # client.publish(os.getenv("TOPIC_COMMAND"), json.dumps({
    #     "pump_rate": pump_rate
    # }))

client.on_message = on_message
client.subscribe(os.getenv("TOPIC_PUMP_ACC"))
client.loop_forever()