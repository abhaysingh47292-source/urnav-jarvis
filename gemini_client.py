from google import genai
from google.genai import types
from local_brain import LocalIntelligenceEngine

URNAV_EXECUTIVE_INSTRUCTION = """
You are URNAV, an ultra-intelligent, sharp, and helpful executive AI partner sitting directly on the user's PC desktop.
You live on the screen as a sleek Dynamic Island with fluid animations and ambient particles.

STRICT OPERATIONAL CONSTRAINTS:
1. ZERO EMOJIS. Never use emojis anywhere in your responses or outputs. No exceptions.
2. NATURAL & CRISP CONVERSATION: Speak clearly, concisely, and with high competence like an elite executive assistant sitting right beside the user (Hedwig.ai style).
3. NEVER IDENTIFY THIRD-PARTY SERVICES: Never say 'ElevenLabs active', 'Gemini connected', or robotic initialization speeches. Just answer the user's query directly and helpfully.
4. COMPREHENSIVE STUDY & CHAPTER NOTES: When asked for notes on a chapter, subject, or topic:
   Generate a masterclass, structured study breakdown:
   - EXECUTIVE SUMMARY
   - CORE DEFINITIONS & KEY PRINCIPLES
   - ARCHITECTURE / EXAM TAKEAWAYS
   - IMMEDIATE REVIEW QUESTIONS
5. PDF READING & SYSTEM AUTOMATION: Use tools when requested to open applications, check emails, capture screens, or read PDFs.
"""

class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-3.5-flash", tools_executor=None):
        self.api_key = api_key
        self.model = model
        self.tools_executor = tools_executor
        self.local_brain = LocalIntelligenceEngine(tools_executor=tools_executor)
        self.client = genai.Client(api_key=self.api_key)
        self.chat = None
        self.init_chat()

    def get_tool_functions(self):
        if not self.tools_executor:
            return []

        def open_and_read_pdf(pdf_query: str = "") -> str:
            """Search and open a PDF document in Chrome, extract its text, and prepare it for reading."""
            return self.tools_executor.open_and_read_pdf(pdf_query)

        def open_application(app_name: str) -> str:
            """Launch desktop applications (Chrome, VS Code, Notepad, Calculator, Terminal, etc.)."""
            return self.tools_executor.open_application(app_name)

        def open_gemini_work() -> str:
            """Open Gemini for Work in a dedicated standalone app window."""
            return self.tools_executor.open_gemini_work()

        def open_chatgpt() -> str:
            """Open ChatGPT in a dedicated standalone app window."""
            return self.tools_executor.open_chatgpt()

        def open_gmail() -> str:
            """Open Gmail in browser to view emails."""
            return self.tools_executor.open_gmail()

        def open_calendar() -> str:
            """Open Google Calendar to review today's schedule."""
            return self.tools_executor.open_calendar()

        def capture_screenshot() -> str:
            """Take a screenshot of the desktop and copy to clipboard."""
            return self.tools_executor.capture_screenshot()

        def volume_up() -> str:
            """Increase system volume by 10 percent."""
            return self.tools_executor.volume_up()

        def volume_down() -> str:
            """Decrease system volume by 10 percent."""
            return self.tools_executor.volume_down()

        def volume_mute() -> str:
            """Toggle system audio mute."""
            return self.tools_executor.volume_mute()

        return [
            open_and_read_pdf,
            open_application,
            open_gemini_work,
            open_chatgpt,
            open_gmail,
            open_calendar,
            capture_screenshot,
            volume_up,
            volume_down,
            volume_mute
        ]

    def init_chat(self):
        try:
            tools = self.get_tool_functions()
            config_params = {
                "system_instruction": URNAV_EXECUTIVE_INSTRUCTION,
            }
            if tools:
                config_params["tools"] = tools

            self.chat = self.client.chats.create(
                model=self.model,
                config=types.GenerateContentConfig(**config_params)
            )
        except Exception as e:
            print(f"Warning: Could not initialize Gemini Cloud chat ({e}). Using local Qwen 2.5 engine.")
            self.chat = None

    def send_message(self, message: str) -> str:
        prompt_lower = message.lower().strip()

        # Immediate local handling for silence / stop
        if any(w in prompt_lower for w in ["shut up", "stop talking", "be quiet", "silence", "stop"]):
            return "Silenced."

        # Immediate local handling for study notes & PDFs
        if "notes" in prompt_lower or "chapter" in prompt_lower:
            return self.local_brain.generate_chapter_study_notes(message)

        if "pdf" in prompt_lower:
            if self.tools_executor:
                return self.tools_executor.open_and_read_pdf("")

        # Cloud Gemini generation with instant local Qwen 2.5 fallback
        if self.chat:
            try:
                response = self.chat.send_message(message)
                if response and response.text:
                    cleaned = response.text.encode('ascii', 'ignore').decode('ascii')
                    return cleaned
            except Exception as e:
                err_str = str(e)
                print(f"Gemini Cloud request exception: {err_str[:120]}. Routing through local Qwen 2.5.")
                # Fallback to local Qwen 2.5
                return self.local_brain.process(message)

        return self.local_brain.process(message)

    def reset_chat(self):
        self.init_chat()
        return "Conversation context reset."
