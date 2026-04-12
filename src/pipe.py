import socket
import threading
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("HOST")

PORT_IN = int(os.getenv("PIPE_PORT_LISTENING"))
PORT_FLOW = int(os.getenv("PIPE_PORT_FLOW"))
PORT_LEVEL = int(os.getenv("PIPE_PORT_LEVEL"))

pump_rate = 0.0
flow_rate = 0.0
tank_level = 0.0

capacity = 100.0

flow_clients = []
level_clients = []

lock = threading.Lock()

def actuator_process():
    global pump_rate

    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connection.bind((HOST, PORT_IN))
    connection.listen(1)

    print(f"[PIPE] Listening for actuator on {PORT_IN}")

    conn, addr = connection.accept()
    print("[PIPE] Actuator connected:", addr)

    while True:
        data = conn.recv(1024)
        if not data:
            break

        msg = json.loads(data.decode())

        with lock:
            pump_rate = msg.get("pump_rate", 0.0)

        print(f"[PIPE] Pump rate updated: {pump_rate}")

def flow_process():
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connection.bind((HOST, PORT_FLOW))
    connection.listen(5)

    print(f"[PIPE] Flow sensor connection on {PORT_FLOW}")

    while True:
        conn, addr = connection.accept()
        print("[PIPE] Flow sensor connected:", addr)
        flow_clients.append(conn)

def level_process():
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connection.bind((HOST, PORT_LEVEL))
    connection.listen(5)

    print(f"[PIPE] Level sensor connection on {PORT_LEVEL}")

    while True:
        conn, addr = connection.accept()
        print("[PIPE] Level sensor connected:", addr)
        level_clients.append(conn)

def simulation_loop():
    global flow_rate, tank_level

    while True:
        with lock:
            flow_rate += (pump_rate - flow_rate) * 0.2

            tank_level += flow_rate * 0.1
            tank_level = max(0, min(capacity, tank_level))

            flow_msg = json.dumps({"flow_rate": round(flow_rate, 2)}).encode()
            level_msg = json.dumps({"level": round(tank_level, 2)}).encode()
        
        for conn in flow_clients:
            try:
                conn.send(flow_msg)
            except:
                flow_clients.remove(conn)

        for conn in level_clients:
            try:
                conn.send(level_msg)
            except:
                level_clients.remove(conn)

        print(f"[PIPE] Flow: {flow_rate:.2f} | Level: {tank_level:.2f}")

        time.sleep(1)

threading.Thread(target=actuator_process, daemon=True).start()
threading.Thread(target=flow_process, daemon=True).start()
threading.Thread(target=level_process, daemon=True).start()

simulation_loop()