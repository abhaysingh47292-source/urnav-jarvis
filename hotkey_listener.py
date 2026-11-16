import ctypes
from ctypes import wintypes
from PySide6.QtCore import QThread, Signal

class GlobalHotkeyListener(QThread):
    hotkey_triggered = Signal()

    def __init__(self, mod_key=0x0001, vk_key=0x20): # Default Alt + Space
        super().__init__()
        self.mod_key = mod_key
        self.vk_key = vk_key
        self.hotkey_id = 9001
        self.running = True

    def run(self):
        user32 = ctypes.windll.user32
        # Register Hotkey on this thread's message queue
        success = user32.RegisterHotKey(None, self.hotkey_id, self.mod_key, self.vk_key)
        if not success:
            print(f"Warning: Could not register global hotkey (ID: {self.hotkey_id}).")
            return

        msg = wintypes.MSG()
        while self.running:
            # Wait for message in thread queue
            if user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312: # WM_HOTKEY
                    if msg.wParam == self.hotkey_id:
                        self.hotkey_triggered.emit()
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

        user32.UnregisterHotKey(None, self.hotkey_id)

    def stop(self):
        self.running = False
        user32 = ctypes.windll.user32
        user32.PostQuitMessage(0)
