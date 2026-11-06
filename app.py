# Real-Time Healthcare Monitoring Dashboard
# Standalone Streamlit version for Community Cloud

import random
from datetime import datetime
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Page configuration
st.set_page_config(
    page_title="Healthcare Monitoring System",
    page_icon="🏥",
    layout="wide"
)

# Patient information and normal baseline readings
PATIENTS = {
    "P101": (75, 36.8),
    "P102": (85, 37.0),
    "P103": (80, 36.9),
    "P104": (70, 36.5),
    "P105": (90, 37.2),
    "P106": (78, 36.8),
    "P107": (72, 36.9),
    "P108": (82, 37.1),
    "P109": (85, 37.1),
    "P110": (76, 36.7)
}

# Generate one simulated reading for each patient
def generate_readings():
    records = []

    for patient_id, (base_hr, base_temp) in PATIENTS.items():

        heart_rate = int(random.gauss(base_hr, 8))
        temperature = round(random.gauss(base_temp, 0.3), 1)

        # Occasionally generate abnormal readings for demonstration
        if random.random() < 0.12:
            heart_rate = random.choice([
                random.randint(45, 59),
                random.randint(101, 125)
            ])

        if random.random() < 0.10:
            temperature = random.choice([
                round(random.uniform(35.0, 35.9), 1),
                round(random.uniform(38.1, 39.5), 1)
            ])

        reasons = []

        if heart_rate < 60 or heart_rate > 100:
            reasons.append("Abnormal heart rate")

        if temperature < 36 or temperature > 38:
            reasons.append("Abnormal temperature")

        records.append({
            "patient_id": patient_id,
            "heart_rate": heart_rate,
            "temperature": temperature,
            "status": "ALERT" if reasons else "NORMAL",
            "alert_reason": ", ".join(reasons) if reasons else "None",
            "timestamp": datetime.now()
        })

    return records


# Store readings during the user's dashboard session
if "records" not in st.session_state:
    st.session_state.records = []

# Refresh the dashboard every 3 seconds
st_autorefresh(interval=3000, key="refresh")

# Dashboard title
st.title("🏥 Real-Time Healthcare Monitoring System")
st.caption("Simulated patient IoT monitoring dashboard")

# Sidebar controls
with st.sidebar:
    st.header("IoT Simulator")

    running = st.toggle(
        "Generate patient readings",
        value=True
    )

    st.info(
        "This dashboard uses simulated patient data. "
        "It is an educational demonstration, not a medical device."
    )

    if st.button("Clear patient history"):
        st.session_state.records = []
        st.rerun()

# Generate new readings
if running:
    new_records = generate_readings()
    st.session_state.records.extend(new_records)

    # Keep only the latest 300 readings
    st.session_state.records = st.session_state.records[-300:]

# Convert records into a DataFrame
data = pd.DataFrame(st.session_state.records)

if data.empty:
    st.info("Waiting for patient readings. Turn on the simulator.")
    st.stop()

# Get the latest reading for each patient
latest = (
    data.sort_values("timestamp")
    .drop_duplicates("patient_id", keep="last")
)

# Calculate dashboard statistics
patient_count = latest["patient_id"].nunique()
normal_count = (latest["status"] == "NORMAL").sum()
alert_count = (latest["status"] == "ALERT").sum()

# Display summary cards
col1, col2, col3 = st.columns(3)

col1.metric("Patients Monitored", patient_count)
col2.metric("Normal Patients", normal_count)
col3.metric("Patients Needing Attention", alert_count)

st.divider()

# Display heart rate and temperature charts
left, right = st.columns(2)

with left:
    st.subheader("❤️ Heart Rate Trend")

    heart_chart = data.pivot_table(
        index="timestamp",
        columns="patient_id",
        values="heart_rate",
        aggfunc="last"
    )

    st.line_chart(heart_chart)
    st.caption("Heart rate in beats per minute (BPM)")

with right:
    st.subheader("🌡️ Temperature Trend")

    temp_chart = data.pivot_table(
        index="timestamp",
        columns="patient_id",
        values="temperature",
        aggfunc="last"
    )

    st.line_chart(temp_chart)
    st.caption("Body temperature in °C")

st.divider()

# Latest patient readings
st.subheader("Latest Patient Status")

display_cols = [
    "patient_id",
    "heart_rate",
    "temperature",
    "status",
    "alert_reason",
    "timestamp"
]

st.dataframe(
    latest[display_cols].sort_values("patient_id"),
    use_container_width=True,
    hide_index=True
)

# Display abnormal readings
st.subheader("⚠️ Abnormal Patient Readings")

alerts = latest[latest["status"] == "ALERT"]

if alerts.empty:
    st.success("No abnormal readings in the latest records.")
else:
    st.dataframe(
        alerts[display_cols],
        use_container_width=True,
        hide_index=True
    )

st.caption(
    "Educational prototype only. Thresholds are simplified examples, "
    "not medical advice or clinically validated alert limits."
)
