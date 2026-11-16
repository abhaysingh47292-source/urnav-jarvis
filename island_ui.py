import os
import sys
import datetime
from PySide6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QRect, Signal, QThread, QUrl
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QPlainTextEdit, QFrame,
    QGraphicsDropShadowEffect, QProgressBar, QScrollArea, QGridLayout,
    QStackedWidget, QFileDialog, QDialog, QMessageBox
)
from PySide6.QtGui import QColor, QFont, QCursor, QDragEnterEvent, QDropEvent

from themes import ThemeManager
from gemini_particles import GeminiParticleWave
from microphone_engine import VoiceListenerThread
from file_intelligence import FileIntelligenceEngine

class AIWorker(QThread):
    finished_signal = Signal(str)

    def __init__(self, gemini_client, prompt):
        super().__init__()
        self.gemini_client = gemini_client
        self.prompt = prompt

    def run(self):
        result = self.gemini_client.send_message(self.prompt)
        self.finished_signal.emit(result)

class SummarizeWorker(QThread):
    finished_signal = Signal(dict)

    def __init__(self, file_engine, file_path):
        super().__init__()
        self.file_engine = file_engine
        self.file_path = file_path

    def run(self):
        res = self.file_engine.summarize_document(self.file_path)
        self.finished_signal.emit(res)

class GitHubPushWorker(QThread):
    finished_signal = Signal(dict)

    def __init__(self, file_engine, summary_path, commit_msg=""):
        super().__init__()
        self.file_engine = file_engine
        self.summary_path = summary_path
        self.commit_msg = commit_msg

    def run(self):
        res = self.file_engine.push_summary_to_github(self.summary_path, self.commit_msg)
        self.finished_signal.emit(res)

