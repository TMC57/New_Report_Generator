"""
Système d'authentification avec tokens Odoo
"""
import httpx
import uuid
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuration Odoo
ODOO_URL = os.getenv("ODOO_URL", "https://tmh-corporation-odoo-basetest-23718588.dev.odoo.com")  # URL de votre serveur Odoo

# Stockage temporaire des tokens validés (en production, utiliser Redis)
validated_tokens: Dict[str, datetime] = {}

security = HTTPBearer()

async def verify_odoo_token(token: str) -> bool:
    """
    Vérifie un token auprès d'Odoo via l'endpoint public /api/verify_token_get
    """
    try:
        print(f"[AUTH] Vérification du token auprès de: {ODOO_URL}/api/verify_token_get")
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Appeler l'endpoint public de vérification de token
            response = await client.get(
                f"{ODOO_URL}/api/verify_token_get",
                params={"token": token}
            )

            print(f"[AUTH] Réponse Odoo - Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"[AUTH] Réponse Odoo - Data: {result}")
                is_valid = result.get("valid", False)

                if is_valid:
                    print(f"[AUTH] ✅ Token validé pour l'utilisateur: {result.get('user')}")
                    # Ajouter le token au cache local avec une expiration d'1 heure
                    validated_tokens[token] = datetime.now() + timedelta(hours=1)
                    return True
                else:
                    print(f"[AUTH] ❌ Token invalide ou expiré: {result.get('error', 'Aucune erreur spécifiée')}")
                    return False
            else:
                print(f"[AUTH] ❌ Erreur HTTP lors de la vérification: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        print(f"[AUTH] ❌ Exception lors de la vérification du token: {type(e).__name__}: {e}")

    return False

async def authenticate_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Middleware d'authentification
    """
    token = credentials.credentials

    # Vérifier si le token est déjà validé et encore valide
    if token in validated_tokens:
        if validated_tokens[token] > datetime.now():
            return token
        else:
            # Token expiré
            del validated_tokens[token]

    # Vérifier le token auprès d'Odoo
    if await verify_odoo_token(token):
        # Token valide, le stocker pour 1 heure
        validated_tokens[token] = datetime.now() + timedelta(hours=1)
        return token

    raise HTTPException(status_code=401, detail="Token invalide ou expiré")

async def get_current_user(request: Request) -> Optional[str]:
    """
    Récupère le token depuis les cookies ou headers
    """
    # Essayer depuis les cookies
    token = request.cookies.get("auth_token")
    if token and token in validated_tokens and validated_tokens[token] > datetime.now():
        return token

    # Essayer depuis les headers Authorization
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if token in validated_tokens and validated_tokens[token] > datetime.now():
            return token

    return None

async def require_auth(request: Request) -> str:
    """
    Dépendance pour exiger une authentification
    """
    token = await get_current_user(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentification requise")
    return token