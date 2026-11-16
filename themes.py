import winreg

class ThemeManager:
    DEFAULT_ORANGE = "#FF6B00"
    DEFAULT_WHITE = "#FFFFFF"

    @staticmethod
    def get_windows_accent_color() -> str:
        """Query native Windows accent color from registry."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM")
            val, _ = winreg.QueryValueEx(key, "ColorizationColor")
            hex_color = f"#{val & 0xFFFFFF:06x}"
            return hex_color
        except Exception:
            return ThemeManager.DEFAULT_ORANGE

    @staticmethod
    def get_style(accent_color: str = None) -> str:
        accent = accent_color or ThemeManager.DEFAULT_ORANGE
        return f"""
        /* 
           URNAV EXECUTIVE DYNAMIC ISLAND HUD
           Aesthetic: Solar Orange ({accent}) & Pure White (#FFFFFF)
           Container: Deep Matte Obsidian (#090B10) with Glass Glow
           Typography: Segoe UI Variable Display, Segoe UI, Inter, sans-serif
           Zero Emojis. Pure Precision & Distinction.
        */

        #container {{
            background-color: #090B10;
            border: 1px solid rgba(255, 107, 0, 0.45);
            border-top: none;
            border-bottom-left-radius: 22px;
            border-bottom-right-radius: 22px;
        }}

        #statusDot {{
            color: {accent};
            font-size: 13px;
            font-weight: 900;
        }}

        #islandTitle {{
            color: #FFFFFF;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', -apple-system, sans-serif;
            font-size: 11px;
            font-weight: 900;
            letter-spacing: 2.2px;
        }}

        #timeLabel {{
            color: #E2E8F0;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', sans-serif;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}

        #telemetryBadge {{
            color: #FFFFFF;
            background-color: #131622;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            padding: 2px 9px;
            font-size: 10px;
            font-weight: 800;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', monospace;
            letter-spacing: 0.5px;
        }}

        /* Buttons in Top Bar */
        .islandBtn {{
            background-color: #131622;
            color: #FFFFFF;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 11px;
            padding: 3px 10px;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1px;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
        }}
        .islandBtn:hover {{
            background-color: {accent};
            color: #000000;
            border: 1px solid {accent};
        }}

        /* Primary Action Buttons */
        .actionBtn {{
            background-color: {accent};
            color: #000000;
            border: 1px solid {accent};
            border-radius: 12px;
            padding: 5px 14px;
            font-size: 10px;
            font-weight: 900;
            letter-spacing: 1px;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
        }}
        .actionBtn:hover {{
            background-color: #FFA040;
            border: 1px solid #FFA040;
        }}

        /* Secondary Action Buttons (GitHub / Sync) */
        .gitBtn {{
            background-color: #24292E;
            color: #FFFFFF;
            border: 1px solid rgba(255, 107, 0, 0.5);
            border-radius: 12px;
            padding: 5px 14px;
            font-size: 10px;
            font-weight: 900;
            letter-spacing: 1px;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
        }}
        .gitBtn:hover {{
            background-color: {accent};
            color: #000000;
            border: 1px solid {accent};
        }}

        /* Tabs Navigation */
        .tabBtn {{
            background-color: transparent;
            color: #94A3B8;
            border: none;
            border-bottom: 2px solid transparent;
            border-radius: 0px;
            padding: 6px 14px;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.2px;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
        }}
        .tabBtn:hover {{
            color: #FFFFFF;
        }}
        .tabBtn[active="true"] {{
            color: #FFFFFF;
            border-bottom: 2px solid {accent};
        }}

        /* Card Panels */
        .hudCard {{
            background-color: #10131D;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 12px;
        }}

        .cardHeader {{
            color: {accent};
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1.2px;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
        }}

        /* File Dropzone Area */
        #dropZone {{
            background-color: rgba(255, 107, 0, 0.04);
            border: 2px dashed rgba(255, 107, 0, 0.45);
            border-radius: 14px;
            padding: 12px;
        }}
        #dropZone[dragActive="true"] {{
            background-color: rgba(255, 107, 0, 0.15);
            border: 2px dashed {accent};
        }}

        /* Inputs */
        #commandInput, .settingInput {{
            background-color: #141824;
            color: #FFFFFF;
            border: 1px solid rgba(255, 107, 0, 0.4);
            border-radius: 12px;
            padding: 8px 14px;
            font-size: 12px;
            font-weight: 600;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
        }}
        #commandInput:focus, .settingInput:focus {{
            border: 1px solid {accent};
            background-color: #181E30;
        }}

        /* Log / Dialogue Display */
        #logArea {{
            background-color: #0C0E15;
            color: #F8FAFC;
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 12px;
            padding: 10px;
            font-size: 11px;
            line-height: 1.5;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;
        }}

        /* Progress Bars */
        QProgressBar {{
            background-color: #161A26;
            border: none;
            border-radius: 4px;
            height: 6px;
            text-align: right;
            color: transparent;
        }}
        QProgressBar::chunk {{
            background-color: {accent};
            border-radius: 4px;
        }}

        /* Tool Launch Buttons */
        .launcherBtn {{
            background-color: #131622;
            color: #F1F5F9;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 7px 10px;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.8px;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
        }}
        .launcherBtn:hover {{
            background-color: #1E2336;
            border: 1px solid {accent};
            color: #FFFFFF;
        }}

        /* Scrollbars */
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 5px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(255, 255, 255, 0.2);
            border-radius: 2px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {accent};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        """