class DynamicIslandHUD(QWidget):
    def __init__(self, gemini_client, system_tools, voice_engine=None):
        super().__init__()
        self.gemini_client = gemini_client
        self.system_tools = system_tools
        self.voice_engine = voice_engine

        # Subsystems
        self.file_engine = FileIntelligenceEngine(
            local_brain=getattr(gemini_client, "local_brain", None),
            gemini_client=gemini_client
        )

        # State flags
        self.is_expanded = False
        self.is_pinned = False
        self.is_listening = False
        self.is_system_accent = False
        self.current_accent = ThemeManager.DEFAULT_ORANGE
        self.current_target_file = ""
        self.current_summary_path = ""
        self.drag_position = QPoint()

        # Proportions
        self.collapsed_width = 380
        self.collapsed_height = 42
        self.expanded_width = 820
        self.expanded_height = 560

        self.init_window_flags()
        self.init_ui()
        self.center_top()

        if self.voice_engine:
            self.voice_engine.set_callbacks(
                on_start=self.on_speech_started,
                on_finish=self.on_speech_finished
            )

        # Telemetry & Clock timer (1.5s)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_telemetry_and_clock)
        self.clock_timer.start(1500)
        self.update_telemetry_and_clock()

        # Auto-collapse timer (5 seconds of inactivity outside)
        self.auto_collapse_timer = QTimer(self)
        self.auto_collapse_timer.setSingleShot(True)
        self.auto_collapse_timer.timeout.connect(self._auto_collapse)

    def init_window_flags(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)

    def init_ui(self):
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.root_layout.addWidget(self.container)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(42)
        self.shadow.setOffset(0, 10)
        self.shadow.setColor(QColor(0, 0, 0, 240))
        self.container.setGraphicsEffect(self.shadow)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(14, 6, 14, 14)
        self.main_layout.setSpacing(8)

        # -------------------------------------------------------------
        # 1. TOP PILL BAR (ALWAYS VISIBLE IN BOTH STATES)
        # -------------------------------------------------------------
        self.top_bar = QWidget()
        self.top_bar_layout = QHBoxLayout(self.top_bar)
        self.top_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.top_bar_layout.setSpacing(10)

        self.status_dot = QLabel("[*]")
        self.status_dot.setObjectName("statusDot")

        self.title_label = QLabel("URNAV")
        self.title_label.setObjectName("islandTitle")

        # Mini particle wave in top bar
        self.mini_particle_wave = GeminiParticleWave(self, height=18, particle_count=18)
        self.mini_particle_wave.setFixedWidth(75)

        self.top_bar_layout.addWidget(self.status_dot)
        self.top_bar_layout.addWidget(self.title_label)
        self.top_bar_layout.addWidget(self.mini_particle_wave)

        self.pill_time_label = QLabel("12:00")
        self.pill_time_label.setObjectName("timeLabel")
        self.top_bar_layout.addWidget(self.pill_time_label)

        self.top_bar_layout.addStretch()

        self.telemetry_badge = QLabel("CPU --% | BAT --%")
        self.telemetry_badge.setObjectName("telemetryBadge")
        self.top_bar_layout.addWidget(self.telemetry_badge)

        # Quick Mic Button
        self.mic_btn = QPushButton("MIC")
        self.mic_btn.setProperty("class", "islandBtn")
        self.mic_btn.setToolTip("Activate Voice Listening")
        self.mic_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mic_btn.clicked.connect(self.toggle_microphone)
        self.top_bar_layout.addWidget(self.mic_btn)

        # Pin / Lock Button
        self.pin_btn = QPushButton("PIN")
        self.pin_btn.setProperty("class", "islandBtn")
        self.pin_btn.setToolTip("Lock Open (Disable Auto-Collapse)")
        self.pin_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pin_btn.clicked.connect(self.toggle_pin)
        self.top_bar_layout.addWidget(self.pin_btn)

        # Expand / Collapse Arrow
        self.toggle_btn = QPushButton("v")
        self.toggle_btn.setProperty("class", "islandBtn")
        self.toggle_btn.setFixedWidth(28)
        self.toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_btn.clicked.connect(self.toggle_expand)
        self.top_bar_layout.addWidget(self.toggle_btn)

        self.main_layout.addWidget(self.top_bar)

        # -------------------------------------------------------------
        # 2. EXPANDED WORKSPACE CONTENT
        # -------------------------------------------------------------
        self.expanded_container = QWidget()
        self.expanded_layout = QVBoxLayout(self.expanded_container)
        self.expanded_layout.setContentsMargins(0, 4, 0, 0)
        self.expanded_layout.setSpacing(10)

        # Gemini Glowing Particle Aura
        self.particle_wave = GeminiParticleWave(self, height=36, particle_count=40)
        self.expanded_layout.addWidget(self.particle_wave)

        # Multi-Dashboard Tab Bar
        self.tab_bar = QWidget()
        self.tab_bar_layout = QHBoxLayout(self.tab_bar)
        self.tab_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_bar_layout.setSpacing(4)

        self.tab_buttons = []
        tabs_config = [
            ("EXECUTIVE BRIEF", 0),
            ("AI COPILOT", 1),
            ("DOCUMENTS & GITHUB", 2),
            ("PC CONTROL", 3)
        ]

        for title, idx in tabs_config:
            btn = QPushButton(title)
            btn.setProperty("class", "tabBtn")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda checked=False, i=idx: self.switch_tab(i))
            self.tab_bar_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        self.tab_bar_layout.addStretch()

        # Silence Speech Button in Tab Bar
        self.silence_btn = QPushButton("SILENCE")
        self.silence_btn.setProperty("class", "islandBtn")
        self.silence_btn.setToolTip("Immediately Silence Voice Speech")
        self.silence_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.silence_btn.clicked.connect(self.silence_everything)
        self.tab_bar_layout.addWidget(self.silence_btn)

        self.expanded_layout.addWidget(self.tab_bar)

        # Multi-Dashboard Stacked Widget
        self.dashboard_stack = QStackedWidget()

        # Initialize the 4 dedicated dashboards
        self._build_dashboard_executive()
        self._build_dashboard_copilot()
        self._build_dashboard_documents_github()
        self._build_dashboard_pc_control()

        self.expanded_layout.addWidget(self.dashboard_stack)
        self.main_layout.addWidget(self.expanded_container)

        self.expanded_container.setVisible(False)
        self.switch_tab(0)

        self.apply_theme()

    # -----------------------------------------------------------------
    # DASHBOARD 1: EXECUTIVE BRIEFING
    # -----------------------------------------------------------------
    def _build_dashboard_executive(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 4, 2, 4)
        layout.setSpacing(10)

        # Banner Header
        banner = QFrame()
        banner.setProperty("class", "hudCard")
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(12, 10, 12, 10)

        b_left = QVBoxLayout()
        self.exec_greeting_label = QLabel("OPERATOR BRIEFING // ACTIVE WORKSTATION")
        self.exec_greeting_label.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 900; letter-spacing: 1px;")
        self.exec_date_label = QLabel("Monday, November 16, 2026")
        self.exec_date_label.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 700;")
        b_left.addWidget(self.exec_greeting_label)
        b_left.addWidget(self.exec_date_label)
        b_layout.addLayout(b_left)

        b_layout.addStretch()

        b_right = QVBoxLayout()
        day_prog_title = QLabel("DAY CYCLE PROGRESS")
        day_prog_title.setStyleSheet("color: #94A3B8; font-size: 10px; font-weight: 800; letter-spacing: 1px;")
        self.day_progress_bar = QProgressBar()
        self.day_progress_bar.setRange(0, 100)
        self.day_progress_bar.setValue(55)
        self.day_progress_bar.setFixedWidth(140)
        b_right.addWidget(day_prog_title)
        b_right.addWidget(self.day_progress_bar)
        b_layout.addLayout(b_right)

        layout.addWidget(banner)

        content_row = QHBoxLayout()
        content_row.setSpacing(10)

        # Left Column: Vitals & Communication Card
        left_col = QVBoxLayout()
        left_col.setSpacing(10)

        vitals_card = QFrame()
        vitals_card.setProperty("class", "hudCard")
        v_layout = QVBoxLayout(vitals_card)
        v_head = QLabel("SYSTEM VITALS TELEMETRY")
        v_head.setProperty("class", "cardHeader")
        v_layout.addWidget(v_head)

        self.cpu_bar_label = QLabel("CPU LOAD: --%")
        self.cpu_bar_label.setStyleSheet("color: #E2E8F0; font-size: 10px; font-weight: 700;")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        v_layout.addWidget(self.cpu_bar_label)
        v_layout.addWidget(self.cpu_bar)

        self.ram_bar_label = QLabel("MEMORY ALLOCATION: --%")
        self.ram_bar_label.setStyleSheet("color: #E2E8F0; font-size: 10px; font-weight: 700;")
        self.ram_bar = QProgressBar()
        self.ram_bar.setRange(0, 100)
        v_layout.addWidget(self.ram_bar_label)
        v_layout.addWidget(self.ram_bar)

        self.bat_bar_label = QLabel("POWER SUBSYSTEM: --%")
        self.bat_bar_label.setStyleSheet("color: #E2E8F0; font-size: 10px; font-weight: 700;")
        self.bat_bar = QProgressBar()
        self.bat_bar.setRange(0, 100)
        v_layout.addWidget(self.bat_bar_label)
        v_layout.addWidget(self.bat_bar)

        left_col.addWidget(vitals_card)

        comm_card = QFrame()
        comm_card.setProperty("class", "hudCard")
        c_layout = QVBoxLayout(comm_card)
        c_head = QLabel("COMMUNICATIONS & WORKSPACE")
        c_head.setProperty("class", "cardHeader")
        c_layout.addWidget(c_head)

        c_grid = QGridLayout()
        c_grid.setSpacing(6)

        btn_gmail = QPushButton("GMAIL INBOX")
        btn_gmail.setProperty("class", "launcherBtn")
        btn_gmail.clicked.connect(self.system_tools.open_gmail)
        c_grid.addWidget(btn_gmail, 0, 0)

        btn_cal = QPushButton("CALENDAR")
        btn_cal.setProperty("class", "launcherBtn")
        btn_cal.clicked.connect(self.system_tools.open_calendar)
        c_grid.addWidget(btn_cal, 0, 1)

        btn_gemini = QPushButton("GEMINI WORK")
        btn_gemini.setProperty("class", "launcherBtn")
        btn_gemini.clicked.connect(self.system_tools.open_gemini_work)
        c_grid.addWidget(btn_gemini, 1, 0)

        btn_gpt = QPushButton("CHATGPT")
        btn_gpt.setProperty("class", "launcherBtn")
        btn_gpt.clicked.connect(self.system_tools.open_chatgpt)
        c_grid.addWidget(btn_gpt, 1, 1)

        c_layout.addLayout(c_grid)
        left_col.addWidget(comm_card)
        content_row.addLayout(left_col, 1)

        # Right Column: Daily Scratchpad & Task Checklist
        right_card = QFrame()
        right_card.setProperty("class", "hudCard")
        r_layout = QVBoxLayout(right_card)
        r_head = QLabel("DAILY SCRATCHPAD // PERSISTENT NOTES")
        r_head.setProperty("class", "cardHeader")
        r_layout.addWidget(r_head)

        self.scratchpad = QPlainTextEdit()
        self.scratchpad.setPlaceholderText(
            "- Priority 1: Ingest document and synthesize executive summary\n"
            "- Priority 2: Push study notes to GitHub repository\n"
            "- Priority 3: Master operating systems scheduling and paging\n"
            "Notes auto-save as you write."
        )
        self.scratchpad.setStyleSheet(
            "background-color: #0C0E15; color: #F1F5F9; border: 1px solid rgba(255,255,255,0.08); "
            "border-radius: 10px; padding: 10px; font-size: 11px; font-family: 'Segoe UI Variable Display', 'Segoe UI', monospace;"
        )
        self._load_scratchpad()
        self.scratchpad.textChanged.connect(self._save_scratchpad)
        r_layout.addWidget(self.scratchpad)

        content_row.addWidget(right_card, 1)
        layout.addLayout(content_row)

        self.dashboard_stack.addWidget(widget)

    # -----------------------------------------------------------------
    # DASHBOARD 2: URNAV VOICE & AI COPILOT
    # -----------------------------------------------------------------
    def _build_dashboard_copilot(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 4, 2, 4)
        layout.setSpacing(10)

        status_card = QFrame()
        status_card.setProperty("class", "hudCard")
        s_layout = QHBoxLayout(status_card)
        s_layout.setContentsMargins(12, 10, 12, 10)

        self.big_mic_btn = QPushButton("ACTIVATE MICROPHONE (VOICE INPUT)")
        self.big_mic_btn.setProperty("class", "actionBtn")
        self.big_mic_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.big_mic_btn.clicked.connect(self.toggle_microphone)
        s_layout.addWidget(self.big_mic_btn)

        self.ai_status_label = QLabel("SYSTEM IDLE // READY FOR DIRECTIVE")
        self.ai_status_label.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 800; letter-spacing: 1px;")
        s_layout.addWidget(self.ai_status_label)
        s_layout.addStretch()

        layout.addWidget(status_card)

        self.copilot_log = QTextEdit()
        self.copilot_log.setObjectName("logArea")
        self.copilot_log.setReadOnly(True)
        self.copilot_log.setHtml(
            "<b style='color: #FF6B00;'>URNAV EXECUTIVE INTELLIGENCE OPERATIONAL</b><br>"
            "<span style='color: #94A3B8;'>Powered by local Qwen 2.5 1.5B (unlimited offline) with Gemini Cloud failover.</span><br><br>"
            "Ready for commands. Try:<br>"
            "• <i>'summarize my latest download'</i> or drag-and-drop a file onto this window<br>"
            "• <i>'push notes to github'</i><br>"
            "• <i>'give notes for chapter 4 operating systems'</i><br>"
            "• <i>'open and read pdf'</i>"
        )
        layout.addWidget(self.copilot_log, 1)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        btn_speak = QPushButton("READ ALOUD")
        btn_speak.setProperty("class", "islandBtn")
        btn_speak.clicked.connect(self._read_current_copilot_text)
        action_row.addWidget(btn_speak)

        btn_copy = QPushButton("COPY ANSWER")
        btn_copy.setProperty("class", "islandBtn")
        btn_copy.clicked.connect(self._copy_copilot_text)
        action_row.addWidget(btn_copy)

        btn_clear = QPushButton("CLEAR")
        btn_clear.setProperty("class", "islandBtn")
        btn_clear.clicked.connect(self.copilot_log.clear)
        action_row.addWidget(btn_clear)

        action_row.addStretch()
        layout.addLayout(action_row)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.prompt_input = QLineEdit()
        self.prompt_input.setObjectName("commandInput")
        self.prompt_input.setPlaceholderText("Type directive or question for Urnav...")
        self.prompt_input.returnPressed.connect(self.send_prompt)
        input_row.addWidget(self.prompt_input, 1)

        send_btn = QPushButton("SEND")
        send_btn.setProperty("class", "actionBtn")
        send_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        send_btn.clicked.connect(self.send_prompt)
        input_row.addWidget(send_btn)

        layout.addLayout(input_row)

        self.dashboard_stack.addWidget(widget)

    # -----------------------------------------------------------------
    # DASHBOARD 3: UNIVERSAL DOCUMENTS & GITHUB PUBLISHING
    # -----------------------------------------------------------------
    def _build_dashboard_documents_github(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 4, 2, 4)
        layout.setSpacing(8)

        # Ingestion & Dropzone Card
        drop_card = QFrame()
        drop_card.setObjectName("dropZone")
        d_layout = QHBoxLayout(drop_card)
        d_layout.setContentsMargins(12, 10, 12, 10)
        d_layout.setSpacing(10)

        d_info = QVBoxLayout()
        self.drop_title = QLabel("DRAG & DROP ANY FILE OR PDF FROM FILE EXPLORER HERE")
        self.drop_title.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: 800; letter-spacing: 1px;")
        self.drop_subtitle = QLabel("Supports PDF, DOCX, Code (.py, .js, .cpp), Markdown, JSON, and Text files")
        self.drop_subtitle.setStyleSheet("color: #94A3B8; font-size: 10px; font-weight: 600;")
        d_info.addWidget(self.drop_title)
        d_info.addWidget(self.drop_subtitle)
        d_layout.addLayout(d_info, 1)

        btn_browse_file = QPushButton("PICK FROM FILE EXPLORER")
        btn_browse_file.setProperty("class", "actionBtn")
        btn_browse_file.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_browse_file.clicked.connect(self._browse_file_explorer)
        d_layout.addWidget(btn_browse_file)

        btn_latest_download = QPushButton("USE LATEST DOWNLOAD")
        btn_latest_download.setProperty("class", "islandBtn")
        btn_latest_download.clicked.connect(self._use_latest_download)
        d_layout.addWidget(btn_latest_download)

        layout.addWidget(drop_card)

        # File Status & Pipeline Actions Bar
        meta_card = QFrame()
        meta_card.setProperty("class", "hudCard")
        m_layout = QHBoxLayout(meta_card)
        m_layout.setContentsMargins(12, 6, 12, 6)
        m_layout.setSpacing(8)

        self.file_meta_label = QLabel("NO FILE LOADED // DRAG A FILE OR CLICK PICK ABOVE")
        self.file_meta_label.setStyleSheet("color: #FF6B00; font-size: 11px; font-weight: 800;")
        m_layout.addWidget(self.file_meta_label, 1)

        self.btn_summarize_doc = QPushButton("SUMMARIZE DOCUMENT")
        self.btn_summarize_doc.setProperty("class", "actionBtn")
        self.btn_summarize_doc.setEnabled(False)
        self.btn_summarize_doc.clicked.connect(self._trigger_file_summarize)
        m_layout.addWidget(self.btn_summarize_doc)

        self.btn_push_github = QPushButton("PUSH TO GITHUB")
        self.btn_push_github.setProperty("class", "gitBtn")
        self.btn_push_github.setEnabled(False)
        self.btn_push_github.setToolTip("Push this Markdown Summary directly to your GitHub repository")
        self.btn_push_github.clicked.connect(self._trigger_github_push)
        m_layout.addWidget(self.btn_push_github)

        self.btn_github_cfg = QPushButton("GITHUB CONFIG")
        self.btn_github_cfg.setProperty("class", "islandBtn")
        self.btn_github_cfg.setToolTip("Set your GitHub Repository & Personal Access Token")
        self.btn_github_cfg.clicked.connect(self._show_github_config_dialog)
        m_layout.addWidget(self.btn_github_cfg)

        layout.addWidget(meta_card)

        # Markdown Document & Summary Viewer
        self.doc_summary_view = QTextEdit()
        self.doc_summary_view.setObjectName("logArea")
        self.doc_summary_view.setReadOnly(True)
        self.doc_summary_view.setPlaceholderText(
            "Drop any PDF or document to generate an executive study summary...\n\n"
            "Workflow:\n"
            "1. Drag file from File Explorer or click 'PICK FROM FILE EXPLORER'\n"
            "2. Urnav analyzes content and generates structured Masterclass Study Notes\n"
            "3. Click 'PUSH TO GITHUB' to immediately commit and publish to your repo"
        )
        layout.addWidget(self.doc_summary_view, 1)

        # Bottom Tools Row
        bot_row = QHBoxLayout()
        bot_row.setSpacing(8)

        btn_copy_sum = QPushButton("COPY SUMMARY")
        btn_copy_sum.setProperty("class", "islandBtn")
        btn_copy_sum.clicked.connect(self._copy_doc_summary)
        bot_row.addWidget(btn_copy_sum)

        btn_save_md = QPushButton("SAVE LOCAL MARKDOWN")
        btn_save_md.setProperty("class", "islandBtn")
        btn_save_md.clicked.connect(self._save_summary_markdown_file)
        bot_row.addWidget(btn_save_md)

        btn_open_chrome = QPushButton("OPEN PDF IN CHROME")
        btn_open_chrome.setProperty("class", "islandBtn")
        btn_open_chrome.clicked.connect(self._open_current_in_chrome)
        bot_row.addWidget(btn_open_chrome)

        btn_read_aloud_sum = QPushButton("READ ALOUD TAKEAWAYS")
        btn_read_aloud_sum.setProperty("class", "islandBtn")
        btn_read_aloud_sum.clicked.connect(self._read_doc_summary_aloud)
        bot_row.addWidget(btn_read_aloud_sum)

        bot_row.addStretch()
        self.github_status_link = QLabel("")
        self.github_status_link.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 700;")
        self.github_status_link.setOpenExternalLinks(True)
        bot_row.addWidget(self.github_status_link)

        layout.addLayout(bot_row)

        self.dashboard_stack.addWidget(widget)

    # -----------------------------------------------------------------
    # DASHBOARD 4: PC CONTROL & WORKSPACE HUB
    # -----------------------------------------------------------------
    def _build_dashboard_pc_control(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 4, 2, 4)
        layout.setSpacing(10)

        # App Launch Grid Card
        app_card = QFrame()
        app_card.setProperty("class", "hudCard")
        a_layout = QVBoxLayout(app_card)
        a_head = QLabel("APPLICATION WORKSPACE LAUNCHERS")
        a_head.setProperty("class", "cardHeader")
        a_layout.addWidget(a_head)

        grid = QGridLayout()
        grid.setSpacing(8)

        apps = [
            ("GOOGLE CHROME", "chrome"),
            ("VS CODE", "code"),
            ("FILE EXPLORER", "explorer"),
            ("WINDOWS TERMINAL", "terminal"),
            ("TASK MANAGER", "task manager"),
            ("NOTEPAD", "notepad"),
            ("CALCULATOR", "calculator"),
            ("WINDOWS SETTINGS", "settings")
        ]

        for i, (label, cmd) in enumerate(apps):
            btn = QPushButton(label)
            btn.setProperty("class", "launcherBtn")
            btn.clicked.connect(lambda checked=False, c=cmd: self.system_tools.open_application(c))
            row = i // 4
            col = i % 4
            grid.addWidget(btn, row, col)

        a_layout.addLayout(grid)
        layout.addWidget(app_card)

        # System Media & Audio Controls Card
        sys_card = QFrame()
        sys_card.setProperty("class", "hudCard")
        s_layout = QVBoxLayout(sys_card)
        s_head = QLabel("SYSTEM AUDIO & DEVICE CONTROLS")
        s_head.setProperty("class", "cardHeader")
        s_layout.addWidget(s_head)

        audio_row = QHBoxLayout()
        audio_row.setSpacing(8)

        btn_vol_up = QPushButton("VOLUME +10%")
        btn_vol_up.setProperty("class", "islandBtn")
        btn_vol_up.clicked.connect(self.system_tools.volume_up)
        audio_row.addWidget(btn_vol_up)

        btn_vol_down = QPushButton("VOLUME -10%")
        btn_vol_down.setProperty("class", "islandBtn")
        btn_vol_down.clicked.connect(self.system_tools.volume_down)
        audio_row.addWidget(btn_vol_down)

        btn_vol_mute = QPushButton("MUTE AUDIO")
        btn_vol_mute.setProperty("class", "islandBtn")
        btn_vol_mute.clicked.connect(self.system_tools.volume_mute)
        audio_row.addWidget(btn_vol_mute)

        audio_row.addStretch()
        s_layout.addLayout(audio_row)
        layout.addWidget(sys_card)

        # Screen Tools & Security Card
        sec_card = QFrame()
        sec_card.setProperty("class", "hudCard")
        sc_layout = QVBoxLayout(sec_card)
        sc_head = QLabel("SCREEN UTILITY & SECURITY")
        sc_head.setProperty("class", "cardHeader")
        sc_layout.addWidget(sc_head)

        sec_row = QHBoxLayout()
        sec_row.setSpacing(8)

        btn_snip = QPushButton("CAPTURE SCREENSHOT")
        btn_snip.setProperty("class", "actionBtn")
        btn_snip.clicked.connect(self._take_screenshot)
        sec_row.addWidget(btn_snip)

        btn_lock = QPushButton("LOCK WORKSTATION")
        btn_lock.setProperty("class", "islandBtn")
        btn_lock.clicked.connect(self.system_tools.lock_workstation)
        sec_row.addWidget(btn_lock)

        btn_theme = QPushButton("SWITCH ACCENT COLOR")
        btn_theme.setProperty("class", "islandBtn")
        btn_theme.setToolTip("Toggle between Solar Orange and Windows Accent Color")
        btn_theme.clicked.connect(self.toggle_accent_color)
        sec_row.addWidget(btn_theme)

        sec_row.addStretch()
        sc_layout.addLayout(sec_row)
        layout.addWidget(sec_card)

        layout.addStretch()
        self.dashboard_stack.addWidget(widget)

    # -----------------------------------------------------------------
    # DRAG & DROP HANDLING FROM FILE EXPLORER
    # -----------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            if not self.is_expanded:
                self.expand()
            self.switch_tab(2)
            if hasattr(self, "drop_title"):
                self.drop_title.setText("DROP FILE NOW TO ANALYZE WITH URNAV")
                self.drop_title.setStyleSheet("color: #FF6B00; font-size: 12px; font-weight: 900;")

    def dragLeaveEvent(self, event):
        if hasattr(self, "drop_title"):
            self.drop_title.setText("DRAG & DROP ANY FILE OR PDF FROM FILE EXPLORER HERE")
            self.drop_title.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: 800; letter-spacing: 1px;")

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if os.path.isfile(file_path):
                self._load_and_summarize_file(file_path)
        if hasattr(self, "drop_title"):
            self.drop_title.setText("DRAG & DROP ANY FILE OR PDF FROM FILE EXPLORER HERE")
            self.drop_title.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: 800; letter-spacing: 1px;")

    # -----------------------------------------------------------------
    # FILE INGESTION & SUMMARIZATION LOGIC
    # -----------------------------------------------------------------
    def _browse_file_explorer(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document or Code File",
            "",
            "Supported Files (*.pdf *.docx *.txt *.md *.py *.json *.csv *.cpp *.java *.html);;All Files (*.*)"
        )
        if file_path:
            self._load_and_summarize_file(file_path)

    def _use_latest_download(self):
        import glob
        downloads_dir = os.path.expanduser("~/Downloads")
        files = glob.glob(os.path.join(downloads_dir, "*.*"))
        # Exclude directories
        files = [f for f in files if os.path.isfile(f) and not f.endswith(".tmp") and not f.endswith(".crdownload")]
        if not files:
            self.file_meta_label.setText("No recent files located in Downloads folder.")
            return
        files.sort(key=os.path.getmtime, reverse=True)
        latest_file = files[0]
        self._load_and_summarize_file(latest_file)

    def _load_and_summarize_file(self, file_path: str):
        self.current_target_file = file_path
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].upper().replace(".", "") or "FILE"

        # Update metadata label
        self.file_meta_label.setText(f"LOADED: {filename} [{ext}]")
        self.btn_summarize_doc.setEnabled(True)
        self.switch_tab(2)

        # Trigger summarization automatically
        self._trigger_file_summarize()

    def _trigger_file_summarize(self):
        if not self.current_target_file:
            return

        filename = os.path.basename(self.current_target_file)
        self.doc_summary_view.setPlainText(f"Ingesting '{filename}' and synthesizing masterclass executive summary with Urnav local brain...")
        self.particle_wave.set_state("thinking")
        self.mini_particle_wave.set_state("thinking")

        self.sum_worker = SummarizeWorker(self.file_engine, self.current_target_file)
        self.sum_worker.finished_signal.connect(self._on_summary_finished)
        self.sum_worker.start()

    def _on_summary_finished(self, result: dict):
        self.particle_wave.set_state("idle")
        self.mini_particle_wave.set_state("idle")

        if result.get("success"):
            self.current_summary_path = result.get("summary_path", "")
            self.doc_summary_view.setPlainText(result.get("summary", ""))
            self.btn_push_github.setEnabled(True)

            meta_txt = f"ANALYZED: {result['filename']} | {result['file_type']} | {result['page_count']} Pages | {result['word_count']} Words"
            self.file_meta_label.setText(meta_txt)

            if self.voice_engine:
                self.voice_engine.speak(f"Summary for {result['filename']} complete. Ready to push to GitHub.")
        else:
            self.doc_summary_view.setPlainText(result.get("summary", "Summarization error occurred."))
            self.file_meta_label.setText("ANALYSIS ERROR")

    # -----------------------------------------------------------------
    # GITHUB SYNCHRONIZATION
    # -----------------------------------------------------------------
    def _trigger_github_push(self):
        if not self.current_summary_path or not os.path.exists(self.current_summary_path):
            QMessageBox.information(self, "Notice", "Please summarize a document first before pushing to GitHub.")
            return

        repo = self.file_engine.github_sync.get_repo()
        token = self.file_engine.github_sync.get_token()

        if not repo or not token:
            self._show_github_config_dialog(push_after=True)
            return

        self.github_status_link.setText("Pushing to GitHub repository...")
        self.particle_wave.set_state("thinking")

        self.push_worker = GitHubPushWorker(self.file_engine, self.current_summary_path)
        self.push_worker.finished_signal.connect(self._on_github_push_finished)
        self.push_worker.start()

    def _on_github_push_finished(self, result: dict):
        self.particle_wave.set_state("idle")
        if result.get("success"):
            url = result.get("url", "")
            if url:
                self.github_status_link.setText(f"<a href='{url}' style='color: #FF6B00; font-weight: 800;'>[VIEW ON GITHUB: {os.path.basename(url)}]</a>")
                QApplication.clipboard().setText(url)
            else:
                self.github_status_link.setText("Committed to local Git repository successfully.")

            if self.voice_engine:
                self.voice_engine.speak("Pushed to GitHub successfully.")
        else:
            self.github_status_link.setText(f"GitHub Error: {result.get('message', 'Failed')}")
            QMessageBox.warning(self, "GitHub Push Notice", result.get("message", "Could not complete GitHub push."))

    def _show_github_config_dialog(self, push_after: bool = False):
        dialog = QDialog(self)
        dialog.setWindowTitle("Urnav GitHub Integration Setup")
        dialog.setStyleSheet("background-color: #0E1017; color: #FFFFFF; font-family: 'Segoe UI', sans-serif;")
        dialog.setFixedSize(440, 260)

        d_layout = QVBoxLayout(dialog)
        d_layout.setSpacing(10)

        title = QLabel("CONFIGURE GITHUB REPOSITORY")
        title.setStyleSheet("color: #FF6B00; font-size: 13px; font-weight: 900; letter-spacing: 1px;")
        d_layout.addWidget(title)

        subtitle = QLabel("Urnav will commit and push generated study summaries directly to your repo.")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 10px;")
        d_layout.addWidget(subtitle)

        # Inputs
        repo_input = QLineEdit()
        repo_input.setPlaceholderText("Repository: username/repo-name (e.g. johndoe/notes-vault)")
        repo_input.setText(self.file_engine.github_sync.get_repo())
        repo_input.setStyleSheet("background-color: #141824; color: #FFFFFF; border: 1px solid rgba(255,107,0,0.4); border-radius: 8px; padding: 6px;")
        d_layout.addWidget(repo_input)

        token_input = QLineEdit()
        token_input.setEchoMode(QLineEdit.EchoMode.Password)
        token_input.setPlaceholderText("GitHub Personal Access Token (ghp_...)")
        token_input.setText(self.file_engine.github_sync.get_token())
        token_input.setStyleSheet("background-color: #141824; color: #FFFFFF; border: 1px solid rgba(255,107,0,0.4); border-radius: 8px; padding: 6px;")
        d_layout.addWidget(token_input)

        folder_input = QLineEdit()
        folder_input.setPlaceholderText("Target Folder in Repo (default: summaries)")
        folder_input.setText(self.file_engine.github_sync.get_folder())
        folder_input.setStyleSheet("background-color: #141824; color: #FFFFFF; border: 1px solid rgba(255,107,0,0.4); border-radius: 8px; padding: 6px;")
        d_layout.addWidget(folder_input)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("SAVE CONFIGURATION")
        btn_save.setProperty("class", "actionBtn")
        btn_save.setStyleSheet("background-color: #FF6B00; color: #000000; font-weight: 900; padding: 6px 14px; border-radius: 10px;")

        def save():
            self.file_engine.github_sync.update_credentials(
                repo=repo_input.text().strip(),
                token=token_input.text().strip(),
                folder=folder_input.text().strip() or "summaries"
            )
            dialog.accept()
            if push_after:
                self._trigger_github_push()

        btn_save.clicked.connect(save)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        d_layout.addLayout(btn_row)

        dialog.exec()

    def _copy_doc_summary(self):
        text = self.doc_summary_view.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.github_status_link.setText("Summary text copied to clipboard.")

    def _save_summary_markdown_file(self):
        text = self.doc_summary_view.toPlainText()
        if not text:
            return
        default_name = f"{os.path.splitext(os.path.basename(self.current_target_file))[0]}_Summary.md" if self.current_target_file else "Summary.md"
        path, _ = QFileDialog.getSaveFileName(self, "Save Markdown Summary", default_name, "Markdown (*.md)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.github_status_link.setText(f"Saved locally: {os.path.basename(path)}")

    def _open_current_in_chrome(self):
        if self.current_target_file and os.path.exists(self.current_target_file):
            self.system_tools.open_and_read_pdf(self.current_target_file)
        else:
            self.system_tools.open_and_read_pdf("")

    def _read_doc_summary_aloud(self):
        text = self.doc_summary_view.toPlainText()
        if text and self.voice_engine:
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip() and not p.startswith("#")]
            if paragraphs:
                self.voice_engine.speak(paragraphs[0])

    # -----------------------------------------------------------------
    # TAB NAVIGATION & THEME MANAGEMENT
    # -----------------------------------------------------------------
    def switch_tab(self, index: int):
        self.dashboard_stack.setCurrentIndex(index)
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.setProperty("active", "true")
            else:
                btn.setProperty("active", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def toggle_accent_color(self):
        self.is_system_accent = not self.is_system_accent
        if self.is_system_accent:
            self.current_accent = ThemeManager.get_windows_accent_color()
        else:
            self.current_accent = ThemeManager.DEFAULT_ORANGE
        self.apply_theme()

    def apply_theme(self):
        style = ThemeManager.get_style(self.current_accent)
        self.setStyleSheet(style)
        self.particle_wave.set_accent_color(self.current_accent)
        self.mini_particle_wave.set_accent_color(self.current_accent)

    # -----------------------------------------------------------------
    # HOVER & AUTO-COLLAPSE PHYSICS
    # -----------------------------------------------------------------
    def enterEvent(self, event):
        if self.auto_collapse_timer.isActive():
            self.auto_collapse_timer.stop()
        if not self.is_expanded:
            self.expand()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.is_expanded and not self.is_pinned:
            self.auto_collapse_timer.start(5000)
        super().leaveEvent(event)

    def _auto_collapse(self):
        if self.is_expanded and not self.is_pinned:
            self.collapse()

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        if self.is_pinned:
            self.pin_btn.setText("PINNED")
            self.pin_btn.setStyleSheet(f"background-color: {self.current_accent}; color: #000000; font-weight: 900;")
            if self.auto_collapse_timer.isActive():
                self.auto_collapse_timer.stop()
        else:
            self.pin_btn.setText("PIN")
            self.pin_btn.setStyleSheet("")

    def toggle_expand(self):
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        self.is_expanded = True
        self.expanded_container.setVisible(True)
        self.toggle_btn.setText("^")

        screen = QApplication.primaryScreen().geometry()
        target_x = (screen.width() - self.expanded_width) // 2
        target_y = 0

        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(280)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(QRect(target_x, target_y, self.expanded_width, self.expanded_height))
        self.anim.start()

    def collapse(self):
        self.is_expanded = False
        self.expanded_container.setVisible(False)
        self.toggle_btn.setText("v")

        screen = QApplication.primaryScreen().geometry()
        target_x = (screen.width() - self.collapsed_width) // 2
        target_y = 0

        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(280)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(QRect(target_x, target_y, self.collapsed_width, self.collapsed_height))
        self.anim.start()

    def center_top(self):
        screen = QApplication.primaryScreen().geometry()
        target_x = (screen.width() - self.collapsed_width) // 2
        self.setGeometry(target_x, 0, self.collapsed_width, self.collapsed_height)

    # -----------------------------------------------------------------
    # SYSTEM TELEMETRY & CLOCK
    # -----------------------------------------------------------------
    def update_telemetry_and_clock(self):
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M")
        self.pill_time_label.setText(time_str)

        if hasattr(self, "exec_date_label"):
            self.exec_date_label.setText(now.strftime("%A, %B %d, %Y"))

        hours_passed = now.hour + now.minute / 60.0
        day_pct = int(min(max((hours_passed - 8.0) / 12.0 * 100, 0), 100))
        if hasattr(self, "day_progress_bar"):
            self.day_progress_bar.setValue(day_pct)

        telemetry = self.system_tools.get_telemetry()
        cpu = int(telemetry["cpu"])
        ram = int(telemetry["ram"])
        bat = int(telemetry["battery"])

        self.telemetry_badge.setText(f"CPU {cpu}% | RAM {ram}%")

        if hasattr(self, "cpu_bar"):
            self.cpu_bar.setValue(cpu)
            self.cpu_bar_label.setText(f"CPU LOAD: {cpu}%")
        if hasattr(self, "ram_bar"):
            self.ram_bar.setValue(ram)
            self.ram_bar_label.setText(f"MEMORY ALLOCATION: {ram}%")
        if hasattr(self, "bat_bar"):
            self.bat_bar.setValue(bat)
            status_txt = "CHARGING" if telemetry.get("plugged") else "BATTERY"
            self.bat_bar_label.setText(f"POWER SUBSYSTEM: {bat}% ({status_txt})")

    # -----------------------------------------------------------------
    # VOICE & AI COPILOT INTERACTION
    # -----------------------------------------------------------------
    def toggle_microphone(self):
        if self.is_listening:
            return

        self.is_listening = True
        self.particle_wave.set_state("listening")
        self.mini_particle_wave.set_state("listening")
        self.mic_btn.setText("REC")
        self.mic_btn.setStyleSheet(f"background-color: {self.current_accent}; color: #000000; font-weight: 900;")
        self.ai_status_label.setText("MICROPHONE ACTIVE // LISTENING TO VOICE...")

        self.listener_thread = VoiceListenerThread(duration_sec=4.0)
        self.listener_thread.status_changed.connect(lambda s: self.ai_status_label.setText(s))
        self.listener_thread.transcription_ready.connect(self._on_voice_transcribed)
        self.listener_thread.error_occurred.connect(self._on_voice_error)
        self.listener_thread.finished.connect(self._on_voice_finished)
        self.listener_thread.start()

    def _on_voice_transcribed(self, text: str):
        self.prompt_input.setText(text)
        self.send_prompt()

    def _on_voice_error(self, err: str):
        self.ai_status_label.setText(f"VOICE NOTICE: {err}")

    def _on_voice_finished(self):
        self.is_listening = False
        self.particle_wave.set_state("idle")
        self.mini_particle_wave.set_state("idle")
        self.mic_btn.setText("MIC")
        self.mic_btn.setStyleSheet("")

    def send_prompt(self):
        query = self.prompt_input.text().strip()
        if not query:
            return

        self.prompt_input.clear()
        if not self.is_expanded:
            self.expand()

        prompt_lower = query.lower()

        # Voice command to summarize or push
        if "summarize" in prompt_lower and ("download" in prompt_lower or "pdf" in prompt_lower or "file" in prompt_lower):
            self.switch_tab(2)
            self._use_latest_download()
            return

        if "push" in prompt_lower and "github" in prompt_lower:
            self.switch_tab(2)
            self._trigger_github_push()
            return

        self.switch_tab(1)

        if any(w in query.lower() for w in ["shut up", "stop talking", "be quiet", "silence", "stop"]):
            self.silence_everything()
            self.copilot_log.append(f"<b style='color: #FFFFFF;'>OPERATOR:</b> {query}<br>")
            self.copilot_log.append(f"<b style='color: {self.current_accent};'>URNAV:</b> Silenced.<br>")
            return

        self.copilot_log.append(f"<b style='color: #FFFFFF;'>OPERATOR:</b> {query}<br>")
        self.particle_wave.set_state("thinking")
        self.mini_particle_wave.set_state("thinking")
        self.ai_status_label.setText("PROCESSING QUERY WITH LOCAL ENGINE...")

        self.ai_worker = AIWorker(self.gemini_client, query)
        self.ai_worker.finished_signal.connect(self._on_ai_reply)
        self.ai_worker.start()

    def _on_ai_reply(self, reply: str):
        self.particle_wave.set_state("idle")
        self.mini_particle_wave.set_state("idle")
        self.ai_status_label.setText("READY FOR DIRECTIVE")

        formatted = reply.replace("\n", "<br>")
        self.copilot_log.append(f"<b style='color: {self.current_accent};'>URNAV:</b> {formatted}<br><br>")
        self.copilot_log.verticalScrollBar().setValue(self.copilot_log.verticalScrollBar().maximum())

        if "CHAPTER NOTES" in reply or "EXECUTIVE STUDY SUMMARY" in reply:
            self.doc_summary_view.setPlainText(reply)
            self.switch_tab(2)

        if self.voice_engine:
            spoken_snippet = reply.split("\n\n")[0]
            clean_speech = spoken_snippet.replace("#", "").replace("*", "").strip()
            self.voice_engine.speak(clean_speech)

    def silence_everything(self):
        if self.voice_engine:
            self.voice_engine.stop()
        self.particle_wave.set_state("idle")
        self.mini_particle_wave.set_state("idle")
        self.ai_status_label.setText("SPEECH SILENCED")

    def on_speech_started(self):
        self.particle_wave.set_state("speaking")
        self.mini_particle_wave.set_state("speaking")

    def on_speech_finished(self):
        self.particle_wave.set_state("idle")
        self.mini_particle_wave.set_state("idle")

    def _read_current_copilot_text(self):
        text = self.copilot_log.toPlainText()
        if text and self.voice_engine:
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if lines:
                self.voice_engine.speak(lines[-1])

    def _copy_copilot_text(self):
        text = self.copilot_log.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.ai_status_label.setText("ANSWER COPIED TO CLIPBOARD")

    # -----------------------------------------------------------------
    # SCREENSHOT & SCRATCHPAD
    # -----------------------------------------------------------------
    def _take_screenshot(self):
        res = self.system_tools.capture_screenshot()
        self.ai_status_label.setText(res)

    def _load_scratchpad(self):
        scratch_file = os.path.join(os.path.dirname(__file__), "scratchpad.txt")
        if os.path.exists(scratch_file):
            try:
                with open(scratch_file, "r", encoding="utf-8") as f:
                    self.scratchpad.setPlainText(f.read())
            except Exception:
                pass

    def _save_scratchpad(self):
        scratch_file = os.path.join(os.path.dirname(__file__), "scratchpad.txt")
        try:
            with open(scratch_file, "w", encoding="utf-8") as f:
                f.write(self.scratchpad.toPlainText())
        except Exception:
            pass

    # -----------------------------------------------------------------
    # DRAG TO REPOSITION
    # -----------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos.x(), max(0, new_pos.y()))
            event.accept()
