import base64

import requests

from config import get_settings


def upload_pdf_to_imagekit(file_bytes: bytes, file_name: str) -> dict:
    settings = get_settings()
    if not settings.imagekit_private_key:
        raise ValueError("IMAGEKIT_PRIVATE_KEY is missing.")

    payload = {
        "fileName": file_name,
        "file": base64.b64encode(file_bytes).decode("utf-8"),
        "folder": settings.imagekit_resume_folder,
        "useUniqueFileName": "true",
    }

    response = requests.post(
        "https://upload.imagekit.io/api/v1/files/upload",
        auth=(settings.imagekit_private_key, ""),
        data=payload,
        timeout=25,
    )
    if not response.ok:
        raise ValueError(f"ImageKit upload failed: {response.text}")

    data = response.json()
    return {
        "url": data.get("url", ""),
        "file_id": data.get("fileId", ""),
    }


def upload_image_to_imagekit(file_bytes: bytes, file_name: str, folder: str = "/project-images") -> dict:
    settings = get_settings()
    if not settings.imagekit_private_key:
        raise ValueError("IMAGEKIT_PRIVATE_KEY is missing.")

    payload = {
        "fileName": file_name,
        "file": base64.b64encode(file_bytes).decode("utf-8"),
        "folder": folder,
        "useUniqueFileName": "true",
    }
    response = requests.post(
        "https://upload.imagekit.io/api/v1/files/upload",
        auth=(settings.imagekit_private_key, ""),
        data=payload,
        timeout=25,
    )
    if not response.ok:
        raise ValueError(f"ImageKit image upload failed: {response.text}")
    data = response.json()
    return {
        "url": data.get("url", ""),
        "file_id": data.get("fileId", ""),
    }


def delete_imagekit_file(file_id: str) -> None:
    if not file_id:
        return

    settings = get_settings()
    if not settings.imagekit_private_key:
        raise ValueError("IMAGEKIT_PRIVATE_KEY is missing.")

    response = requests.delete(
        f"https://api.imagekit.io/v1/files/{file_id}",
        auth=(settings.imagekit_private_key, ""),
        timeout=20,
    )
    if not response.ok:
        raise ValueError(f"ImageKit delete failed: {response.text}")
