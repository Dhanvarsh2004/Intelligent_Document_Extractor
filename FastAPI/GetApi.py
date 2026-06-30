from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import sys
import asyncio
import StatusDB as DB
from pathlib import Path
import shutil

BASE_DIR = Path(__file__).resolve().parent.parent

REQUEST_FOLDER = BASE_DIR / "Documents" / "review documents"
SUCCESS_FOLDER = BASE_DIR / "Documents" / "approved documents"
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("Connection added")
        print("Active connections:", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):

        print("Active connections:", len(self.active_connections))

        dead_connections = []

        for connection in self.active_connections:

            try:
                print("Sending update")
                await connection.send_text(message)

            except Exception as e:
                print("Connection error:", e)
                dead_connections.append(connection)

        for connection in dead_connections:
            self.active_connections.remove(connection)
        
manager = ConnectionManager()

app = FastAPI()

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)

worker_process = None

# ==========================================================

# Start Processing

# ==========================================================

@app.post("/start")
def start_processing():


    global worker_process

    # Prevent duplicate starts
    if worker_process is not None and worker_process.poll() is None:
        return {
            "message": "Processing is already running"
        }

    worker_file = Path(__file__).parent / "worker.py"

    worker_process = subprocess.Popen(
        [
            sys.executable,
            str(worker_file)
        ]
    )

    return {
        "message": "Processing started"
    }

# ==========================================================

# Dashboard

# ==========================================================


@app.get("/dashboard")
def dashboard():


    return DB.get_dashboard_data()


# ==========================================================

# Success Items

# ==========================================================

@app.get("/success-items")
def success_items():

    return DB.get_success_items()

# ==========================================================

# Review Items

# ==========================================================

@app.get("/review-items")
def review_items():


    return DB.get_review_items()


# ==========================================================

# Module Status

# ==========================================================

@app.get("/module-status")
def module_status():


    dashboard = DB.get_dashboard_data()

    return {
        "systemStatus": dashboard["systemStatus"],
        "progressPercentage": dashboard["progressPercentage"],
        "currentDocument": dashboard["currentDocument"]
    }


# ==========================================================

# Request Models

# ==========================================================
class ReviewRequest(BaseModel):
    reviewId: int
    documentName: str
    month: str
    year: str
    assetName: str
    mtdValue: str


# ==========================================================

# Approve Review

# ==========================================================

@app.post("/approve-review")
async def approve_review(request: ReviewRequest):

    DB.approve_review(
        request.reviewId,
        request.documentName,
        request.month,
        request.year,
        request.assetName,
        request.mtdValue
    )

    source_file = REQUEST_FOLDER / request.documentName
    destination_file = SUCCESS_FOLDER / request.documentName
    print(source_file)

    try:

        if source_file.exists():

            shutil.move(
                source_file,
                destination_file
            )

            print(f"{request.documentName} moved successfully")

        else:

            print(f"{request.documentName} not found")

    except Exception as e:

        print("Error moving file:", e)

    await manager.broadcast("update")

    return {
        "message": "Review item approved successfully"
    }

# ==========================================================

# Reject Review

# ==========================================================

@app.post("/reject-review")
def reject_review(request: ReviewRequest):

    DB.reject_review(request.review_id)

    return {
        "message": "Review item rejected successfully"
    }

# ==========================================================

# Health Check

# ==========================================================

@app.get("/")
def home():


    return {
        "message": "FastAPI Server Running"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    print("Client connected")

    await manager.connect(websocket)

    try:
        while True:
            await asyncio.sleep(1)

    except WebSocketDisconnect:

        print("Client disconnected")

        manager.disconnect(websocket)


@app.post("/notify-dashboard")
async def notify_dashboard():

    print("Broadcasting update")

    await manager.broadcast("update")

    return {
        "message": "Dashboard notified"
    }