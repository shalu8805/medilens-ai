import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

# Reports yahan save hongi: backend/storage/reports/<user_id>/
STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage" / "reports"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Extension -> file type
ALLOWED_EXTENSIONS = {
    ".pdf": "pdf",
    ".jpg": "jpg",
    ".jpeg": "jpg",
    ".png": "png",
}

# File ke andar ke pehle bytes (asli type pehchanne ke liye)
MAGIC_BYTES = {
    "pdf": b"%PDF-",
    "jpg": b"\xff\xd8\xff",
    "png": b"\x89PNG\r\n\x1a\n",
}


def validate_and_read(upload: UploadFile) -> tuple[bytes, str]:
    """File check karta hai. Sahi ho to (content, file_type) deta hai."""
    filename = upload.filename or ""
    extension = Path(filename).suffix.lower()

    # 1. Extension check
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, JPG and PNG files are allowed",
        )
    file_type = ALLOWED_EXTENSIONS[extension]

    # 2. Size check (limit se 1 byte zyada padhte hain, taaki badi file pakdi jaye)
    content = upload.file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large (maximum 10 MB)",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    # 3. Asli content check: sirf naam badalke .pdf karne se kaam nahi chalega
    if not content.startswith(MAGIC_BYTES[file_type]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match its type",
        )

    return content, file_type


def save_file(user_id: int, content: bytes, file_type: str) -> str:
    """File ko user ke private folder mein random naam se save karta hai."""
    user_folder = STORAGE_ROOT / str(user_id)
    user_folder.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid.uuid4().hex}.{file_type}"
    (user_folder / stored_filename).write_bytes(content)
    return stored_filename


def delete_file(user_id: int, stored_filename: str) -> None:
    """File ko disk se hatata hai (agar hai)."""
    file_path = STORAGE_ROOT / str(user_id) / stored_filename
    file_path.unlink(missing_ok=True)