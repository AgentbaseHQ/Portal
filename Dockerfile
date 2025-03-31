FROM debian:bookworm-slim

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install ca-certificates for HTTPS repo support
RUN apt-get update && apt-get install -y ca-certificates

# Install necessary packages
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    xterm \
    chromium \
    net-tools \
    python3 \
    python3-pip \
    nodejs \
    npm \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-freefont-ttf \
    fonts-liberation \
    fonts-dejavu \
    procps \
    supervisor \
    novnc \
    websockify \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
    
# Install Python packages
RUN pip3 install --break-system-packages --no-cache-dir uvicorn pydantic fastapi

# Create a non-root user to run the browser
RUN useradd -m portal
WORKDIR /home/portal

# Copy the browser directory to the root of the container
COPY controls /controls

# Setup environment variables
ENV DISPLAY=:99
ENV RESOLUTION=1920x1080x24

# Expose VNC port
EXPOSE 5900
# Expose noVNC port
EXPOSE 6080
# Expose common FastAPI port
EXPOSE 8000
# Expose common Node.js port
EXPOSE 3000

# Copy start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Set the entrypoint
ENTRYPOINT ["/start.sh"] 