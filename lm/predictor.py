#!/usr/bin/env python3
"""Build an ML dataset from Firebase history and predict future room scores.

Input Firebase structure:
  history/<room_id>/<timestamp>

Output Firebase structure:
  predictions/<room_id>

The model predicts the room score after a configurable time horizon.
"""

import argparse
import json
import time
import urllib.parse
import urllib.request

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split


FEATURE_COLUMNS = [
    "temperature",
    "humidity",
    "noise",
    "presence",
    "hour",
    "day_of_week",
    "score_now",
]


def firebase_url(database_host, path, auth_token=None):
    url = f"https://{database_host.rstrip('/')}/{path.lstrip('/')}.json"
    if auth_token:
        url += "?auth=" + urllib.parse.quote(auth_token)
    return url


def get_json(url):
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def put_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url=url,
        data=data,
        method="PUT",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.status


def calculate_score(row):
    temperature = float(row["temperature"])
    humidity = float(row["humidity"])
    noise = float(row["noise"])
    presence = bool(row["presence"])

    if 20 <= temperature <= 23:
        temperature_score = 35
    elif 18 <= temperature <= 25:
        temperature_score = 25
    elif 16 <= temperature <= 28:
        temperature_score = 15
    else:
        temperature_score = 5

    if noise <= 40:
        noise_score = 35
    elif noise <= 60:
        noise_score = 22
    elif noise <= 75:
        noise_score = 10
    else:
        noise_score = 3

    if 40 <= humidity <= 60:
        humidity_score = 20
    elif 30 <= humidity <= 70:
        humidity_score = 12
    else:
        humidity_score = 5

    presence_score = 5 if presence else 10
    return max(0, min(100, temperature_score + noise_score + humidity_score + presence_score))


def history_to_dataframe(history):
    rows = []

    if not history:
        return pd.DataFrame()

    for room_id, room_history in history.items():
        if not isinstance(room_history, dict):
            continue

        for key, value in room_history.items():
            if not isinstance(value, dict):
                continue

            try:
                timestamp = int(value.get("lastUpdate", key))
                rows.append(
                    {
                        "room_id": room_id,
                        "timestamp": timestamp,
                        "temperature": float(value["temperature"]),
                        "humidity": float(value["humidity"]),
                        "noise": float(value["noise"]),
                        "presence": 1 if bool(value["presence"]) else 0,
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.sort_values(["room_id", "timestamp"]).reset_index(drop=True)

    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["hour"] = df["datetime"].dt.hour
    df["day_of_week"] = df["datetime"].dt.dayofweek
    df["score_now"] = df.apply(calculate_score, axis=1)

    return df


def add_future_target(df, horizon_minutes):
    rows = []
    horizon_ms = horizon_minutes * 60 * 1000

    for room_id, room_df in df.groupby("room_id"):
        room_df = room_df.sort_values("timestamp").reset_index(drop=True)

        for _, row in room_df.iterrows():
            target_time = row["timestamp"] + horizon_ms
            future_rows = room_df[room_df["timestamp"] >= target_time]
            if future_rows.empty:
                continue

            future_row = future_rows.iloc[0]
            training_row = row.to_dict()
            training_row["target_score"] = int(future_row["score_now"])
            rows.append(training_row)

    return pd.DataFrame(rows)


def train_model(dataset):
    X = dataset[FEATURE_COLUMNS]
    y = dataset["target_score"]

    if len(dataset) < 10:
        raise ValueError("servono almeno 10 righe con target futuro per allenare il modello")

    if len(dataset) >= 30:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    else:
        X_train, X_test, y_train, y_test = X, X, y, y

    model = RandomForestRegressor(n_estimators=120, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, predictions))

    return model, mae


def trend_label(current_score, predicted_score):
    delta = predicted_score - current_score
    if delta >= 5:
        return "miglioramento"
    if delta <= -5:
        return "peggioramento"
    return "stabile"


def build_predictions(df, model, mae, horizon_minutes):
    predictions = {}
    generated_at = int(time.time() * 1000)

    for room_id, room_df in df.groupby("room_id"):
        latest = room_df.sort_values("timestamp").iloc[-1]
        features = pd.DataFrame([latest[FEATURE_COLUMNS].to_dict()])
        predicted_score = int(round(model.predict(features)[0]))
        predicted_score = max(0, min(100, predicted_score))
        current_score = int(latest["score_now"])

        predictions[room_id] = {
            "currentScore": current_score,
            "predictedScore": predicted_score,
            "horizonMinutes": horizon_minutes,
            "trend": trend_label(current_score, predicted_score),
            "model": "RandomForestRegressor",
            "mae": round(mae, 2),
            "generatedAt": generated_at,
        }

    return predictions


def run_once(args):
    history = get_json(firebase_url(args.database_host, "history", args.auth))
    df = history_to_dataframe(history)
    if df.empty:
        raise SystemExit("Nessun dato valido trovato in history/")

    dataset = add_future_target(df, args.horizon_minutes)
    if args.export_csv:
        dataset.to_csv(args.export_csv, index=False)
        print(f"Dataset esportato in {args.export_csv} ({len(dataset)} righe)")

    model, mae = train_model(dataset)
    predictions = build_predictions(df, model, mae, args.horizon_minutes)

    for room_id, payload in predictions.items():
        status = put_json(firebase_url(args.database_host, f"predictions/{room_id}", args.auth), payload)
        print(f"predictions/{room_id}: HTTP {status} -> {payload}")

    print(f"Training rows: {len(dataset)}")
    print(f"MAE: {mae:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Smart Study Rooms ML predictor")
    parser.add_argument("--database-host", required=True, help="Firebase RTDB host without https://")
    parser.add_argument("--auth", default=None, help="Optional Firebase database secret or auth token")
    parser.add_argument("--horizon-minutes", type=int, default=15, help="Prediction horizon. Default: 15")
    parser.add_argument("--export-csv", default=None, help="Optional path where the generated dataset CSV is saved")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=60, help="Loop interval in seconds. Default: 60")
    args = parser.parse_args()

    while True:
        run_once(args)
        if not args.loop:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
