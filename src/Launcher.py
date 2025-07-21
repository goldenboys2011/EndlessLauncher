import platform
import sys
import os
import json
import urllib.parse
import subprocess
import requests
from datetime import datetime, timedelta
import threading
import patoolib
from PyQt6.QtCore import QUrl, pyqtSignal, QObject, Qt, QThread, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QMessageBox, QLabel, QProgressBar
)
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView

CLIENT_ID = "67e473a7-2caa-46eb-84b6-dbd5f65fcc72"
REDIRECT_URI = "http://localhost"
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPE = ["XboxLive.signin"]
AUTH_URL = (
    f"{AUTHORITY}/oauth2/v2.0/authorize?response_type=code&client_id={CLIENT_ID}&"
    f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&response_mode=query&scope={' '.join(SCOPE)}&prompt=select_account"
)
TOKEN_URL = f"{AUTHORITY}/oauth2/v2.0/token"
ACCOUNTS_FILE = "accounts.json"
MINECRAFT_JAR_PATH = "./minecraft/client.jar"

# Files to download with URLs

FILE_DOWNLOADS = {
    "minecraft/client.jar": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/client.jar",
    "launcherData/launcher_ui.html": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/launcherData/launcher_ui.html",
    "launcherData/background.png": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/launcherData/background.png",
    "launcherData/logo.png": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/launcherData/logo.png",
    "minecraft/libraries/lwjgl_util.jar": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/libraries/lwjgl_util.jar",
    "minecraft/libraries/lwjgl.jar": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/libraries/lwjgl.jar",
    "minecraft/libraries/jinput.jar": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/libraries/jinput.jar",
    "minecraft/libraries/person/json-20210307.jar": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/libraries/json-20210307.jar",
    "minecraft/natives/OpenAL64.dll": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/OpenAL64.dll",
    "minecraft/natives/OpenAL32.dll": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/OpenAL32.dll",
    "minecraft/natives/lwjgl64.dll": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/lwjgl64.dll",
    "minecraft/natives/lwjgl.dll": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/lwjgl.dll",
    "minecraft/natives/libopenal64.so": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/libopenal64.so",
    "minecraft/natives/libopenal.so": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/libopenal.so",
    "minecraft/natives/liblwjgl64.so": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/liblwjgl64.so",
    "minecraft/natives/liblwjgl.so": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/liblwjgl.so",
    "minecraft/natives/libjinput-linux64.so": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/libjinput-linux64.so",
    "minecraft/natives/libjinput-linux.so": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/libjinput-linux.so",
    "minecraft/natives/jinput-raw_64.dll": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/jinput-raw_64.dll",
    "minecraft/natives/jinput-raw.dll": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/jinput-raw.dll",
    "minecraft/natives/jinput-dx8_64.dll": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/jinput-dx8_64.dll",
    "minecraft/natives/jinput-dx8.dll": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/natives/jinput-dx8.dll"
}

java_downloads = {
    "windows": "https://github.com/goldenboys2011/EndlessLauncher/raw/refs/heads/latest/java/windows.rar"
}


def get_platform_key(self):
    system = platform.system().lower()
    arch = platform.machine()

    if system in java_downloads:
        if not arch.endswith("64"):
            QMessageBox.critical(self, "Unsupported Architecture", "It Looks Like The Architecture You Are Using Is Unsupported By The Launcher. If you want support please visit `github.com/goldenboys2011/EndlessLauncher`")
            sys.exit("Unsupported Architecture.")
        return system
    else:
        QMessageBox.critical(self, "Unsupported OS", "The `Operating System` you are using is unsuported by this launcher")
        sys.exit("Unsupported OS.")

class DownloaderThread(QThread):
    progress_updated = pyqtSignal(int)
    label_updated = pyqtSignal(str)
    finished = pyqtSignal()

    def run(self):
        total = len(FILE_DOWNLOADS)
        for i, (path, url) in enumerate(FILE_DOWNLOADS.items(), start=1):
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                if os.path.exists(path):
                    self.progress_updated.emit(i)
                    self.label_updated.emit(f"Already exists: {os.path.basename(path)}")
                    continue

                r = requests.get(url, stream=True)
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                self.progress_updated.emit(i)
                self.label_updated.emit(f"Downloaded {os.path.basename(path)}")
            except Exception as e:
                self.label_updated.emit(f"Error downloading {os.path.basename(path)}: {e}")
    
        
        self.finished.emit()

