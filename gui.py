import os
import base64
import asyncio
import tempfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import yt_dlp
from pathlib import Path
from typing import Dict, Any

app = FastAPI()

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Estado global para el progreso (en un app real usaríamos algo más robusto)
download_status = {
    "progress": "0%",
    "speed": "0 MB/s",
    "eta": "00:00",
    "status": "idle",
    "filename": ""
}

class DownloadRequest(BaseModel):
    url: str
    quality: str

def progress_hook(d):
    global download_status
    if d['status'] == 'downloading':
        download_status["progress"] = d.get('_percent_str', '0%').strip()
        download_status["speed"] = d.get('_speed_str', '0 MB/s').strip()
        download_status["eta"] = d.get('_eta_str', '00:00').strip()
        download_status["status"] = "downloading"
        download_status["filename"] = d.get('filename', '').split(os.sep)[-1]
    elif d['status'] == 'finished':
        download_status["status"] = "finished"
        download_status["progress"] = "100%"

def run_download(url: str, quality_setting: str):
    global download_status
    output_dir = Path.cwd() / "descargas"
    output_dir.mkdir(exist_ok=True)
    
    output_template = str(output_dir / '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': quality_setting,
        'outtmpl': output_template,
        'extract_audio': True,
        'audio_format': 'mp3',
        'progress_hooks': [progress_hook],
        'js_runtimes': {'node': {}},
        'remote_components': ['ejs:github'],
        'quiet': True,
        'no_warnings': True,
    }

    cookies_base64 = os.environ.get("COOKIES_BASE64")
    cookies_file = os.environ.get("COOKIES_FILE")
    if cookies_base64:
        try:
            decoded = base64.b64decode(cookies_base64).decode("utf-8")
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
            tmp.write(decoded)
            tmp.close()
            ydl_opts["cookiefile"] = tmp.name
            logger.info("Usando COOKIES_BASE64 (%d bytes)", len(decoded))
        except Exception as e:
            logger.error("Error al decodificar COOKIES_BASE64: %s", e)
    elif cookies_file and os.path.isfile(cookies_file):
        ydl_opts["cookiefile"] = cookies_file
        logger.info("Usando COOKIES_FILE: %s", cookies_file)
    else:
        browser = os.environ.get("COOKIES_BROWSER", "firefox")
        ydl_opts["cookiesfrombrowser"] = (browser,)
        logger.info("Usando cookiesfrombrowser: %s", browser)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        logger.error("Error en descarga: %s", e)
        download_status["status"] = f"error: {str(e)}"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.post("/download")
async def start_download(req: DownloadRequest, background_tasks: BackgroundTasks):
    global download_status
    # Reset status
    download_status = {
        "progress": "0%",
        "speed": "0 MB/s",
        "eta": "00:00",
        "status": "starting",
        "filename": ""
    }
    
    quality_map = {
        "high": 'bestaudio/best',
        "mid": 'bestaudio[brate>=320]/bestvideo[ext=m4a]/best',
        "low": 'worstaudio/best'
    }
    
    q_setting = quality_map.get(req.quality, 'bestaudio/best')
    background_tasks.add_task(run_download, req.url, q_setting)
    return {"message": "Download started"}

@app.get("/status")
async def get_status():
    return download_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
