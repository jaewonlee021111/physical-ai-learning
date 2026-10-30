"""Local image collection UI for an existing ESP32 JPEG capture endpoint."""
import io
import os
import re
import zipfile
from pathlib import Path
from uuid import uuid4
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from PIL import Image, ImageOps

app=FastAPI(title="27일 이미지 수집")
ROOT=Path(os.getenv("DATASET_DIR","runtime/dataset")).resolve()
CAPTURE_URL=os.getenv("CAPTURE_URL","")

def folder(label):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",label):
        raise HTTPException(422,"Use a short class name: letters/digits/_/-")
    path=ROOT/label
    path.mkdir(parents=True,exist_ok=True)
    return path

def photo(label,name):
    if not re.fullmatch(r"[a-f0-9]{32}\.jpg",name):
        raise HTTPException(404,"Photo not found")
    p=folder(label)/name
    if not p.is_file():
        raise HTTPException(404,"Photo not found")
    return p

@app.get("/",response_class=HTMLResponse)
def home():
    return (Path(__file__).parent/"web/collector.html").read_text(encoding="utf-8")

@app.post("/classes/{label}/capture",status_code=201)
async def capture(label:str):
    target=folder(label)
    if not CAPTURE_URL:
        raise HTTPException(503,"CAPTURE_URL is not configured; no camera attached")
    try:
        async with httpx.AsyncClient(timeout=10,follow_redirects=False) as client:
            async with client.stream("GET",CAPTURE_URL) as response:
                response.raise_for_status()
                data=bytearray()
                async for chunk in response.aiter_bytes():
                    data.extend(chunk)
                    if len(data)>8_000_000:
                        raise ValueError("Image too large")
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            rgb=ImageOps.exif_transpose(image).convert("RGB")
    except (httpx.HTTPError,OSError,ValueError):
        raise HTTPException(502,"Camera HTTP/JPEG read failed")
    name=uuid4().hex+".jpg"
    rgb.save(target/name,quality=95)
    return {"name":name,"label":label,"source":"configured_camera_http"}

@app.get("/classes/{label}")
def listing(label:str):
    return {"label":label,"photos":[p.name for p in sorted(folder(label).glob("*.jpg"))]}

@app.get("/classes/{label}/{name}")
def image(label:str,name:str):
    return FileResponse(photo(label,name),media_type="image/jpeg")

@app.delete("/classes/{label}/{name}",status_code=204)
def remove(label:str,name:str):
    photo(label,name).unlink()
    return Response(status_code=204)

@app.get("/download/{label}")
def download(label:str):
    output=io.BytesIO()
    with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(folder(label).glob("*.jpg")):
            archive.write(p,arcname=label+"/"+p.name)
    return Response(output.getvalue(),media_type="application/zip",headers={"Content-Disposition":f'attachment; filename="{label}.zip"'})