class JavaSetupThread(QThread):
    label_updated = pyqtSignal(str)
    finished = pyqtSignal()

    def run(self):
        platforma = get_platform_key(self)
        extract_path = os.path.abspath("java")

        if os.path.isdir(extract_path):
            self.label_updated.emit("Java already extracted.")
        else:
            try:
                url = java_downloads[platforma]
                self.label_updated.emit("Downloading Java...")
                r = requests.get(url, stream=True)
                r.raise_for_status()
                with open("java.rar", "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                self.label_updated.emit("Extracting Java...")
                os.makedirs(extract_path, exist_ok=True)
                patoolib.extract_archive(os.path.abspath("java.rar"), outdir=extract_path)
                os.remove(os.path.abspath("java.rar"))

                self.label_updated.emit("Java setup complete.")
            except Exception as e:
                self.label_updated.emit(f"Java setup failed: {e}")
        
        self.finished.emit()


class Downloader(QWidget):
    def __init__(self, on_complete_callback):
        super().__init__()
        self.setWindowTitle("Preparing Launcher")
        self.resize(400, 120)

        layout = QVBoxLayout(self)
        self.label = QLabel("Starting downloads...")
        self.progress = QProgressBar()
        self.progress.setMaximum(len(FILE_DOWNLOADS))

        layout.addWidget(self.label)
        layout.addWidget(self.progress)

        self.thread = DownloaderThread()
        self.thread.progress_updated.connect(self.progress.setValue)
        self.thread.label_updated.connect(self.label.setText)
        self.thread.finished.connect(self.on_finished)

        self._on_complete = on_complete_callback
        self.thread.start()

    def on_finished(self):
        platforma = get_platform_key(self)

        if os.path.isdir(os.path.abspath("java")):
            print(f"The '{os.path.abspath("java")}' directory exists!")
        else:
            url = java_downloads[platforma]
            r = requests.get(url, stream=True)
            r.raise_for_status()
            with open("java.rar", "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            extract_path = os.path.abspath("java") 
            os.makedirs(extract_path, exist_ok=True)
            patoolib.extract_archive(os.path.abspath("java.rar"), outdir=extract_path)
            os.remove(os.path.abspath("java.rar"))
        self._on_complete()
        self.close()

class Signals(QObject):
    done = pyqtSignal(bool, dict)

class Bridge(QObject):
    def __init__(self, launcher):
        super().__init__()
        self.launcher = launcher

    @pyqtSlot()
    def play(self):
        self.launcher.play_game()

    @pyqtSlot(int)
    def onAccountSelected(self, index):
        self.launcher.on_account_selected(index)

class LoginWindow(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.setWindowTitle("Login")
        self.resize(600, 500)
        self.callback = callback

        self.webview = QWebEngineView(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.webview)

        self.webview.urlChanged.connect(self.on_url_changed)
        self.auth_code = None

        self.signals = Signals()
        self.signals.done.connect(self.on_done)
        self.webview.load(QUrl(AUTH_URL))

    def on_url_changed(self, url):
        url_str = url.toString()
        if url_str.startswith(REDIRECT_URI):
            query = urllib.parse.urlparse(url_str).query
            params = urllib.parse.parse_qs(query)
            if "code" in params:
                self.auth_code = params["code"][0]
                self.exchange_code_for_token()

    def exchange_code_for_token(self):
        data = {
            "client_id": CLIENT_ID,
            "scope": " ".join(SCOPE),
            "code": self.auth_code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        r = requests.post(TOKEN_URL, data=data)
        tokens = r.json()
        access_token = tokens.get("access_token")
        if access_token:
            self.complete_login(access_token)
        else:
            self.signals.done.emit(False, {"error": "Token exchange failed."})

    def complete_login(self, access_token):
        try:
            xbl_token, uhs = self.get_xbox_live_token(access_token)
            xsts_token, uhs = self.get_xsts_token(xbl_token)
            mc_token = self.get_minecraft_access_token(uhs, xsts_token)
            if self.check_minecraft_ownership(mc_token):
                profile = self.get_minecraft_profile(mc_token)
                account = {
                    "uuid": profile["id"],
                    "username": profile["name"],
                    "access_token": mc_token,
                    "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
                }
                self.signals.done.emit(True, account)
            else:
                self.signals.done.emit(False, {"error": "Minecraft not owned."})
        except Exception as e:
            self.signals.done.emit(False, {"error": str(e)})

    def on_done(self, success, data):
        self.callback(success, data)
        self.close()

    def get_xbox_live_token(self, token):
        r = requests.post("https://user.auth.xboxlive.com/user/authenticate", json={
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": f"d={token}"
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT"
        })
        r.raise_for_status()
        d = r.json()
        return d["Token"], d["DisplayClaims"]["xui"][0]["uhs"]

    def get_xsts_token(self, xbl_token):
        r = requests.post("https://xsts.auth.xboxlive.com/xsts/authorize", json={
            "Properties": {
                "SandboxId": "RETAIL",
                "UserTokens": [xbl_token]
            },
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT"
        })
        r.raise_for_status()
        d = r.json()
        return d["Token"], d["DisplayClaims"]["xui"][0]["uhs"]

    def get_minecraft_access_token(self, uhs, xsts_token):
        r = requests.post("https://api.minecraftservices.com/authentication/login_with_xbox", json={
            "identityToken": f"XBL3.0 x={uhs};{xsts_token}"
        })
        r.raise_for_status()
        return r.json()["access_token"]

    def check_minecraft_ownership(self, token):
        r = requests.get("https://api.minecraftservices.com/entitlements/mcstore", headers={
            "Authorization": f"Bearer {token}"
        })
        r.raise_for_status()
        return any("minecraft" in item["name"] for item in r.json().get("items", []))

    def get_minecraft_profile(self, token):
        r = requests.get("https://api.minecraftservices.com/minecraft/profile", headers={
            "Authorization": f"Bearer {token}"
        })
        r.raise_for_status()
        return r.json()

class WebMainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EndlesLauncher")
        self.resize(800, 500)

        self.accounts = self.load_accounts()

        layout = QVBoxLayout(self)
        self.webview = QWebEngineView()
        layout.addWidget(self.webview)

        # Web channel for JS -> Python communication
        self.channel = QWebChannel()
        self.bridge = Bridge(self)
        self.channel.registerObject("pyplay", self.bridge)
        self.webview.page().setWebChannel(self.channel)

        # Load HTML with correct file path
        html_path = os.path.abspath("launcherData/launcher_ui.html")
        if not os.path.exists(html_path):
            QMessageBox.critical(self, "Error", f"Missing UI file: {html_path}")
            sys.exit(1)

        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        self.webview.setHtml(html, QUrl.fromLocalFile(html_path))

        # Wait until page loads before calling JS
        self.webview.page().loadFinished.connect(self.on_page_loaded)

    def on_page_loaded(self):
        js = f"setAccounts({json.dumps(self.accounts)});"
        self.webview.page().runJavaScript(js)

    def load_accounts(self):
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, "r") as f:
                return json.load(f)
        return []

    def save_accounts(self):
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump(self.accounts, f, indent=2)

    def on_account_selected(self, index):
        if index == len(self.accounts) + 1:  # "+ Add Account"
            self.open_login()
        self.last_selected_index = index

    def launch_beta_173(self, username):
        classpath = os.pathsep.join([
            os.path.abspath(MINECRAFT_JAR_PATH),
            os.path.abspath("minecraft/libraries/jinput.jar"),
            os.path.abspath("minecraft/libraries/lwjgl.jar"),
            os.path.abspath("minecraft/libraries/lwjgl_util.jar"),
            os.path.abspath("minecraft/libraries/person/json-20210307.jar"),
        ])

        java_path = os.path.abspath("java/bin/java.exe")
        jre_base = os.path.abspath("java")  # folder containing bin/, lib/, etc.

        params = [
            java_path,
            "-Xmx1024M",
            "-Djava.library.path=" + os.path.abspath("minecraft/natives"),
            "-classpath", classpath,
            "net.minecraft.client.Minecraft",
            username
        ]

        # 🔧 Setup the environment to make Java 7 portable
        env = os.environ.copy()
        env["JAVA_HOME"] = jre_base
        env["PATH"] = os.pathsep.join([
            os.path.join(jre_base, "bin", "server"),
            os.path.join(jre_base, "bin"),
            env.get("PATH", "")
        ])

        print(f"Launching Minecraft Beta 1.7.3 with command:\n{' '.join(params)}")

        def run_game():
            try:
                subprocess.run(params, check=True, env=env)
                print("Game exited successfully.")
            except subprocess.CalledProcessError as e:
                print("Game launch failed:", e)
                QMessageBox.critical(self, "Launch Failed", "Failed to launch Minecraft Beta 1.7.3.")

        self.hide()
        threading.Thread(target=run_game, daemon=True).start()
        self.show()
        
    def open_login(self):
        self.login_win = LoginWindow(self.handle_login_result)
        self.login_win.show()

    def handle_login_result(self, success, data):
        if success:
            # Look for an existing account with the same uuid and username
            replaced = False
            for i, account in enumerate(self.accounts):
                print(account)
                if account["uuid"] == data["uuid"] and account["username"] == data["username"]:
                    self.accounts[i] = data  # Replace the old account with the new data
                    replaced = True
                    break
            
            if not replaced:
                self.accounts.append(data)  # Add new account if not found

            self.save_accounts()
            js = f"setAccounts({json.dumps(self.accounts)});"
            self.webview.page().runJavaScript(js)
        else:
            QMessageBox.critical(self, "Login Failed", str(data.get("error", "Unknown error")))


    def play_game(self):
        index = getattr(self, "last_selected_index", 0)
        if index <= 0 or index >= len(self.accounts) + 1:
            QMessageBox.warning(self, "No account", "Please select a valid account.")
            return

        account = self.accounts[index - 2]  # Adjusted index to match dropdown
        if datetime.fromisoformat(account["expires_at"]) <= datetime.utcnow():
            QMessageBox.warning(self, "Session Expired", "Session expired. Please login again.")
            
            # Remove the expired account from the list
            del self.accounts[index - 2]
            self.save_accounts()
            
            # Update the UI dropdown with the new account list
            js = f"setAccounts({json.dumps(self.accounts)});"
            self.webview.page().runJavaScript(js)
            
            # Open login window so user can add a new account
            self.open_login()
            return


        self.launch_beta_173(account["username"])

def main():
    app = QApplication(sys.argv)

    def show_launcher():
        window = WebMainWindow()
        window.show()

    downloader = Downloader(show_launcher)
    downloader.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
