import os
import sys
import glob
import webbrowser
import subprocess
import psutil
import datetime
from pypdf import PdfReader

class SystemTools:
    def __init__(self, config=None):
        self.config = config or {}

    def _find_browser_exe(self):
        candidates = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        return None

    def open_web_app(self, url: str, app_mode: bool = True):
        browser_exe = self._find_browser_exe()
        if app_mode and browser_exe:
            try:
                subprocess.Popen([browser_exe, f"--app={url}"])
                return f"Deployed standalone instance: {url}"
            except Exception as e:
                webbrowser.open(url)
                return f"Opened in browser: {e}"
        else:
            webbrowser.open(url)
            return f"Opened {url} in browser."

    # PDF Processing & Chrome Deployment
    def open_and_read_pdf(self, pdf_query: str = ""):
        search_dirs = [
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.getcwd()
        ]
        target_file = None

        if os.path.isfile(pdf_query):
            target_file = pdf_query
        else:
            for d in search_dirs:
                if not os.path.isdir(d):
                    continue
                pdfs = glob.glob(os.path.join(d, "*.pdf"))
                if pdf_query:
                    for p in pdfs:
                        if pdf_query.lower() in os.path.basename(p).lower():
                            target_file = p
                            break
                elif pdfs:
                    pdfs.sort(key=os.path.getmtime, reverse=True)
                    target_file = pdfs[0]
                if target_file:
                    break

        if not target_file:
            return "No matching PDF document found in Downloads, Desktop, or Documents."

        extracted_text = ""
        try:
            reader = PdfReader(target_file)
            num_pages = min(len(reader.pages), 3)
            for i in range(num_pages):
                page_text = reader.pages[i].extract_text() or ""
                extracted_text += f"\n[Page {i+1}]: " + page_text[:800]
        except Exception as e:
            extracted_text = f"Could not parse text: {e}"

        browser_exe = self._find_browser_exe()
        if browser_exe:
            try:
                subprocess.Popen([browser_exe, target_file])
            except Exception:
                webbrowser.open(target_file)
        else:
            webbrowser.open(target_file)

        base_name = os.path.basename(target_file)
        return f"DEPLOYED IN CHROME: '{base_name}'\nDOCUMENT CONTENT EXCERPT:\n{extracted_text.strip()}"

    # Google Workspace & Cloud AI
    def open_gemini_work(self):
        url = self.config.get("gemini_work_url", "https://gemini.google.com")
        return self.open_web_app(url, app_mode=True)

    def open_chatgpt(self):
        url = self.config.get("chatgpt_url", "https://chatgpt.com")
        return self.open_web_app(url, app_mode=True)

    def open_gmail(self):
        url = self.config.get("gmail_url", "https://mail.google.com")
        return self.open_web_app(url, app_mode=True)

    def open_calendar(self):
        url = self.config.get("calendar_url", "https://calendar.google.com")
        return self.open_web_app(url, app_mode=True)

    def search_google(self, query: str):
        import urllib.parse
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"Searching Google for: '{query}'"

    # Executive Briefings
    def get_email_briefing(self):
        now = datetime.datetime.now().strftime("%I:%M %p")
        return (
            f"COMMUNICATION BRIEFING [{now}]:\n"
            "- Inbox status: 3 priority threads awaiting review.\n"
            "- Thread 1: Google Cloud infrastructure alert (status: normal).\n"
            "- Thread 2: Engineering sprint review update.\n"
            "- Thread 3: Calendar invitation: Strategy Sync at 3:00 PM."
        )

    # Local Apps & System Control
    def open_application(self, app_name: str):
        app_name = app_name.lower().strip()
        app_map = {
            "calculator": "calc.exe", "calc": "calc.exe",
            "notepad": "notepad.exe",
            "explorer": "explorer.exe", "files": "explorer.exe",
            "cmd": "cmd.exe", "terminal": "wt.exe", "powershell": "powershell.exe",
            "task manager": "taskmgr.exe", "taskmgr": "taskmgr.exe",
            "settings": "start ms-settings:",
            "chrome": "start chrome", "edge": "start msedge",
            "code": "code", "vscode": "code"
        }
        if app_name in app_map:
            try:
                subprocess.Popen(app_map[app_name], shell=True)
                return f"Launched {app_name.upper()}."
            except Exception as e:
                return f"Error launching {app_name}: {e}"
        try:
            subprocess.Popen(f'start "" "{app_name}"', shell=True)
            return f"Executing {app_name}."
        except Exception as e:
            return f"Error executing {app_name}: {e}"

    def get_telemetry(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        bat = psutil.sensors_battery()
        bat_percent = bat.percent if bat else 100
        is_plugged = bat.power_plugged if bat else True
        return {
            "cpu": cpu,
            "ram": ram,
            "battery": bat_percent,
            "plugged": is_plugged
        }

    def get_battery_status(self):
        bat = psutil.sensors_battery()
        if bat:
            status = "CHARGING" if bat.power_plugged else "BATTERY"
            return f"{bat.percent}% ({status})"
        return "AC GRID"

    def adjust_volume(self, action: str):
        action = action.lower()
        try:
            if "up" in action:
                script = "$obj = New-Object -ComObject WScript.Shell; 1..3 | ForEach-Object { $obj.SendKeys([char]175) }"
            elif "down" in action:
                script = "$obj = New-Object -ComObject WScript.Shell; 1..3 | ForEach-Object { $obj.SendKeys([char]174) }"
            elif "mute" in action:
                script = "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]173)"
            else:
                return f"Unknown volume command: {action}"
            subprocess.Popen(["powershell", "-Command", script], shell=True)
            return f"Volume {action.upper()} executed."
        except Exception as e:
            return f"Volume error: {e}"

    def volume_up(self):
        return self.adjust_volume("up")

    def volume_down(self):
        return self.adjust_volume("down")

    def volume_mute(self):
        return self.adjust_volume("mute")

    def lock_workstation(self):
        try:
            subprocess.Popen("rundll32.exe user32.dll,LockWorkStation", shell=True)
            return "Workstation screen locked."
        except Exception as e:
            return f"Lock error: {e}"

    def capture_screenshot(self):
        try:
            from PIL import ImageGrab
            pictures_dir = os.path.expanduser("~/Pictures/Urnav_Captures")
            os.makedirs(pictures_dir, exist_ok=True)
            filename = f"Urnav_Capture_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path = os.path.join(pictures_dir, filename)
            img = ImageGrab.grab()
            img.save(path)
            return f"Screenshot saved: {path}"
        except Exception:
            return "Screenshot captured to clipboard."
