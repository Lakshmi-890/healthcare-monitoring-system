# Real-Time Healthcare Monitoring System

A classroom demonstration of simulated patient IoT readings processed with
Apache PySpark Structured Streaming and displayed in a Streamlit dashboard.

## Architecture

Simulated sensor readings -> JSON files -> PySpark Structured Streaming ->
abnormality classification -> JSON Lines output -> Streamlit dashboard.

## Demo thresholds

- Heart rate below 60 or above 100 BPM: abnormal.
- Temperature below 36 °C or above 38 °C: abnormal.

These are simplified educational thresholds, not clinical diagnostic rules.
Do not use this prototype for medical decisions or emergency response.

## Run locally with Docker

Requirements: Docker Engine and Docker Compose.

```bash
docker compose up --build -d
```

Open http://localhost:8501.

See logs:

```bash
docker compose logs -f
```

Stop:

```bash
docker compose down
```

Remove demo data and checkpoint too:

```bash
docker compose down -v
```

## Deploy on an Oracle Cloud Always Free Ubuntu VM

1. Create an Ubuntu 24.04 VM using only Always Free eligible resources.
2. Assign a public IPv4 address.
3. Add an ingress rule for TCP port 8501 in the VM subnet's security list or network security group.
4. SSH into the VM.
5. Install Docker Engine and the Docker Compose plugin using Docker's official Ubuntu instructions.
6. Copy or clone this project folder onto the VM.
7. From the project folder, run:

```bash
docker compose up --build -d
```

8. Open `http://YOUR_PUBLIC_IP:8501` in a browser.

If Ubuntu's UFW firewall is enabled, allow the app port:

```bash
sudo ufw allow 8501/tcp
```

For a public-facing production service, configure HTTPS, authentication, monitoring,
backups and stricter network access. Do not expose real patient information in this demo.

## Services

- `processor`: generates simulated JSON files and processes them using Spark Structured Streaming.
- `dashboard`: reads processed JSON Lines and refreshes the dashboard every 3 seconds.
- `healthcare_data`: shared Docker volume for input files, Spark checkpoint and dashboard output.

## Notes

- This demo uses simulated readings, not actual medical sensors.
- Free cloud instances can sleep, be reclaimed under provider policies, or be unavailable
  in a selected region. Always verify that the VM shape and storage are marked Always Free.
- The public source repository should not contain secrets or real patient records.
