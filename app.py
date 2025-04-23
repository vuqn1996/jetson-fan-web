from flask import Flask, request, render_template_string
import os
import psutil
import threading
import time

app = Flask(__name__)
PWM_PATH = "/sys/devices/pwm-fan/target_pwm"
AUTO_MODE_FILE = "/tmp/auto_mode_flag"

# ----- Utility Functions -----
def read_fan_speed():
    try:
        with open(PWM_PATH, "r") as f:
            return int(f.read().strip())
    except:
        return -1

def write_fan_speed(value):
    try:
        value = max(0, min(255, int(value)))
        with open(PWM_PATH, "w") as f:
            f.write(str(value))
        return True
    except:
        return False

def get_temperature():
    try:
        temps = psutil.sensors_temperatures()
        for k in temps:
            if "thermal-fan-est" in k:
                return temps[k][0].current
        return next(iter(temps.values()))[0].current
    except:
        return -1

# ----- Auto Mode Control -----
def get_auto_mode():
    return os.path.exists(AUTO_MODE_FILE)

def set_auto_mode(enabled):
    if enabled:
        with open(AUTO_MODE_FILE, "w") as f:
            f.write("1")
    else:
        if os.path.exists(AUTO_MODE_FILE):
            os.remove(AUTO_MODE_FILE)

def auto_fan_control():
    while True:
        if get_auto_mode():
            temp = get_temperature()
            if temp < 40:
                pwm = 0
            elif temp < 50:
                pwm = 100
            elif temp < 60:
                pwm = 160
            else:
                pwm = 255
            write_fan_speed(pwm)
        time.sleep(5)

# ----- Flask Routes -----
@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    auto_mode = get_auto_mode()

    if request.method == "POST":
        if "set_speed" in request.form:
            set_auto_mode(False)
            speed = request.form.get("fan_speed")
            if write_fan_speed(speed):
                message = f"Fan speed set to {speed}"
            else:
                message = "Failed to set fan speed."
        elif "auto_mode" in request.form:
            auto_mode = not auto_mode
            set_auto_mode(auto_mode)
            message = f"Auto mode {'enabled' if auto_mode else 'disabled'}."

    fan_speed = read_fan_speed()
    temp = get_temperature()

    return render_template_string("""
    <html>
    <head>
        <title>Jetson Fan Dashboard</title>
        <script>
            function autoRefresh() {
                setTimeout(function() {
                    location.reload();
                }, 3000);
            }
            window.onload = autoRefresh;
        </script>
    </head>
    <body style="font-family:sans-serif;text-align:center;">
        <h1>Jetson Fan Control</h1>
        <p><strong>Temperature:</strong> {{ temp }} °C</p>
        <p><strong>Fan Speed:</strong> {{ fan_speed }} / 255</p>
        <form method="post">
            <label>Set Fan Speed (0-255):</label>
            <input type="number" name="fan_speed" min="0" max="255" value="{{ fan_speed }}">
            <button type="submit" name="set_speed">Set</button>
        </form>
        <form method="post" style="margin-top:20px;">
            <button type="submit" name="auto_mode">
                {{ 'Disable' if auto_mode else 'Enable' }} Auto Mode
            </button>
        </form>
        <p><em>Auto mode is {{ 'enabled' if auto_mode else 'disabled' }}.</em></p>
        <p style="color:green;">{{ message }}</p>
    </body>
    </html>
    """, fan_speed=fan_speed, temp=temp, auto_mode=auto_mode, message=message)

# ----- Start Background Thread & App -----
if __name__ == "__main__":
    thread = threading.Thread(target=auto_fan_control, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=5001)
