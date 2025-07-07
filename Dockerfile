FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any). Using sqlite in lib for python.
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency specification first for better caching
COPY requirements.txt ./

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose any port if necessary (not required for polling bot)
# EXPOSE 8080

# Environment variables can be passed at runtime (e.g., TELEGRAM_BOT_TOKEN)
ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

# Default command to run the bot
CMD ["python", "run_bot.py"] 