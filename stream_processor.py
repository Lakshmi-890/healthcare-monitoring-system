# Background process: simulates IoT devices and processes their JSON files
# with Apache Spark Structured Streaming.

from pathlib import Path
from datetime import datetime, timezone
import json
import os
import random
import time
import shutil

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from pyspark.sql.functions import col, when, lit, concat_ws, to_timestamp

# Shared folder is mounted into both Docker services.
DATA_DIR = Path("/app/shared")
INPUT_DIR = DATA_DIR / "input"
CHECKPOINT_DIR = DATA_DIR / "checkpoint"
OUTPUT_FILE = DATA_DIR / "processed.jsonl"
CONTROL_FILE = DATA_DIR / "control.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
INPUT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

# Example readings are deliberately varied so the dashboard shows normal
# and abnormal examples. These are simulated values, not real patients.
SAMPLE_PATIENTS = [
    {"patient_id": "P101", "heart_rate": 75,  "temperature": 36.8},
    {"patient_id": "P102", "heart_rate": 115, "temperature": 37.0},
    {"patient_id": "P103", "heart_rate": 80,  "temperature": 39.2},
    {"patient_id": "P104", "heart_rate": 55,  "temperature": 36.5},
    {"patient_id": "P105", "heart_rate": 90,  "temperature": 37.2},
    {"patient_id": "P106", "heart_rate": 120, "temperature": 39.5},
    {"patient_id": "P107", "heart_rate": 72,  "temperature": 36.9},
    {"patient_id": "P108", "heart_rate": 48,  "temperature": 35.5},
    {"patient_id": "P109", "heart_rate": 85,  "temperature": 37.1},
    {"patient_id": "P110", "heart_rate": 105, "temperature": 38.5},
]

# Spark expects a fixed schema for streaming file sources.
PATIENT_SCHEMA = StructType([
    StructField("patient_id", StringType(), True),
    StructField("heart_rate", IntegerType(), True),
    StructField("temperature", DoubleType(), True),
    StructField("timestamp", StringType(), True),
])

def simulator_is_running():
    """Return the dashboard's simulator setting; run by default."""
    try:
        return json.loads(CONTROL_FILE.read_text()).get("running", True)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return True

def generate_one_reading(index: int):
    """Write one complete JSON file, then atomically rename it into the input folder."""
    patient = SAMPLE_PATIENTS[index % len(SAMPLE_PATIENTS)].copy()
    # Add small random variation to make repeated readings look more realistic.
    patient["heart_rate"] += random.randint(-3, 3)
    patient["temperature"] = round(patient["temperature"] + random.uniform(-0.2, 0.2), 1)
    patient["timestamp"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Spark watches only *.json files. Use a temporary suffix until writing finishes.
    final_path = INPUT_DIR / f"reading_{time.time_ns()}.json"
    temp_path = INPUT_DIR / f".{final_path.name}.tmp"

    temp_path.write_text(json.dumps(patient), encoding="utf-8")
    os.replace(temp_path, final_path)
    print(f"Generated simulated reading: {patient}", flush=True)

def write_processed_batch(batch_df, batch_id: int):
    """Write each processed Spark micro-batch to JSON Lines for the dashboard."""
    rows = batch_df.toJSON().collect()
    if not rows:
        return

    # Append one complete JSON object per line.
    with OUTPUT_FILE.open("a", encoding="utf-8") as output:
        for row in rows:
            output.write(row + "\n")

    print(f"Processed Spark batch {batch_id}: {len(rows)} reading(s)", flush=True)

def main():
    # Configure Spark for a small educational VM.
    spark = (
        SparkSession.builder
        .appName("HealthcareMonitoringSystem")
        .master("local[2]")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    # Read new JSON files as a Structured Streaming source.
    stream = (
        spark.readStream
        .schema(PATIENT_SCHEMA)
        .option("maxFilesPerTrigger", 1)
        .json(str(INPUT_DIR))
    )

    # Apply simple demonstration thresholds:
    # heart rate outside 60-100 BPM OR temperature outside 36-38 °C => ALERT.
    classified = (
        stream
        .withColumn("event_time", to_timestamp(col("timestamp")))
        .withColumn(
            "status",
            when(
                (col("heart_rate") < 60) |
                (col("heart_rate") > 100) |
                (col("temperature") < 36.0) |
                (col("temperature") > 38.0),
                lit("ALERT")
            ).otherwise(lit("NORMAL"))
        )
        .withColumn(
            "alert_reason",
            concat_ws(
                "; ",
                when(
                    (col("heart_rate") < 60) | (col("heart_rate") > 100),
                    lit("Abnormal Heart Rate")
                ),
                when(
                    (col("temperature") < 36.0) | (col("temperature") > 38.0),
                    lit("Abnormal Temperature")
                )
            )
        )
        .drop("event_time")
    )

    # Start the streaming query before generating the first input file.
    query = (
        classified.writeStream
        .foreachBatch(write_processed_batch)
        .outputMode("append")
        .option("checkpointLocation", str(CHECKPOINT_DIR))
        .trigger(processingTime="2 seconds")
        .start()
    )

    print("PySpark Structured Streaming started.", flush=True)

    index = 0
    try:
        while True:
            if simulator_is_running():
                generate_one_reading(index)
                index += 1
            time.sleep(3)
    except KeyboardInterrupt:
        print("Stopping simulator...", flush=True)
    finally:
        query.stop()
        spark.stop()

if __name__ == "__main__":
    main()
