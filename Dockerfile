# Use official Python slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all files into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default command for Render (web service)
CMD ["streamlit", "run", "app.py", "--server.port=$PORT", "--server.enableCORS=false"]
