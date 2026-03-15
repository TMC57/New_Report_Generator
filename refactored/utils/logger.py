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
    
    def debug(self, message: str, facility_id: Optional[int] = None):
        """Log uniquement si DEBUG_MODE est activé"""
        if self.debug_enabled:
            print(self._format_message("DEBUG", message, facility_id), file=sys.stdout)
    
    def info(self, message: str, facility_id: Optional[int] = None):
        """Log toujours (informations importantes)"""
        print(self._format_message("INFO", message, facility_id), file=sys.stdout)
    
    def warning(self, message: str, facility_id: Optional[int] = None):
        """Log les avertissements"""
        print(self._format_message("⚠️ WARNING", message, facility_id), file=sys.stderr)
    
    def error(self, message: str, facility_id: Optional[int] = None):
        """Log les erreurs"""
        print(self._format_message("❌ ERROR", message, facility_id), file=sys.stderr)
    
    def success(self, message: str, facility_id: Optional[int] = None):
        """Log les succès"""
        print(self._format_message("✅ SUCCESS", message, facility_id), file=sys.stdout)

def get_logger(module_name: str) -> DebugLogger:
    """Factory pour créer un logger"""
    return DebugLogger(module_name)
