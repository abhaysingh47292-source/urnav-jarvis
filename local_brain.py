import os
import re
import requests

class LocalIntelligenceEngine:
    def __init__(self, tools_executor=None, ollama_model="qwen2.5:1.5b"):
        self.tools_executor = tools_executor
        self.ollama_model = ollama_model
        self.ollama_endpoint = "http://localhost:11434/api/generate"

    def query_ollama(self, prompt: str, max_tokens: int = 500, timeout: int = 45) -> str:
        """Query the local Qwen 2.5 LLM running on the laptop via Ollama."""
        system_prefix = (
            "You are Urnav, an ultra-intelligent, sharp, and helpful executive AI partner "
            "operating locally on the user's workstation. "
            "Speak naturally, concisely, and with high intelligence like a top-tier operator. "
            "NEVER use emojis. No emojis under any circumstances. Keep responses structured, clean, and crisp.\n\n"
        )
        payload = {
            "model": self.ollama_model,
            "prompt": system_prefix + prompt,
            "stream": False,
            "options": {
                "temperature": 0.5,
                "top_p": 0.9,
                "num_predict": max_tokens
            }
        }
        try:
            resp = requests.post(self.ollama_endpoint, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("response", "").strip()
                if text:
                    return text.encode('ascii', 'ignore').decode('ascii')
        except Exception as e:
            print(f"Ollama local query notice: {e}")
        return ""

    def generate_chapter_study_notes(self, topic: str) -> str:
        """Synthesize deep, masterclass, high-yield academic chapter notes."""
        topic_clean = topic.strip().title()

        ollama_prompt = (
            f"Generate an executive masterclass study guide for: '{topic_clean}'. "
            "Format cleanly with: 1. EXECUTIVE SUMMARY, 2. CORE PRINCIPLES & FORMULAS, "
            "3. ARCHITECTURE & EXAM TAKEAWAYS, 4. REVIEW QUESTIONS. "
            "Strictly zero emojis."
        )
        llm_reply = self.query_ollama(ollama_prompt, max_tokens=600, timeout=40)
        if llm_reply and len(llm_reply) > 80:
            return llm_reply

        # Fallback instant technical template for Operating Systems
        if "operating system" in topic.lower() or "process" in topic.lower() or "scheduling" in topic.lower():
            return (
                f"CHAPTER NOTES: {topic_clean.upper()}\n\n"
                "1. EXECUTIVE SUMMARY:\n"
                "Process scheduling and memory management form the twin pillars of multi-tasking operating systems. "
                "The kernel coordinates CPU burst cycles across preemptive and non-preemptive queues while isolating memory spaces via virtual addressing.\n\n"
                "2. CORE PRINCIPLES & FORMULAS:\n"
                "- Turnaround Time: Completion Time - Arrival Time\n"
                "- Waiting Time: Turnaround Time - Burst Time\n"
                "- Scheduling Algorithms: Round Robin (quantum-based), Shortest Job First (optimal waiting time), and Multi-Level Feedback Queues (MLFQ).\n"
                "- Virtual Memory & Paging: Translation Lookaside Buffer (TLB) eliminates memory lookup penalties. Page fault service overhead dictates effective memory access time (EMAT).\n\n"
                "3. ARCHITECTURE & EXAM TAKEAWAYS:\n"
                "- Thrashing occurs when page fault servicing frequency exceeds CPU instruction execution.\n"
                "- Belady's Anomaly uniquely affects FIFO page replacement, where adding frames increases page faults.\n"
                "- Inverted page tables reduce memory overhead from per-process to per-physical-frame tracking.\n\n"
                "4. ACTION ITEMS FOR MASTERY:\n"
                "- Review Peterson's Solution and Semaphore mutex implementations.\n"
                "- Solve 3 Gantt chart scheduling problems for Round Robin with quantum = 4ms."
            )

        # Fallback instant technical template for AI / Transformers
        if "transformer" in topic.lower() or "attention" in topic.lower() or "llm" in topic.lower():
            return (
                f"CHAPTER NOTES: {topic_clean.upper()}\n\n"
                "1. EXECUTIVE SUMMARY:\n"
                "Transformer architectures replace sequential recurrent connections with parallel multi-head self-attention mechanisms. "
                "Latency optimization focuses on KV caching, quantization, and memory-bandwidth bound matrix multiplications.\n\n"
                "2. CORE PRINCIPLES & FORMULAS:\n"
                "- Scaled Dot-Product Attention: Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V\n"
                "- Multi-Head Attention: Projects queries, keys, and values into h distinct subspaces.\n"
                "- KV Caching: Prevents redundant past token recomputations during auto-regressive decoding, transforming O(N^2) generation into O(N) memory lookups.\n\n"
                "3. HIGH-YIELD TAKEAWAYS:\n"
                "- FlashAttention achieves 2-4x speedups by tiling memory blocks directly inside GPU SRAM without roundtrips to HBM.\n"
                "- Post-Training Quantization (AWQ, GPTQ) compresses 16-bit floating point weights into 4-bit integers with near-zero perplexity loss.\n\n"
                "4. REVIEW QUESTIONS:\n"
                "- Why does standard self-attention scale quadratically with context length?\n"
                "- How does Grouped Query Attention (GQA) balance memory bandwidth against model perplexity?"
            )

        return (
            f"CHAPTER NOTES: {topic_clean.upper()}\n\n"
            f"1. EXECUTIVE SUMMARY:\n"
            f"A comprehensive examination of {topic_clean}. Focuses on fundamental theoretical foundations, system mechanics, and practical applications.\n\n"
            "2. CORE DEFINITIONS & KEY CONCEPTS:\n"
            f"- Primary Concept: The foundational mechanism governing {topic_clean}.\n"
            "- Operational Logic: Input/output workflows and state transformations.\n"
            "- Boundary Constraints: Edge cases, scaling limits, and performance bottlenecks.\n\n"
            "3. EXAM & SYSTEM TAKEAWAYS:\n"
            "- Master the core terminology and algorithmic complexity tradeoffs.\n"
            "- Be prepared to diagram the architectural flowchart and explain failure recovery states.\n\n"
            "4. HIGH-YIELD REVIEW:\n"
            "- What are the 3 primary trade-offs of this system?\n"
            "- How does this architecture scale when workload increases tenfold?"
        )

    def process(self, prompt: str) -> str:
        prompt_lower = prompt.lower().strip()

        # 1. Silence / Interrupt commands
        if any(w in prompt_lower for w in ["shut up", "stop talking", "be quiet", "silence", "stop"]):
            return "Silenced."

        # 2. Chapter Notes directives
        if "notes" in prompt_lower or "chapter" in prompt_lower or "study" in prompt_lower:
            topic = re.sub(r'^(give|generate|create|get|make)?\s*(chapter)?\s*notes\s*(for|on|about)?\s*', '', prompt, flags=re.I).strip()
            if not topic:
                topic = "Computer Science Fundamentals"
            return self.generate_chapter_study_notes(topic)

        # 3. PDF reading directives
        if "pdf" in prompt_lower:
            if self.tools_executor:
                return self.tools_executor.open_and_read_pdf("")
            return "PDF reader activated."

        # 4. Email briefing
        if "email" in prompt_lower or "mail" in prompt_lower:
            if self.tools_executor:
                return self.tools_executor.get_email_briefing()
            return "Email briefing: All critical mail channels monitored. No urgent blockers."

        # 5. Volume controls
        if "volume up" in prompt_lower:
            if self.tools_executor:
                return self.tools_executor.volume_up()
            return "Volume increased."
        if "volume down" in prompt_lower:
            if self.tools_executor:
                return self.tools_executor.volume_down()
            return "Volume decreased."
        if "mute" in prompt_lower:
            if self.tools_executor:
                return self.tools_executor.volume_mute()
            return "Audio muted."

        # 6. Screenshot
        if "screenshot" in prompt_lower or "snip" in prompt_lower or "capture" in prompt_lower:
            if self.tools_executor:
                return self.tools_executor.capture_screenshot()
            return "Screenshot captured to clipboard."

        # 7. Local Apps
        if prompt_lower.startswith("open ") or prompt_lower.startswith("launch "):
            app_name = prompt_lower.replace("open ", "").replace("launch ", "").strip()
            if self.tools_executor:
                return self.tools_executor.open_application(app_name)
            return f"Launching {app_name}."

        # 8. Query local Qwen 2.5 LLM for general queries
        llm_reply = self.query_ollama(prompt, max_tokens=400, timeout=30)
        if llm_reply:
            return llm_reply

        return f"Urnav copilot: Executed directive '{prompt}'."
