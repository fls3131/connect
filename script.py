import tkinter as tk
from tkinter import messagebox, filedialog, Menu, ttk
import subprocess
import os
import threading
import speedtest
import time
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem, Icon
import base64

class OpenVPNClient:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenVPN Client 0.02")
        self.root.geometry("400x300")
        self.process = None
        self.is_vpn_connected = False

        # Variáveis para o estado da internet
        self.internet_status = False

        # Check for administrative privileges on Windows
        if not self.check_admin():
            messagebox.showerror("Permission Denied", "This application requires administrative privileges. Please run as an administrator.")
            self.root.quit()
            return

        # Load the last .ovpn file path
        self.ovpn_file_path = self.load_last_config()

        # Create menu
        self.create_menu()

        # GUI Elements
        self.label = tk.Label(root, text="Select OpenVPN Configuration File:")
        self.label.pack(pady=10)

        self.file_button = tk.Button(root, text="Browse", command=self.browse_file)
        self.file_button.pack(pady=10)

        self.connect_button = tk.Button(root, text="Connect", command=self.connect_vpn, state=tk.DISABLED)
        self.connect_button.pack(pady=10)

        self.disconnect_button = tk.Button(root, text="Disconnect", command=self.disconnect_vpn, state=tk.DISABLED)
        self.disconnect_button.pack(pady=10)

        self.speedtest_button = tk.Button(root, text="Speed Test", command=self.open_speed_test_window)
        self.speedtest_button.pack(pady=10)

        self.exit_button = tk.Button(root, text="Exit", command=self.root.quit)
        self.exit_button.pack(pady=10)

        # Pre-fill the file path if available
        if self.ovpn_file_path:
            messagebox.showinfo("Previous Configuration Loaded", f"Previous configuration loaded: {self.ovpn_file_path}")
            self.connect_button.config(state=tk.NORMAL)

        # Start monitoring in a separate thread
        threading.Thread(target=self.monitor_status, daemon=True).start()

        # Initialize system tray icon
        self.icon = Icon("OpenVPN Client", self.create_image(color='blue'))
        self.icon.menu = self.create_systray_menu()
        threading.Thread(target=self.icon.run, daemon=True).start()

    def create_menu(self):
        menu_bar = Menu(self.root)

        programs_menu = Menu(menu_bar, tearoff=0)
        programs_menu.add_command(label="Speed Test", command=self.open_speed_test_window)
        programs_menu.add_command(label="Run net.py", command=self.run_net_script)
        programs_menu.add_separator()
        programs_menu.add_command(label="About", command=self.show_about_window)
        menu_bar.add_cascade(label="Programs", menu=programs_menu)

        self.root.config(menu=menu_bar)

    def check_admin(self):
        """Check for administrative privileges on Windows."""
        # This is a simplified way to check for admin privileges by attempting to create a temporary folder in a system location
        try:
            subprocess.run(["mkdir", "C:\\Windows\\Temp\\test_admin"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["rmdir", "C:\\Windows\\Temp\\test_admin"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except Exception:
            return False

    def load_last_config(self):
        try:
            with open("last_config.txt", "r") as f:
                # Decode the base64 encoded path
                encoded_path = f.readline().strip()
                decoded_path = base64.b64decode(encoded_path).decode('utf-8')
                return decoded_path if os.path.exists(decoded_path) else None
        except (FileNotFoundError, ValueError):
            return None

    def save_last_config(self):
        if self.ovpn_file_path:
            encoded_path = base64.b64encode(self.ovpn_file_path.encode('utf-8')).decode('utf-8')
            with open("last_config.txt", "w") as f:
                f.write(encoded_path)

    def browse_file(self):
        self.ovpn_file_path = filedialog.askopenfilename(
            title="Select OpenVPN Configuration (.ovpn)",
            filetypes=[("OpenVPN Files", "*.ovpn")]
        )
        if self.ovpn_file_path:
            self.connect_button.config(state=tk.NORMAL)
            messagebox.showinfo("Selected File", f"Selected: {self.ovpn_file_path}")
            self.save_last_config()

    def connect_vpn(self):
        if not self.ovpn_file_path:
            messagebox.showwarning("No File", "Please select a .ovpn file.")
            return

        self.process = subprocess.Popen(
            ["openvpn", "--config", self.ovpn_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True
        )

        self.is_vpn_connected = True
        self.connect_button.config(state=tk.DISABLED)
        self.disconnect_button.config(state=tk.NORMAL)
        self.exit_button.config(state=tk.DISABLED)  # Disable exit button

        threading.Thread(target=self.read_output).start()

    def read_output(self):
        while True:
            output = self.process.stdout.readline()
            if output == '' and self.process.poll() is not None:
                break
            if output:
                print(output.strip())

        self.disconnect_vpn()

    def disconnect_vpn(self):
        if self.process:
            self.process.terminate()
            self.process = None
            
        self.is_vpn_connected = False
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.exit_button.config(state=tk.NORMAL)  # Enable exit button
        messagebox.showinfo("Disconnected", "You have been disconnected from the VPN.")

    def open_speed_test_window(self):
        speed_test_window = tk.Toplevel(self.root)
        speed_test_app = SpeedTestApp(speed_test_window)

    def run_net_script(self):
        try:
            subprocess.Popen(["python", "net.py"], shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not execute the script net.py.\n{str(e)}")

    def show_about_window(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.geometry("400x200")

        about_text = (
            "OpenVPN Client 0.3\n"
            "Developed by:\n"
            "Fabio Lipel Schmit\n"
            "Hostmaster@bithostel.com.br\n"
            "Bithostel TI - https://bithostel.com.br"
        )

        label = tk.Label(about_window, text=about_text, justify=tk.LEFT, padx=10, pady=10)
        label.pack()

        close_button = tk.Button(about_window, text="Close", command=about_window.destroy)
        close_button.pack(pady=10)

    def create_image(self, color='blue'):
        # Create a filled square of the specified color
        size = (16, 16)
        image = Image.new("RGB", size, "white")
        draw = ImageDraw.Draw(image)

        # Draw a rectangle of the specified color
        draw.rectangle([0, 0, size[0], size[1]], fill=color)

        return image

    def create_systray_menu(self):
        return (MenuItem('Exit', self.quit_application),)

    def quit_application(self, icon):
        self.icon.stop()
        self.root.destroy()

    def monitor_status(self):
        while True:
            # Check internet status
            self.check_internet()
            # Update the tray icon based on status
            self.update_icon()
            time.sleep(5)  # Check every 5 seconds

    def check_internet(self):
        try:
            # Ping Google
            subprocess.run(["ping", "-n", "1", "google.com"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.internet_status = True
        except Exception:
            self.internet_status = False

    def update_icon(self):
        # Update the tray icon based on VPN connection status
        if self.is_vpn_connected:
            self.icon.icon = self.create_image(color='green')  # Green when connected
        else:
            self.icon.icon = self.create_image(color='blue')  # Blue when disconnected


# Speed test application
class SpeedTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Internet Speed Test")

        # Create a Frame
        self.frame = tk.Frame(self.root)
        self.frame.pack(pady=20)

        # Create a label for instructions
        self.label = tk.Label(self.frame, text="Click the button to test internet speed.")
        self.label.pack(pady=10)

        # Create a button to start speed test
        self.start_button = tk.Button(self.frame, text="Start Speed Test", command=self.start_test)
        self.start_button.pack(pady=10)

        # Create a progress bar
        self.progress = ttk.Progressbar(self.frame, orient="horizontal", mode="determinate", length=300)
        self.progress.pack(pady=10)

        # Create label for results
        self.result_label = tk.Label(self.frame, text="")
        self.result_label.pack(pady=10)

    def start_test(self):
        # Disable start button to prevent multiple clicks
        self.start_button.config(state=tk.DISABLED)

        # Start the progress bar
        self.progress.config(mode="indeterminate")
        self.progress.start()

        # Run speed test in a separate thread
        thread = threading.Thread(target=self.run_speed_test)
        thread.start()

    def run_speed_test(self):
        # Create a Speedtest object
        st = speedtest.Speedtest()

        # Simulate download progress
        for _ in range(10):  # Simulate 10 steps (10% for each iteration)
            time.sleep(0.5)  # Simulate time for each part of the download
            self.root.after(0, self.progress.step, 10)  # Update progress bar

        # Perform actual download test
        download_speed = st.download() / (10**6)  # Convert to Mbps

        # Simulate upload progress
        for _ in range(10):  # Simulate 10 steps (10% for each iteration)
            time.sleep(0.5)  # Simulate time for each part of the upload
            self.root.after(0, self.progress.step, 10)  # Update progress bar

        # Perform actual upload test
        upload_speed = st.upload() / (10**6)  # Convert to Mbps

        # Stop the progress bar
        self.progress.stop()

        # Update result label and re-enable the button
        self.result_label.config(text=f"Download Speed: {download_speed:.2f} Mbps\n"
                                       f"Upload Speed: {upload_speed:.2f} Mbps")
        self.start_button.config(state=tk.NORMAL)


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = OpenVPNClient(root)
    root.mainloop()
