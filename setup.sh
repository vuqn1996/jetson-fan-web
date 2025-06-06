#!/bin/bash
set -x

# Variables
USER=$(whoami)
PROJECT_DIR="/home/$USER/jetson-fan-web"

# Step 1: Update system and install dependencies
sudo apt update
sudo apt install -y python3-pip python3-tk

# Step 2: Change target_pwm owner and chmod
sudo chown asilla:asilla /sys/devices/pwm-fan/target_pwm
sudo chmod 666 /sys/devices/pwm-fan/target_pwm

# Step 3: Install Flask
pip3 install flask psutil

# Step 4: Create systemd service file
cat <<EOL | sudo tee /etc/systemd/system/jetson-fan-web.service
[Unit]
Description=Jetson Fan Control Web Dashboard
After=network.target

[Service]
ExecStart=/usr/bin/python3 $PROJECT_DIR/app.py
WorkingDirectory=$PROJECT_DIR
Restart=always
User=$USER
Group=$USER
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL

# Step 5: Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable jetson-fan-web
sudo systemctl start jetson-fan-web

# Step 6: Confirm the service is running
sudo systemctl status jetson-fan-web
