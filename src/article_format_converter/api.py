from __future__ import annotations

from tempfile import NamedTemporaryFile

from article_format_converter.profiles import PROFILES
from article_format_converter.service import analyze_docx, analyze_text

try:
    from fastapi import FastAPI, File, Form, UploadFile
except ImportError as error:  # pragma: no cover
    raise RuntimeError(
        "FastAPI dependencies are not installed. Install them with: pip install -e '.[web]'"
    ) from error


app = FastAPI(title="Article Format Converter", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/profiles")
def profiles() -> list[dict[str, str]]:
    return [
        {
            "id": profile.id,
            "name": profile.name,
            "version": profile.version,
        }
        for profile in PROFILES.values()
    ]


@app.post("/analyze-text")
def analyze_text_endpoint(
    text: str = Form(...),
    profile_id: str = Form("pravoslavny-teolog"),
) -> dict:
    return analyze_text(text, profile_id=profile_id).to_dict()


@app.post("/analyze-docx")
async def analyze_docx_endpoint(
    file: UploadFile = File(...),
    profile_id: str = Form("pravoslavny-teolog"),
) -> dict:
    suffix = ".docx" if file.filename and file.filename.lower().endswith(".docx") else ""
    with NamedTemporaryFile(suffix=suffix) as temporary_file:
        temporary_file.write(await file.read())
        temporary_file.flush()
        return analyze_docx(temporary_file.name, profile_id=profile_id).to_dict()
