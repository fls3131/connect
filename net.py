import requests
import threading
import time
import pystray
from PIL import Image, ImageDraw
from pystray import MenuItem, Icon
import subprocess
import platform

status = "Checking..."  # Initial status
public_ip = ""  # Variable to hold the public IP address
ping_time = "N/A"  # Variable to hold the ping time

def ping_host(host):
    """Ping the specified host and return the ping time in milliseconds."""
    try:
        # Determine the command based on the operating system
        if platform.system().lower() == "windows":
            # Windows: use 'ping -n 1'
            command = ["ping", "-n", "1", host]
        else:
            # Linux/macOS: use 'ping -c 1'
            command = ["ping", "-c", "1", host]

        # Execute the ping command
        output = subprocess.run(command, capture_output=True, text=True)
        
        # Extract the round-trip time from the output
        if platform.system().lower() == "windows":
            # Windows output parsing
            for line in output.stdout.splitlines():
                if "time=" in line:
                    return line.split("time=")[1].split(" ")[0] + " ms"
        else:
            # Linux/macOS output parsing
            for line in output.stdout.splitlines():
                if "time=" in line:
                    return line.split("time=")[1].split(" ")[0]
                    
    except Exception as e:
        print(f"Ping failed: {e}")
        return "N/A"
    return "N/A"  # If nothing was returned

def check_internet():
    global status, public_ip, ping_time
    while True:
        try:
            # Test internet connection
            requests.get("http://www.google.com", timeout=5)
            status = "Online"

            # Fetch the public IP address
            public_ip = requests.get("https://api.ipify.org").text  # Using ipify to get public IP
            
            # Measure the ping time
            ping_time = ping_host("www.google.com")  # Ping Google and get the response time

        except requests.ConnectionError:
            status = "Offline"
            public_ip = ""
            ping_time = "N/A"

        # Update the icon every 5 seconds
        time.sleep(5)

def create_image(icon_status):
    # Create an image for the icon
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    if icon_status == "Online":
        draw.rectangle([0, 0, width, height], fill=(0, 255, 0))  # Green for Online
    else:
        draw.rectangle([0, 0, width, height], fill=(255, 0, 0))  # Red for Offline
    
    return image

def update_icon(icon):
    icon.icon = create_image(status)
    icon.title = f"Status: {status}\nPublic IP: {public_ip if public_ip else 'N/A'}\nPing: {ping_time}"  # Update icon title with status, IP, and ping

def exit_program(icon, item):
    icon.stop()

# Create the menu for the system tray
menu = (MenuItem("Exit", exit_program),)

# Create the system tray icon
icon = Icon("Internet Status", create_image(status), "Internet Status", menu)

# Start the internet checking in a separate thread
thread = threading.Thread(target=check_internet, daemon=True)
thread.start()

# Set the icon update in a loop
def run_icon_updater():
    while True:
        update_icon(icon)
        time.sleep(1)  # Update the icon every second

# Start the icon updater in a separate thread
updater_thread = threading.Thread(target=run_icon_updater, daemon=True)
updater_thread.start()

# Run the system tray icon
icon.run()
