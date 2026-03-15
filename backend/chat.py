from datetime import datetime

import google.generativeai as genai

from config import get_settings
from models import ChatMessageResponse
from pdf_loader import load_pdf_text


def _get_model() -> genai.GenerativeModel:
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)
    preferred_models = [
        settings.gemini_model,
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]

    def normalize(name: str) -> str:
        return name if name.startswith("models/") else f"models/{name}"

    supported: list[str] = []
    try:
        for model in genai.list_models():
            methods = getattr(model, "supported_generation_methods", []) or []
            if "generateContent" in methods:
                supported.append(model.name)
    except Exception:
        # If model listing fails (network/provider issue), still try preferred default.
        return genai.GenerativeModel(settings.gemini_model)

    normalized_preferred = [normalize(name) for name in preferred_models if name]
    for candidate in normalized_preferred:
        if candidate in supported:
            return genai.GenerativeModel(candidate)

    if supported:
        return genai.GenerativeModel(supported[0])

    return genai.GenerativeModel(settings.gemini_model)


def ask_pdf_aware_gemini(question: str) -> ChatMessageResponse:
    settings = get_settings()
    pdf_text = load_pdf_text()
    if not pdf_text.strip():
        return ChatMessageResponse(
            reply=(
                "I could not read resume content yet. Please upload/select a resume PDF first, "
                "then ask your question again."
            ),
            created_at=datetime.utcnow(),
        )

    system_prompt = (
        "You are an AI assistant for Aishik's portfolio website.\n"
        "Your job is to answer user questions using ONLY the resume text provided below.\n"
        "Do not invent facts.\n\n"
        "Response rules:\n"
        "1) Write in clear, natural English.\n"
        "2) Keep answers concise and professional.\n"
        "3) If asked about skills, return a section titled 'Skills' and list only skills found in resume.\n"
        "4) If asked about experience, return a section titled 'Experience' and summarize roles, companies, and durations found in resume.\n"
        "5) If information is missing in resume, say: 'This detail is not available in the resume.'\n"
        "6) Never output broken grammar like 'Aishik skill's are'. Use proper grammar.\n"
        "7) Prefer bullet points for skills/experience questions.\n\n"
        "Examples of style:\n"
        "- Question: What are Aishik's skills?\n"
        "  Answer format:\n"
        "  Skills\n"
        "  - ...\n"
        "  - ...\n"
        "- Question: Does Aishik have experience?\n"
        "  Answer format:\n"
        "  Experience\n"
        "  - Role at Company (Duration): key responsibility/achievement.\n\n"
        "PDF CONTENT START\n"
        f"{pdf_text}\n"
        "PDF CONTENT END\n"
    )

    model = _get_model()
    prompt = f"{system_prompt}\nUser question: {question}"

    response = model.generate_content(prompt)
    text = response.text if hasattr(response, "text") else str(response)

    return ChatMessageResponse(reply=text.strip(), created_at=datetime.utcnow())
