"""
Point d'entrée principal du projet refactorisé
Lance le serveur FastAPI avec tous les endpoints
"""
import webbrowser
import threading
import time
import uvicorn
import sys
from pathlib import Path

# Ajouter le dossier parent au PYTHONPATH pour pouvoir importer refactored
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

def open_browser():
    """Ouvre le navigateur sur le port 8000 après un délai"""
    time.sleep(2)
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    # Ouvrir le navigateur après un délai
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Démarrer le serveur FastAPI
    uvicorn.run("refactored.app:app", host="0.0.0.0", port=8000, reload=True)
