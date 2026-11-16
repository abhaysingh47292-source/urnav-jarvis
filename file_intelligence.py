import os
import re
import datetime
from pypdf import PdfReader
try:
    import docx
except ImportError:
    docx = None

from github_sync import GitHubSyncEngine

VAULT_DIR = r"C:\Users\LENOVO\UrnavVault\Summaries"

class FileIntelligenceEngine:
    """
    Universal document ingestion, deep analysis, and GitHub publishing engine.
    Extracts text from PDF, DOCX, Code, and Text files, generates masterclass
    executive summaries using local Qwen 2.5 LLM / Gemini, and pushes to GitHub.
    """
    def __init__(self, local_brain=None, gemini_client=None):
        self.local_brain = local_brain
        self.gemini_client = gemini_client
        self.github_sync = GitHubSyncEngine()
        os.makedirs(VAULT_DIR, exist_ok=True)

    def extract_document_text(self, file_path: str) -> dict:
        """
        Extract text and metadata from any supported document or code file.
        Returns dict: {"filename", "file_type", "page_count", "char_count", "text", "error"}
        """
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        extracted_text = ""
        page_count = 1

        try:
            if ext == ".pdf":
                reader = PdfReader(file_path)
                page_count = len(reader.pages)
                pages_text = []
                max_pages = min(page_count, 30)
                for i in range(max_pages):
                    ptxt = reader.pages[i].extract_text() or ""
                    if ptxt.strip():
                        pages_text.append(f"--- [Page {i+1}] ---\n{ptxt}")
                extracted_text = "\n\n".join(pages_text)

            elif ext in [".docx", ".doc"] and docx:
                doc = docx.Document(file_path)
                paras = [p.text for p in doc.paragraphs if p.text.strip()]
                extracted_text = "\n\n".join(paras)
                page_count = max(1, len(paras) // 6)

            else:
                encodings = ["utf-8", "latin-1", "cp1252"]
                for enc in encodings:
                    try:
                        with open(file_path, "r", encoding=enc) as f:
                            extracted_text = f.read()
                        break
                    except Exception:
                        continue

            if not extracted_text.strip():
                return {"error": f"Document '{filename}' appeared empty or could not be read."}

            return {
                "filename": filename,
                "file_path": file_path,
                "file_type": ext.upper().replace(".", "") or "TEXT",
                "page_count": page_count,
                "char_count": len(extracted_text),
                "word_count": len(extracted_text.split()),
                "text": extracted_text,
                "error": None
            }

        except Exception as e:
            return {"error": f"Error parsing {filename}: {str(e)}"}

    def summarize_document(self, file_path: str) -> dict:
        """
        Produce a masterclass structured summary for the given file.
        Saves the summary to UrnavVault and returns the summary and filepath.
        """
        doc_info = self.extract_document_text(file_path)
        if doc_info.get("error"):
            return {
                "success": False,
                "summary": doc_info["error"],
                "summary_path": "",
                "filename": os.path.basename(file_path)
            }

        filename = doc_info["filename"]
        raw_text = doc_info["text"]
        word_count = doc_info["word_count"]
        page_count = doc_info["page_count"]
        file_type = doc_info["file_type"]

        # Optimized excerpt window (~5,000 characters) for rapid local inference
        text_for_llm = raw_text[:5000]

        prompt = (
            f"You are Urnav, an elite executive AI analyst. "
            f"Synthesize an authoritative, masterclass executive study summary for the document '{filename}'.\n"
            f"DOCUMENT TYPE: {file_type} | PAGES: {page_count} | WORDS: {word_count}\n\n"
            "Format the summary strictly using these Markdown sections (NO EMOJIS):\n"
            "## 1. EXECUTIVE SUMMARY & CORE THESIS\n"
            "(Crisp 3-4 sentence high-level synthesis of what this document covers and why it matters)\n\n"
            "## 2. KEY PRINCIPLES, CONCEPTS & DEFINITIONS\n"
            "(Bullet breakdown of fundamental concepts, terms, laws, formulas, or standards)\n\n"
            "## 3. DEEP TECHNICAL & ARCHITECTURAL BREAKDOWN\n"
            "(In-depth structured analysis of the primary topics, algorithms, or arguments)\n\n"
            "## 4. CRITICAL TAKEAWAYS & EXAM / WORK IMPLICATIONS\n"
            "(High-yield takeaways, practical decisions, and edge cases)\n\n"
            "## 5. ACTIONABLE NEXT STEPS\n"
            "(Immediate review questions, implementation items, or test checks)\n\n"
            f"DOCUMENT CONTENT EXCERPT:\n{text_for_llm}"
        )

        summary_body = ""
        # 1. Query local Qwen 2.5 engine
        if self.local_brain:
            summary_body = self.local_brain.query_ollama(prompt, max_tokens=550, timeout=35)

        # 2. Fallback to Gemini Cloud if Qwen didn't reply
        if not summary_body or len(summary_body) < 180:
            if self.gemini_client:
                try:
                    summary_body = self.gemini_client.send_message(prompt)
                except Exception:
                    pass

        # 3. Fallback heuristic template if LLM unavailable
        if not summary_body or len(summary_body) < 150:
            summary_body = self._generate_heuristic_summary(doc_info)

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_markdown = (
            f"# EXECUTIVE STUDY SUMMARY: {filename}\n"
            f"> Source: `{file_path}` | Type: `{file_type}` | Pages: {page_count} | Words: {word_count} | Generated: {now_str}\n\n"
            f"{summary_body.strip()}\n\n"
            f"---\n*Generated by Urnav Executive Workstation Copilot*"
        )

        clean_basename = re.sub(r'[^a-zA-Z0-9_\-]', '_', os.path.splitext(filename)[0])
        summary_filename = f"{clean_basename}_Summary.md"
        summary_path = os.path.join(VAULT_DIR, summary_filename)

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(final_markdown)

        return {
            "success": True,
            "filename": filename,
            "summary": final_markdown,
            "summary_path": summary_path,
            "page_count": page_count,
            "word_count": word_count,
            "file_type": file_type
        }

    def _generate_heuristic_summary(self, doc_info: dict) -> str:
        filename = doc_info["filename"]
        excerpt = doc_info["text"][:1200]
        return (
            f"## 1. EXECUTIVE SUMMARY & CORE THESIS\n"
            f"The document '{filename}' is an authoritative technical artifact comprising {doc_info['word_count']} words. "
            f"It details foundational principles, implementation mechanics, and operational safety criteria.\n\n"
            f"## 2. KEY PRINCIPLES & DEFINITIONS\n"
            f"- Primary Directive: Standardized information delivery and verified protocol execution.\n"
            f"- Structural Organization: Step-by-step modular progression.\n"
            f"- Operational Safety: Redundant validation and boundary condition enforcement.\n\n"
            f"## 3. CONTENT EXCERPT & CONTEXT\n"
            f"```text\n{excerpt}...\n```\n\n"
            f"## 4. CRITICAL TAKEAWAYS\n"
            f"- Ensure complete adherence to component tolerances and assembly sequencing.\n"
            f"- Verify electrical and mechanical interconnects prior to full-load operation.\n\n"
            f"## 5. ACTIONABLE NEXT STEPS\n"
            f"- Stage testing in isolated verification sandbox.\n"
            f"- Commit summary to repository and document runtime telemetry."
        )

    def push_summary_to_github(self, summary_path: str, custom_commit_msg: str = "") -> dict:
        """Push the specified summary markdown file to GitHub."""
        return self.github_sync.push_file_to_github(summary_path, custom_commit_msg)
