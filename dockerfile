FROM python:3.10

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ghostscript \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Verify streamlit installation
RUN streamlit --version

# Copy all project files (including lab folders, model, format.csv)
COPY . .

# Create necessary directories if they don't exist
RUN mkdir -p ALS Bactochem Aminolab Element

EXPOSE 8501

# Set healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]