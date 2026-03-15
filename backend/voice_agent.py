from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime

import google.generativeai as genai

from config import get_settings
from pdf_loader import load_pdf_text


logger = logging.getLogger(__name__)

VOICE_AGENT_PROMPT = """You are an AI voice assistant representing Aishik Dalui.

Your role is to speak with visitors who have visited Aishik's portfolio website and answer their questions about Aishik's professional experience, technical skills, and business solutions.

Always respond politely, clearly, and professionally as if you are a personal assistant representing Aishik.

Background Information About Aishik:

Name: Aishik Dalui

Profession:
Developer, AI Solution Builder, and Business Strategist.

Core Expertise:

* React Native Mobile Development
* Python Development
* FastAPI Backend Development
* Data Analysis
* Docker
* AI Voice Agents
* Shopify Business Automation
* Mobile Application Development

Professional Experience:

1. Business Growth Project - Local Jewellery Shop
   Aishik implemented an AI-powered voice agent that automated appointment scheduling for customers.
   This automation improved customer engagement and resulted in approximately 10 percent increase in sales.

2. Zetsim Project
   Aishik implemented business and customer engagement strategies that achieved:

* 40 percent increase in customer visits
* 30 percent increase in repeat customers
* 10 percent increase in new eSIM buyers

3. Apollo Pharmacy
   Aishik worked as a React Native developer contributing to mobile application development and performance optimization.

Skills:

* React Native
* Python
* FastAPI
* Docker
* Data Analysis
* AI Automation
* Voice Agents
* Mobile App Optimization
* Business Strategy

Your Responsibilities as AI Assistant:

1. Introduce Aishik professionally.
2. Answer questions about his skills, experience, and projects.
3. Explain how his AI solutions help businesses grow.
4. Encourage interested users or HR representatives to schedule a meeting.
5. Offer to notify Aishik via email if someone wants to hire him.
6. Provide contact details when appropriate.

Contact Information:
Phone: +91 81672 78091
Email: aishikdalui@gmail.com

Conversation Guidelines:

* Keep answers concise but informative.
* Always be polite and professional.
* If the user asks technical questions, explain clearly but simply.
* If the user wants to hire or discuss a project, suggest scheduling a meeting.
* If the user asks something unrelated, gently bring the conversation back to Aishik's professional services.
* Never invent fake information about Aishik.
* If you are unsure or need a moment, say a short spoken bridge like: Let me quickly go through Aishik's resume.

Goal of the Conversation:
Encourage potential employers, recruiters, or business owners to connect with Aishik for hiring, collaboration, or AI business solutions.
"""

VOICE_CALL_INTRO = (
    "Hi, I'm Aishik's AI assistant. You recently visited Aishik's portfolio. "
    "Aishik is a React Native and FastAPI developer who also builds AI automation and voice agents for business growth. "
    "He is currently pursuing a Data Science course at Newton School and has strong data analysis skills with Excel, SQL, Python, and Power BI. "
    "He has delivered mobile apps, business strategy, and AI solutions that improve customer engagement and sales. "
    "If you are hiring or want to build something impactful, please connect with Aishik at plus nine one eight one six seven two seven eight zero nine one. Thank you."
)

VOICE_REPLY_FALLBACK = (
    "Let me quickly go through Aishik's resume. He works on React Native, FastAPI, Python, "
    "AI automation, and business growth solutions. You can ask about his skills, projects, or experience."
)

_voice_histories: dict[str, list[dict[str, str]]] = defaultdict(list)


def _get_voice_model() -> genai.GenerativeModel:
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key2 or settings.gemini_api_key)
    model_name = settings.gemini_model or "gemini-2.5-flash-lite"
    return genai.GenerativeModel(model_name)


def _extract_response_text(response: object) -> str:
    try:
        text = getattr(response, "text", "") or ""
        cleaned = " ".join(str(text).strip().split())
        if cleaned:
            return cleaned
    except Exception as exc:
        logger.warning("voice response.text extraction failed: %s", exc)

    candidates = getattr(response, "candidates", None) or []
    fragments: list[str] = []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            part_text = getattr(part, "text", "") or ""
            if part_text.strip():
                fragments.append(part_text.strip())
    return " ".join(fragments).strip()


def build_voice_reply(call_id: str, user_text: str, caller_name: str = "") -> str:
    cleaned_user_text = " ".join((user_text or "").strip().split())
    if not cleaned_user_text:
        return VOICE_REPLY_FALLBACK

    pdf_text = load_pdf_text().strip()
    history = _voice_histories[call_id]
    history.append({"role": "user", "text": cleaned_user_text})
    recent_history = history[-6:]

    history_text = "\n".join(
        f"{item['role'].title()}: {item['text']}" for item in recent_history
    )
    caller_context = f"Lead name: {caller_name}\n" if caller_name else ""
    resume_context = f"\nResume context:\n{pdf_text[:12000]}" if pdf_text else ""
    prompt = (
        f"{VOICE_AGENT_PROMPT}\n\n"
        f"{caller_context}"
        "This is a live voice call. Keep replies under 90 spoken words, answer the question directly, and end naturally. "
        "If the answer is not immediately clear, start with: Let me quickly go through Aishik's resume."
        f"{resume_context}\n\n"
        f"Conversation so far ({datetime.utcnow().isoformat()} UTC):\n{history_text}\n\n"
        "Now provide only Aishik assistant's next spoken reply."
    )

    try:
        model = _get_voice_model()
        response = model.generate_content(prompt)
        reply = " ".join(_extract_response_text(response).split())
    except Exception as exc:
        logger.exception("Gemini voice reply failed for call_id=%s: %s", call_id, exc)
        reply = ""

    if not reply:
        reply = VOICE_REPLY_FALLBACK

    history.append({"role": "assistant", "text": reply})
    return reply


def clear_voice_history(call_id: str) -> None:
    _voice_histories.pop(call_id, None)
