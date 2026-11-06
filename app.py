
# Real-Time Healthcare Monitoring Dashboard
# Standalone Streamlit version for Community Cloud

import random
from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Healthcare Monitoring System",
    page_icon="🏥",
    layout="wide"
)


# --------------------------------------------------
# 2. PATIENT INFORMATION
# --------------------------------------------------

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


# --------------------------------------------------
# 3. GENERATE SIMULATED PATIENT READINGS
# --------------------------------------------------

def generate_readings():

    records = []

    # One common timestamp for this batch
    current_time = datetime.now()

    for patient_id, (base_hr, base_temp) in PATIENTS.items():

        heart_rate = int(random.gauss(base_hr, 8))
        temperature = round(random.gauss(base_temp, 0.3), 1)

        # Occasionally generate abnormal heart rate
        if random.random() < 0.12:
            heart_rate = random.choice([
                random.randint(45, 59),
                random.randint(101, 125)
            ])

        # Occasionally generate abnormal temperature
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
            "timestamp": current_time
        })

    return records


# --------------------------------------------------
# 4. SESSION STATE
# --------------------------------------------------

if "records" not in st.session_state:
    st.session_state.records = []


# --------------------------------------------------
# 5. AUTOMATIC REFRESH
# --------------------------------------------------

st_autorefresh(
    interval=3000,
    key="refresh"
)


# --------------------------------------------------
# 6. DASHBOARD TITLE
# --------------------------------------------------

st.title("🏥 Real-Time Healthcare Monitoring System")

st.caption(
    "Simulated patient IoT monitoring dashboard"
)


# --------------------------------------------------
# 7. SIDEBAR CONTROLS
# --------------------------------------------------

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


# --------------------------------------------------
# 8. GENERATE NEW READINGS
# --------------------------------------------------

if running:

    new_records = generate_readings()

    st.session_state.records.extend(new_records)

    # Keep only the latest 300 readings
    st.session_state.records = (
        st.session_state.records[-300:]
    )


# --------------------------------------------------
# 9. CONVERT DATA INTO DATAFRAME
# --------------------------------------------------

data = pd.DataFrame(st.session_state.records)

if data.empty:

    st.info(
        "Waiting for patient readings. "
        "Turn on the simulator."
    )

    st.stop()


data["timestamp"] = pd.to_datetime(data["timestamp"])

data = data.sort_values("timestamp")


# --------------------------------------------------
# 10. LATEST READING FOR EACH PATIENT
# --------------------------------------------------

latest = (
    data.sort_values("timestamp")
    .drop_duplicates(
        subset="patient_id",
        keep="last"
    )
)


# --------------------------------------------------
# 11. DASHBOARD STATISTICS
# --------------------------------------------------

patient_count = latest["patient_id"].nunique()

normal_count = (
    latest["status"] == "NORMAL"
).sum()

alert_count = (
    latest["status"] == "ALERT"
).sum()


col1, col2, col3 = st.columns(3)

col1.metric(
    "Patients Monitored",
    patient_count
)

col2.metric(
    "Normal Patients",
    normal_count
)

col3.metric(
    "Patients Needing Attention",
    alert_count
)


st.divider()


# --------------------------------------------------
# 12. HEART RATE AND TEMPERATURE CHARTS
# --------------------------------------------------

left, right = st.columns(2)


# HEART RATE CHART

with left:

    st.subheader("❤️ Heart Rate Trend")

    st.line_chart(
        data,
        x="timestamp",
        y="heart_rate",
        color="patient_id",
        height=350
    )

    st.caption(
        "Heart rate in beats per minute (BPM)"
    )


# TEMPERATURE CHART

with right:

    st.subheader("🌡️ Temperature Trend")

    st.line_chart(
        data,
        x="timestamp",
        y="temperature",
        color="patient_id",
        height=350
    )

    st.caption(
        "Body temperature in °C"
    )


st.divider()


# --------------------------------------------------
# 13. LATEST PATIENT STATUS
# --------------------------------------------------

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


# --------------------------------------------------
# 14. ABNORMAL PATIENT READINGS
# --------------------------------------------------

st.subheader("⚠️ Abnormal Patient Readings")

alerts = latest[
    latest["status"] == "ALERT"
]

if alerts.empty:

    st.success(
        "No abnormal readings in the latest records."
    )

else:

    st.dataframe(
        alerts[display_cols],
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# 15. DISCLAIMER
# --------------------------------------------------

st.caption(
    "Educational prototype only. Thresholds are "
    "simplified examples, not medical advice or "
    "clinically validated alert limits."
)
