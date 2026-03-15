from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Device:
    """Modèle pour un device/routeur"""
    device_id: int
    serial_number: str
    facility_id: int
    zone: Optional[str] = None
    
    @classmethod
    def from_cm2w_data(cls, data: dict) -> "Device":
        """Créer un Device depuis les données CM2W"""
        return cls(
            device_id=data.get("deviceId"),
            serial_number=data.get("serialNumber", ""),
            facility_id=data.get("facilityId"),
            zone=data.get("zone")
        )
