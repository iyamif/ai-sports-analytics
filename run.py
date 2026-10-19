import uvicorn
import os
import sys

# Ensure root dir in path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

if __name__ == "__main__":
    print("================================================================")
    print("   GARUDA AI SPORTS ANALYTICS & COMPETITION PLATFORM (GSI)      ")
    print("================================================================")
    print("🚀 Starting Web Dashboard and FastAPI Server...")
    print("👉 Dashboard URL : http://localhost:8000")
    print("👉 API Docs (Swagger): http://localhost:8000/docs")
    print("================================================================")

    from src.api.app import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
