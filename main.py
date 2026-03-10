import webbrowser
import threading
import time
import uvicorn
import subprocess
import os

def start_frontend():
    """Démarre le serveur frontend React avec npm"""
    frontend_dir = os.path.join(os.path.dirname(__file__), "pixel-perfect-replica-50")
    subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def open_browser():
    """Ouvre le navigateur sur le frontend React après un délai"""
    time.sleep(5)  # Attendre que le frontend et backend soient prêts
    webbrowser.open("http://localhost:8080")

if __name__ == "__main__":
    # Démarrer le frontend React en arrière-plan
    threading.Thread(target=start_frontend, daemon=True).start()
    
    # Ouvrir le navigateur après un délai
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Démarrer le backend FastAPI (bloquant)
    uvicorn.run("ApiRest:app", host="0.0.0.0", port=8000, reload=True)
