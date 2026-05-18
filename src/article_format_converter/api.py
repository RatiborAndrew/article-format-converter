from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import BadZipFile

from article_format_converter.profiles import PROFILES
from article_format_converter.service import analyze_docx, analyze_text

try:
    from fastapi import FastAPI, File, Form, HTTPException, UploadFile
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
except ImportError as error:  # pragma: no cover
    raise RuntimeError(
        "FastAPI dependencies are not installed. Install them with: pip install -e '.[web]'"
    ) from error


app = FastAPI(title="Article Format Converter", version="0.1.0")
WEB_DIR = Path(__file__).with_name("web")

app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


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
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Upload a .docx file.")

    suffix = ".docx"
    with NamedTemporaryFile(suffix=suffix) as temporary_file:
        temporary_file.write(await file.read())
        temporary_file.flush()
        try:
            return analyze_docx(temporary_file.name, profile_id=profile_id).to_dict()
        except BadZipFile as error:
            raise HTTPException(status_code=400, detail="The uploaded file is not a valid .docx archive.") from error
