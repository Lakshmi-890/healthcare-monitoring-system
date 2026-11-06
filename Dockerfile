# One image is used by both the Spark processor and Streamlit dashboard.
FROM python:3.11-slim-bookworm

# Install Java 17 because PySpark runs on the Java Virtual Machine.
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Find the architecture-specific Java directory and expose a stable path.
RUN ln -s "$(dirname "$(dirname "$(readlink -f "$(which java)")")")" /opt/java

ENV JAVA_HOME=/opt/java
ENV PATH="${JAVA_HOME}/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV PYSPARK_PYTHON=python3

WORKDIR /app

# Install Python dependencies before copying source files for better build caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source into the image.
COPY app.py stream_processor.py ./

# Streamlit listens on port 8501 inside the container.
EXPOSE 8501
