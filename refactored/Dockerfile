FROM python:3.11-slim

# Libs utiles pour Pillow/ReportLab + timezone
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev zlib1g-dev libfreetype6-dev tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code applicatif - copier dans un dossier refactored pour garder la structure d'imports
COPY . ./refactored/

EXPOSE 8000

# Démarrage FastAPI depuis le dossier refactored
CMD ["uvicorn", "refactored.app:app", "--host", "0.0.0.0", "--port", "8000"]
