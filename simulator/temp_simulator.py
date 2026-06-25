import argparse
import json
import random
import time
import urllib.error
import urllib.request
import serial
import re
import threading


ROOMS = {
    "room1": "Aula 1",
    "room2": "Aula 2",
}

latest_temp = None


def serial_reader(ser):
    global latest_temp

    while True:
        line = ser.readline().decode(errors="ignore").strip()
        print("RAW Arduino:", line)

        match = re.search(r"-?\d+(\.\d+)?", line)
        if match:
            latest_temp = float(match.group())
            print("TEMP AGGIORNATA:", latest_temp)


def build_payload(room_name, temperature=None):
    return {
        "name": room_name,
        "temperature": temperature if temperature is not None else round(random.uniform(19.0, 27.0), 1),
        "humidity": round(random.uniform(35.0, 70.0), 0),
        "noise": round(random.uniform(20.0, 80.0), 0),
        "presence": random.choice([True, False]),
        "lastUpdate": int(time.time() * 1000),
    }


def put_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="PUT",
                                  headers={"Content-Type": "application/json"})

    with urllib.request.urlopen(req, timeout=10) as res:
        return res.status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-host", required=True)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--serial-port", default="COM3")
    parser.add_argument("--baudrate", type=int, default=9600)

    args = parser.parse_args()

    base_url = f"https://{args.database_host.rstrip('/')}/rooms"

    ser = serial.Serial(args.serial_port, args.baudrate, timeout=1)

    
    thread = threading.Thread(target=serial_reader, args=(ser,), daemon=True)
    thread.start()

    print("Started")

    while True:

        for room_id, room_name in ROOMS.items():

            if room_id == "room1":
                payload = build_payload(room_name, temperature=latest_temp)
            else:
                payload = build_payload(room_name)

            url = f"{base_url}/{room_id}.json"

            try:
                put_json(url, payload)
                print(room_id, payload)
            except Exception as e:
                print("error:", e)

        time.sleep(args.interval)


if __name__ == "__main__":
    main()