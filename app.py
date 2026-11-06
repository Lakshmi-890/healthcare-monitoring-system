# Streamlit dashboard for the PySpark healthcare monitoring demo.
# This page reads processed records written by stream_processor.py.

from pathlib import Path
import json
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# All containers share this folder through Docker Compose.
DATA_DIR = Path("/app/shared")
OUTPUT_FILE = DATA_DIR / "processed.jsonl"
CONTROL_FILE = DATA_DIR / "control.json"

st.set_page_config(
    page_title="Healthcare Monitoring",
    page_icon="🏥",
    layout="wide"
)

def read_control():
    """Read the simulator on/off setting; default to ON for a fresh deployment."""
    try:
        return json.loads(CONTROL_FILE.read_text()).get("running", True)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return True

def write_control(running: bool):
    """Tell the background processor whether it should generate simulated readings."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONTROL_FILE.write_text(json.dumps({"running": running}))

def load_records():
    """Load complete JSON lines; ignore a partially written final line safely."""
    records = []
    if not OUTPUT_FILE.exists():
        return pd.DataFrame()

    with OUTPUT_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not records:
        return pd.DataFrame()

    frame = pd.DataFrame(records)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    frame = frame.dropna(subset=["timestamp"])
    return frame.sort_values("timestamp")

def update_simulator():
    """Callback used by the sidebar toggle."""
    write_control(st.session_state.simulator_running)

# Automatically refresh the dashboard every 3 seconds.
st_autorefresh(interval=3000, key="dashboard_refresh")

st.title("🏥 Real-Time Healthcare Monitoring System")
st.caption("PySpark Structured Streaming • Simulated patient IoT readings")

# Let the user start or pause the simulated sensor feed.
with st.sidebar:
    st.header("IoT Simulator")
    st.toggle(
        "Generate patient readings",
        value=read_control(),
        key="simulator_running",
        on_change=update_simulator,
        help="Turn the simulated patient sensor feed on or off."
    )
    st.info(
        "This is a classroom demonstration using simulated data. "
        "It is not connected to medical devices."
    )

data = load_records()

if data.empty:
    st.warning("Waiting for the first patient readings. The stream processor may still be starting.")
    st.stop()

# Keep only the latest reading for each patient for the summary cards.
latest = (
    data.sort_values("timestamp")
        .drop_duplicates(subset=["patient_id"], keep="last")
)

normal_count = int((latest["status"] == "NORMAL").sum())
alert_count = int((latest["status"] == "ALERT").sum())
patient_count = int(latest["patient_id"].nunique())

# Display high-level patient statistics.
col1, col2, col3 = st.columns(3)
col1.metric("Patients monitored", patient_count)
col2.metric("Normal patients", normal_count)
col3.metric("Patients needing attention", alert_count)

st.divider()

# Display recent heart-rate and temperature trends.
left, right = st.columns(2)

with left:
    st.subheader("Heart rate trend")
    heart_chart = data[["timestamp", "patient_id", "heart_rate"]].copy()
    heart_chart["patient"] = heart_chart["patient_id"]
    st.line_chart(
        heart_chart.pivot_table(
            index="timestamp",
            columns="patient",
            values="heart_rate",
            aggfunc="last"
        )
    )
    st.caption("Illustrative heart-rate readings in beats per minute (BPM).")

with right:
    st.subheader("Temperature trend")
    temp_chart = data[["timestamp", "patient_id", "temperature"]].copy()
    temp_chart["patient"] = temp_chart["patient_id"]
    st.line_chart(
        temp_chart.pivot_table(
            index="timestamp",
            columns="patient",
            values="temperature",
            aggfunc="last"
        )
    )
    st.caption("Illustrative temperature readings in °C.")

st.divider()

# Show the latest known reading for each patient.
st.subheader("Latest patient status")
display_cols = [
    "patient_id", "heart_rate", "temperature",
    "status", "alert_reason", "timestamp"
]
st.dataframe(
    latest[display_cols].sort_values("patient_id", ascending=True),
    use_container_width=True,
    hide_index=True
)

# Show current alerts separately for quick review.
st.subheader("⚠️ Current abnormal readings")
alerts = latest[latest["status"] == "ALERT"].copy()

if alerts.empty:
    st.success("No abnormal readings in the latest patient records.")
else:
    st.dataframe(
        alerts[display_cols].sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True
    )

st.caption(
    "Educational prototype only. Thresholds are simplified examples, "
    "not medical advice or a clinically validated alert system."
)
