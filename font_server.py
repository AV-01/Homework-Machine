import os
import json
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Tuple

app = FastAPI(title="Handwriting Font Creator")

# Allow CORS for development if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# Ensure directories exist
os.makedirs(FONTS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# Pydantic models for request bodies
class CharData(BaseModel):
    bounds: List[float] # [left, right]
    strokes: List[List[Tuple[float, float]]]

@app.get("/")
def read_root():
    return RedirectResponse(url="/ui/index.html")

# API Endpoints
@app.get("/api/fonts")
def list_fonts():
    fonts = []
    for f in os.listdir(FONTS_DIR):
        if f.endswith(".json"):
            fonts.append(f[:-5])
    return {"fonts": sorted(fonts)}

@app.post("/api/fonts/{font_name}")
def create_font(font_name: str):
    file_path = os.path.join(FONTS_DIR, f"{font_name}.json")
    if os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="Font already exists")
    
    with open(file_path, "w") as f:
        json.dump({}, f)
    return {"status": "success", "message": f"Font {font_name} created."}

@app.get("/api/fonts/{font_name}")
def get_font(font_name: str):
    file_path = os.path.join(FONTS_DIR, f"{font_name}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Font not found")
    
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    return data

@app.post("/api/fonts/{font_name}/{char}")
def save_character(font_name: str, char: str, data: CharData):
    file_path = os.path.join(FONTS_DIR, f"{font_name}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Font not found")
        
    with open(file_path, "r") as f:
        try:
            font_data = json.load(f)
        except json.JSONDecodeError:
            font_data = {}
            
    # Format for font_data.py is [left_boundary, right_boundary, stroke1, stroke2, ...]
    formatted_data = data.bounds + data.strokes
    font_data[char] = formatted_data
    
    with open(file_path, "w") as f:
        json.dump(font_data, f, indent=2)
        
    return {"status": "success", "message": f"Character '{char}' saved."}

@app.delete("/api/fonts/{font_name}/{char}")
def delete_character(font_name: str, char: str):
    file_path = os.path.join(FONTS_DIR, f"{font_name}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Font not found")
        
    with open(file_path, "r") as f:
        try:
            font_data = json.load(f)
        except json.JSONDecodeError:
            font_data = {}
            
    if char in font_data:
        del font_data[char]
        with open(file_path, "w") as f:
            json.dump(font_data, f, indent=2)
            
    return {"status": "success"}

# Serve static UI files last so API routes take precedence
app.mount("/ui", StaticFiles(directory=ASSETS_DIR), name="ui")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("Starting Font Creator Server on http://localhost:8000")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
