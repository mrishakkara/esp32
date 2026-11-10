import os, tempfile, subprocess, pathlib, uuid, shutil
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests

ROOT = pathlib.Path(__file__).parent
WORK = pathlib.Path(tempfile.gettempdir()) / "cloud-code-jobs"
WORK.mkdir(exist_ok=True)

app = FastAPI(title="CLOUD CODE API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str = Field(min_length=1, max_length=30000)
    stdin: str = Field(default="", max_length=5000)

def safe_job():
    p = WORK / uuid.uuid4().hex
    p.mkdir(mode=0o700)
    return p

@app.get("/api/health")
def health():
    return {"ok": True, "service": "CLOUD CODE", "cpp_run": "Wandbox API", "esp32": shutil.which("arduino-cli") is not None}

@app.post("/api/cpp/run")
def cpp_run(req: CodeRequest):
    # Wandbox runs snippets in its own sandbox; user code is not executed on this server.
    try:
        listing = requests.get("https://wandbox.org/api/list.json", timeout=15)
        listing.raise_for_status()
        compilers = listing.json()
        choices = [c for c in compilers if c.get("language") == "C++" and c.get("name", "").startswith("gcc")]
        if not choices:
            raise HTTPException(503, "Wandbox üzerinde C++ derleyicisi bulunamadı.")
        compiler = choices[0]["name"]
        result = requests.post(
            "https://wandbox.org/api/compile.json",
            json={"compiler": compiler, "code": req.code, "stdin": req.stdin},
            timeout=35,
        )
        result.raise_for_status()
        data = result.json()
        return {
            "compiler": compiler,
            "status": data.get("status", "unknown"),
            "compiler_message": data.get("compiler_message", ""),
            "program_message": data.get("program_message", ""),
            "signal": data.get("signal", ""),
        }
    except requests.RequestException as e:
        raise HTTPException(502, f"Bulut C++ servisine ulaşılamadı: {e}")

@app.post("/api/cpp/exe")
def cpp_exe(req: CodeRequest):
    # Compiles only; the resulting EXE is never run on this server.
    compiler = shutil.which("x86_64-w64-mingw32-g++")
    if not compiler:
        raise HTTPException(503, "Windows EXE derleyicisi sunucuda kurulu değil.")
    job = safe_job()
    src = job / "main.cpp"
    out = job / "program.exe"
    src.write_text(req.code, encoding="utf-8")
    try:
        proc = subprocess.run(
            [compiler, "-std=c++17", "-O2", "-static", str(src), "-o", str(out)],
            capture_output=True, text=True, timeout=45, cwd=job,
        )
        if proc.returncode != 0:
            raise HTTPException(400, proc.stderr[-12000:] or "Derleme başarısız.")
        return FileResponse(out, filename="program.exe", media_type="application/octet-stream")
    except subprocess.TimeoutExpired:
        raise HTTPException(408, "Derleme zaman aşımına uğradı.")
    finally:
        # Keep successful artifact until response has started; FileResponse opens it later.
        # The OS temp directory is periodically cleaned by the host.
        pass

@app.post("/api/esp32/bin")
def esp32_bin(req: CodeRequest):
    cli = shutil.which("arduino-cli")
    if not cli:
        raise HTTPException(503, "ESP32 derleyicisi bu sunucuda kurulu değil. README'deki Docker kurulumunu kullan.")
    job = safe_job()
    sketch = job / "CloudSketch"
    sketch.mkdir()
    (sketch / "CloudSketch.ino").write_text(req.code, encoding="utf-8")
    build = job / "build"
    try:
        proc = subprocess.run(
            [cli, "compile", "--fqbn", "esp32:esp32:esp32", "--export-binaries",
             "--build-path", str(build), str(sketch)],
            capture_output=True, text=True, timeout=180, cwd=job,
        )
        if proc.returncode != 0:
            raise HTTPException(400, (proc.stdout + "\n" + proc.stderr)[-16000:])
        candidates = list(build.rglob("*.bin"))
        if not candidates:
            candidates = list(sketch.rglob("*.bin"))
        if not candidates:
            raise HTTPException(500, "Derleme başarılı görünüyor ancak BIN dosyası bulunamadı.")
        # Return the application image, not bootloader/partition table.
        app_bin = next((p for p in candidates if p.name.endswith(".ino.bin")), candidates[0])
        return FileResponse(app_bin, filename="cloud_code_esp32.bin", media_type="application/octet-stream")
    except subprocess.TimeoutExpired:
        raise HTTPException(408, "ESP32 derlemesi 180 saniyeyi aştı.")
    finally:
        # Build artifacts are temporary and are not persistent user storage.
        pass

app.mount("/", StaticFiles(directory=ROOT / "static", html=True), name="static")
