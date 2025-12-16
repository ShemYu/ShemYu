from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import uvicorn

from src.loader import YamlDataLoader
from src.generator import Jinja2Generator
from src.ai import GeminiAIProvider

app = FastAPI(title="ShemYu CV Manager")

# Setup Dependencies
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
WEB_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

# Create necessary directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), 'static'), exist_ok=True)
os.makedirs(WEB_TEMPLATE_DIR, exist_ok=True)

loader = YamlDataLoader(DATA_DIR)
generator = Jinja2Generator(TEMPLATE_DIR)
ai_provider = GeminiAIProvider()

# Mount Static
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), 'static')), name="static")
templates = Jinja2Templates(directory=WEB_TEMPLATE_DIR)

# Models
class SectionUpdate(BaseModel):
    data: List[Dict[str, Any]]

class BasicsUpdate(BaseModel):
    data: Dict[str, Any]

class TailorRequest(BaseModel):
    jd_text: str

# API Endpoints
@app.get("/api/profile")
async def get_profile():
    return loader.load()

@app.post("/api/profile/basics")
async def update_basics(update: BasicsUpdate):
    try:
        loader.save_basics(update.data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profile/{section}")
async def update_section(section: str, update: SectionUpdate):
    try:
        loader.save_section(section, update.data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tailor")
async def tailor_resume(request: TailorRequest):
    try:
        profile = loader.load()
        tailored_profile = ai_provider.tailor_profile(profile, request.jd_text)
        return tailored_profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/preview/bible")
async def preview_bible(tailored: Optional[bool] = False):
    """Render the Bible resume HTML directly."""
    # Note: In a real app we might want to store tailored state in a session or pass it in.
    # For simplicity, we just load fresh data. If the client wants to preview tailored, 
    # they should POST the tailored JSON to a temporary preview endpoint or we handle it here.
    # Actually, let's keep it simple: This preview just views whatever is in data/.
    # To preview tailored, we need to accept the profile data.
    profile = loader.load()
    html = generator.render(profile, 'resume_bible.html.j2')
    return HTMLResponse(content=html)

@app.post("/preview/custom")
async def preview_custom(profile: Dict[str, Any]):
    """Render the preview with provided (tailored) JSON."""
    html = generator.render(profile, 'resume_bible.html.j2')
    return HTMLResponse(content=html)

@app.post("/api/generate")
async def generate_artifacts(background_tasks: BackgroundTasks, profile: Optional[Dict[str, Any]] = None):
    """Trigger generation of items in output/"""
    if not profile:
        profile = loader.load()
    
    def _generate(prof):
        # Determine suffix
        suffix = "_tailored" if profile else "" 
        # Wait, if profile IS passed, it's tailored. If not, it's master.
        # But wait, logic above says 'if not profile: load master'.
        # We need a way to distinguish.
        # Let's assume if the client sends a profile, it is tailored.
        
        # Actually simplest is just to generate everything.
        # But usually we want to distinguish tailored vs master.
        # Let's stick to master generation if no profile, tailored if profile.
        
        is_tailored = "ai_highlight" not in prof and suffix == "" # Rough check or just trust context
        # Better: Client sends a flag? 
        # Let's just generate with suffix if it looks different? No.
        
        # Hardcode: API generates 'master' set.
        generator.generate(prof, 'resume.md.j2', os.path.join(OUTPUT_DIR, 'RESUME.md'))
        generator.generate(prof, 'resume.html.j2', os.path.join(OUTPUT_DIR, 'resume.html'))
        generator.generate(prof, 'resume_bible.html.j2', os.path.join(OUTPUT_DIR, 'resume_bible.html'))
        
    background_tasks.add_task(_generate, profile)
    return {"status": "started", "output_dir": OUTPUT_DIR}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("src.web.app:app", host="127.0.0.1", port=8000, reload=True)
