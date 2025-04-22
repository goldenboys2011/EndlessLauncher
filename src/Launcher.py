import os
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import requests
import json
import subprocess
import platform
from PIL import Image, ImageTk
import threading

LAUNCHER_DIR = "launcherData"
LOGIN_FILE = os.path.join(LAUNCHER_DIR, "login.dat")
FILE_DOWNLOADS = {
    "./client.jar":                   "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/client.jar",
    "launcherData/bg.png":          "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/launcherData/bg.png",
    "launcherData/logo.png":        "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/launcherData/bg.png",
    "libraries/lwjgl_util.jar":     "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/libraries/lwjgl_util.jar",
    "libraries/lwjgl.jar":          "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/libraries/lwjgl.jar",
    "libraries/jinput.jar":         "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/libraries/jinput.jar",
    "libraries/json-20210307.jar":  "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/libraries/json-20210307.jar",
    "natives/OpenAL64.dll":         "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/OpenAL64.dll",
    "natives/OpenAL32.dll":         "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/OpenAL32.dll",
    "natives/lwjgl64.dll":          "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/lwjgl64.dll",
    "natives/lwjgl.dll":            "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/lwjgl.dll",
    "natives/libopenal64.so":       "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/libopenal64.so",
    "natives/libopenal.so":         "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/libopenal.so",
    "natives/liblwjgl64.so":         "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/liblwjgl64.so",
    "natives/liblwjgl.so":           "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/liblwjgl.so",
    "natives/libjinput-linux64.so": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/libjinput-linux64.so",
    "natives/libjinput-linux.so":   "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/libjinput-linux.so",
    "natives/jinput-raw_64.dll":    "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/jinput-raw_64.dll",
    "natives/jinput-raw.dll":       "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/jinput-raw.dll",
    "natives/jinput-dx8_64.dll":    "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/jinput-dx8_64.dll",
    "natives/jinput-dx8.dll":       "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/jinput-dx8.dll"
}


class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Endless Beta Launcher")
        self.ram_mb = "1024"
        self.login_method = tk.StringVar(value="OSMC")
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        
        
    
    def build_ui(self):
        # Load bg tile image
        self.bg_tile = Image.open("launcherData/bg.png").resize((32, 32))
        self.bg_tile_tk = ImageTk.PhotoImage(self.bg_tile)

        # Optional: Load logo
        # self.logo = Image.open("launcherData/logo.png").resize((200, 100), Image.ANTIALIAS)
        # self.logo_tk = ImageTk.PhotoImage(self.logo)

        canvas = tk.Canvas(self.root, width=300, height=400)
        canvas.pack(fill="both", expand=True)

        for x in range(0, 800, self.bg_tile.width):
            for y in range(0, 600, self.bg_tile.height):
                canvas.create_image(x, y, image=self.bg_tile_tk, anchor="nw")

        frame = tk.Frame(canvas, bg="#ffffff", bd=0)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="Login Method:", bg="white").pack()
        login_menu = ttk.Combobox(frame, textvariable=self.login_method, values=["OSMC", "Microsoft"], state="readonly")
        login_menu.pack()

        tk.Label(frame, text="Username:", bg="white").pack()
        self.username_entry = tk.Entry(frame, textvariable=self.username)
        self.username_entry.pack()

        tk.Label(frame, text="Password:", bg="white").pack()
        self.password_entry = tk.Entry(frame, textvariable=self.password, show="*")
        self.password_entry.pack()

        launch_button = tk.Button(frame, text="Launch", command=self.launch)
        launch_button.pack(pady=(10, 5))

        settings_button = tk.Button(frame, text="Settings", command=self.open_settings)
        settings_button.pack()

        creds = self.load_credentials()
        if creds:
            self.login_method.set(creds[0])
            self.username_entry.insert(0, creds[1])
            self.password_entry.insert(0, creds[2])

    def open_settings(self):
        new_ram = simpledialog.askstring("Settings", "Enter RAM in MB:", initialvalue=self.ram_mb)
        if new_ram:
            self.ram_mb = new_ram.strip()

    def show_alert(self, message):
        messagebox.showinfo("Info", message)

    def save_credentials(self):
        os.makedirs(LAUNCHER_DIR, exist_ok=True)
        with open(LOGIN_FILE, "w") as f:
            f.write(f"{self.login_method.get()}\n{self.username.get()}\n{self.password.get()}")

    def load_credentials(self):
        if not os.path.exists(LOGIN_FILE):
            return
        with open(LOGIN_FILE) as f:
            lines = f.read().splitlines()
            if len(lines) == 3:
                self.login_method.set(lines[0])
                self.username.set(lines[1])
                self.password.set(lines[2])

    def authenticate_with_osmc(self, username, password):
        url = "https://os-mc.net/api/v1/authenticate"
        data = {"username": username, "password": password}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data, headers=headers)
        return response.json()

    def launch(self):
        method = self.login_method.get()
        username = self.username.get()
        password = self.password.get()

        if method == "OSMC":
            try:
                response = self.authenticate_with_osmc(username, password)
                if response.get("success"):
                    profile = response["selectedProfile"]
                    player_name = profile["name"]
                    uuid = profile["id"]
                    self.save_credentials()
                    self.launch_game(player_name, uuid, "osmc")
                else:
                    self.show_alert("Authentication failed.")
            except Exception as e:
                print(e)
                self.show_alert("Login failed.")
        else:
            self.show_alert("Microsoft login not implemented.")

    def launch_game(self, username, uuid, launch_type):
        print(f"Launching Minecraft for: Username: {username}, UUID: {uuid}, RAM: {self.ram_mb}MB, Type: {launch_type}")
        java_exec = "javaw" if platform.system() == "Windows" else "java"

        classpath = os.pathsep.join([
            "client.jar",
            "libraries/json.jar",
            "libraries/lwjgl.jar",
            "libraries/lwjgl_util.jar"
        ])

        params = [
            java_exec,
            f"-Xmx{self.ram_mb}M",
            "-Djava.library.path=natives",
            "-classpath", classpath,
            "net.minecraft.client.Minecraft",
            username,
            uuid,
            launch_type
        ]

        try:
            root.withdraw()  # Hide the main window for now
            
            threading.Thread(target=subprocess.run(params, check=True)).start()
            
            root.deiconify()
            print("Game exited successfully.")
        except subprocess.CalledProcessError as e:
            print("Game process failed:", e)
            self.show_alert("Game launch failed.")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window for now
    download_window = tk.Toplevel()
    download_window.title("Preparing Launcher")
    download_window.geometry("300x100")
    download_window.resizable(False, False)
    label = tk.Label(download_window, text="Downloading required files...")
    label.pack(pady=10)
    progress = ttk.Progressbar(download_window, mode="determinate", maximum=len(FILE_DOWNLOADS))
    progress.pack(pady=10, padx=20, fill="x")

    def download_and_continue():
        total = len(FILE_DOWNLOADS)
        for i, (local_path, url) in enumerate(FILE_DOWNLOADS.items()):
            try:
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                if not os.path.exists(local_path):
                    response = requests.get(url)
                    with open(local_path, "wb") as f:
                        f.write(response.content)
                progress["value"] = i + 1
                label.config(text=f"Downloading {os.path.basename(local_path)}")
                download_window.update_idletasks()
            except Exception as e:
                print(f"Error downloading {local_path}: {e}")
        
        # Once done, close the popup and show main window
        download_window.destroy()
        root.deiconify()
        app = LauncherApp(root)
        app.build_ui()


    threading.Thread(target=download_and_continue).start()
    root.mainloop()
