import json
from pathlib import Path
from functools import lru_cache

import pdfplumber

from config import get_settings, resolve_project_path


_STATE_FILE_PATH = Path(__file__).resolve().parent / "data" / "active_resume.json"


def _read_active_resume_state() -> dict:
    if not _STATE_FILE_PATH.exists():
        return {}
    try:
        return json.loads(_STATE_FILE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_active_resume_state(state: dict) -> None:
    _STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE_PATH.write_text(json.dumps(state), encoding="utf-8")


def clear_active_resume_state() -> None:
    _write_active_resume_state({})
    load_pdf_text.cache_clear()


def set_active_pdf_path(pdf_path: str, imagekit_url: str = "", imagekit_file_id: str = "") -> None:
    absolute_pdf_path = resolve_project_path(pdf_path)
    state = {
        "pdf_path": str(absolute_pdf_path),
        "imagekit_url": imagekit_url,
        "imagekit_file_id": imagekit_file_id,
    }
    _write_active_resume_state(state)
    load_pdf_text.cache_clear()


def get_active_pdf_path() -> Path:
    settings = get_settings()
    state = _read_active_resume_state()
    candidate = state.get("pdf_path", "").strip()
    if candidate:
        return resolve_project_path(candidate)
    return resolve_project_path(settings.pdf_path)


def get_active_resume_source() -> dict:
    path = get_active_pdf_path()
    state = _read_active_resume_state()
    return {
        "pdf_path": str(path),
        "imagekit_url": state.get("imagekit_url", ""),
        "imagekit_file_id": state.get("imagekit_file_id", ""),
    }


@lru_cache
def load_pdf_text() -> str:
    """
    Load and cache text content from the configured PDF.
    """
    pdf_path = get_active_pdf_path()
    if not pdf_path.exists():
        return ""

    texts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            texts.append(page_text)

    return "\n\n".join(texts).strip()
