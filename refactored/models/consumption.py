from dataclasses import dataclass
from typing import Optional

@dataclass
class DailyConsumption:
    """Consommation quotidienne d'un produit"""
    date: str
    qty: float
    product_id: int
    product_name: str
    zone: Optional[str] = None

@dataclass
class MonthlyConsumption:
    """Consommation mensuelle d'un produit"""
    year: int
    month: int
    qty: float
    product_id: int
    product_name: str
    zone: Optional[str] = None
