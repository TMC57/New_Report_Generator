import webbrowser
import threading
import time
import uvicorn

def open_browser():
    # on attend un peu que le serveur soit prêt
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000/app")
    webbrowser.open("http://127.0.0.1:8000/")
    webbrowser.open("http://127.0.0.1:8000/group-app")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("ApiRest:app", host="0.0.0.0", port=8000, reload=True)
