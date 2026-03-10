import webbrowser
import threading
import time
import uvicorn

def open_browser():
    """Ouvre le navigateur sur le port 8000 après un délai"""
    time.sleep(2)  # Attendre que le backend soit prêt
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    # Ouvrir le navigateur après un délai
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Démarrer le backend FastAPI qui sert aussi le frontend React (bloquant)
    uvicorn.run("ApiRest:app", host="0.0.0.0", port=8000, reload=True)
