import sys
from datetime import datetime
from typing import Optional
from refactored.config.settings import DEBUG_MODE

class DebugLogger:
    """Logger avec mode debug pour tracer la récupération et le traitement des données"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.debug_enabled = DEBUG_MODE
    
    def _format_message(self, level: str, message: str, facility_id: Optional[int] = None) -> str:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        facility_info = f" [Facility {facility_id}]" if facility_id else ""
        return f"[{timestamp}] [{level}] [{self.module_name}]{facility_info} {message}"

    @staticmethod
    def _emit(text: str, stream):
        """Ecrit dans le flux sans jamais crasher sur un caractere non encodable
        (ex: emojis vers une console Windows cp1252)."""
        try:
            print(text, file=stream)
        except UnicodeEncodeError:
            enc = getattr(stream, "encoding", None) or "utf-8"
            print(text.encode(enc, errors="replace").decode(enc), file=stream)

    def debug(self, message: str, facility_id: Optional[int] = None):
        """Log uniquement si DEBUG_MODE est activé"""
        if self.debug_enabled:
            self._emit(self._format_message("DEBUG", message, facility_id), sys.stdout)

    def info(self, message: str, facility_id: Optional[int] = None):
        """Log toujours (informations importantes)"""
        self._emit(self._format_message("INFO", message, facility_id), sys.stdout)

    def warning(self, message: str, facility_id: Optional[int] = None):
        """Log les avertissements"""
        self._emit(self._format_message("⚠️ WARNING", message, facility_id), sys.stderr)

    def error(self, message: str, facility_id: Optional[int] = None):
        """Log les erreurs"""
        self._emit(self._format_message("❌ ERROR", message, facility_id), sys.stderr)

    def success(self, message: str, facility_id: Optional[int] = None):
        """Log les succès"""
        self._emit(self._format_message("✅ SUCCESS", message, facility_id), sys.stdout)

def get_logger(module_name: str) -> DebugLogger:
    """Factory pour créer un logger"""
    return DebugLogger(module_name)
