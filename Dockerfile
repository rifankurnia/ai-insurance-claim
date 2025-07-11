FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-eng poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app/ ./app/
COPY utils/ ./utils/
COPY .env ./

# Set Streamlit to run on port 8701
ENV STREAMLIT_SERVER_PORT=8701

# Expose Streamlit port
EXPOSE 8701

# Run Streamlit app
CMD ["streamlit", "run", "app/app.py", "--server.port=8701", "--server.address=0.0.0.0"] 