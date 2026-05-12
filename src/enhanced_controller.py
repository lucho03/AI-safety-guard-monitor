import json
import os
import numpy as np
import paho.mqtt.client as mqtt
from sklearn.ensemble import IsolationForest
from dotenv import load_dotenv
import joblib

load_dotenv()

TOPIC_DEBIT = os.getenv("TOPIC_DEBIT")
TOPIC_QUANTITY = os.getenv("TOPIC_QUANTITY")
TOPIC_PUMP = os.getenv("TOPIC_PUMP_ACC")

MODEL_PATH = os.getenv("MODEL_PATH")

client = mqtt.Client()
client.username_pw_set(os.getenv("CONTROLLER_USERNAME"), os.getenv("CONTROLLER_PASSWORD"))
client.tls_set(
    os.getenv("CA_CRT"),
    os.getenv("CONTROLLER_CRT"),
    os.getenv("CONTROLLER_KEY")
)
client.connect(os.getenv("BROKER"), int(os.getenv("PORT")))

if os.path.exists(MODEL_PATH):
    print("Loading existing model...")
    model = joblib.load(MODEL_PATH)
    model_ready = True
else:
    print("Creating new model...")
    model = IsolationForest(contamination=0.1)
    model_ready = False

data_buffer = []

mode = "INIT"
stop_pumping = False
system_started = False
target_level = 50

Kp = 0.8
Ki = 0.05
Kd = 0.1

integral = 0
prev_error = 0

def pid_control(level):
    global integral, prev_error

    error = target_level - level

    integral += error
    integral = max(-100, min(100, integral))
    derivative = error - prev_error

    output = Kp * error + Ki * integral + Kd * derivative

    prev_error = error

    # ограничаване (много важно!)
    output = max(0, min(20, output))

    return output

def fallback_control(level):
    if level > 80:
        return 0
    elif level < 20:
        return 15
    else:
        return 8

def ai_control(flow):
    return flow * 0.8

def on_message(client, userdata, msg):
    global data_buffer, stop_pumping, mode, system_started, model_ready

    current_level = 0

    data = json.loads(msg.payload)
    print(f"\n📩 {msg.topic}: {data}")

    if msg.topic == TOPIC_QUANTITY:
        current_level = data["level"]
        stop_pumping = current_level > 90

        print(f"Tank level: {current_level}")

        if current_level <= 5:
            print("🟢 Tank empty → starting system")
            system_started = True

        if current_level > 90:
            print("🔴 HIGH LEVEL → STOP")
            stop_pumping = True
            mode = "FALLBACK"

        return

    if msg.topic == TOPIC_DEBIT:

        flow = data["flow_rate"]
        
        if not system_started:
            print("⏳ Waiting for system start...")
            return

        if stop_pumping:
            client.publish(TOPIC_PUMP, json.dumps({"pump_rate": 0}))
            return
        
        data_buffer.append([flow])

        # This has to be stopped when it's used in production
        if len(data_buffer) >= 50:
            print("🧠 Training model...")
            model.fit(data_buffer)

            joblib.dump(model, MODEL_PATH)
            print("💾 Model saved!")

            data_buffer.clear()
            model_ready = True
        
        if model_ready:
            pred = model.predict([[flow]])

            print(f"Prediction: {pred}")

            if pred[0] == -1:
                print("⚠️ Anomaly → FALLBACK")
                mode = "FALLBACK"
            else:
                mode = "AI"
        else:
            print("⚠️ Model not ready → FALLBACK")
            mode = "FALLBACK"
        
        if mode == "AI":
            pump_rate = pid_control(current_level)
        else:
            pump_rate = fallback_control(current_level)

        print(f"Mode: {mode} | Pump: {pump_rate}")

        client.publish(TOPIC_PUMP, json.dumps({"pump_rate": pump_rate}))

client.on_message = on_message
client.subscribe(TOPIC_DEBIT)
client.subscribe(TOPIC_QUANTITY)

print("🚀 PLC started...")
client.loop_forever()