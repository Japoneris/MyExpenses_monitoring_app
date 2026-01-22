# Use Ingenico's base Python image from the internal Artifactory
FROM artfact-rndsoft.ingenico.com/docker-public/library/python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the source code and dependencies file into the container
COPY src/ /app/
COPY requirements.txt /app/requirements.txt

# Install system dependencies (e.g., curl for health checks)
RUN apt-get update && apt upgrade -y \
    && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install required Python packages
RUN pip3 install --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt


# Expose the default Streamlit port
EXPOSE 8501

# Define a healthcheck for CI/CD and monitoring
#HEALTHCHECK CMD curl --fail http://localhost:8501/in2-tech/_stcore/health || exit 1

# Define the entrypoint command to start the Streamlit application
ENTRYPOINT ["streamlit", "run", "app.py"]