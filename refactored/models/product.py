from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Product:
    """Modèle pour un produit"""
    product_id: int
    name: str
    zone: Optional[str] = None
    
    remaining_quantity: Optional[float] = None
    remaining_quantity_unit: str = "L"
    average_daily_consumption: Optional[float] = None
    remaining_days: Optional[int] = None
    
    @classmethod
    def from_stock_data(cls, data: dict) -> "Product":
        """Créer un Product depuis les données de stock"""
        remaining_qty_str = data.get("remainingQuantity", "0 L")
        qty_parts = remaining_qty_str.split()
        remaining_qty = float(qty_parts[0]) if qty_parts else 0.0
        unit = qty_parts[1] if len(qty_parts) > 1 else "L"
        
        avg_consumption_str = data.get("averageDailyConsumption", "0 L")
        avg_parts = avg_consumption_str.split()
        avg_consumption = float(avg_parts[0]) if avg_parts else 0.0
        
        return cls(
            product_id=data.get("productId"),
            name=data.get("name", ""),
            remaining_quantity=remaining_qty,
            remaining_quantity_unit=unit,
            average_daily_consumption=avg_consumption,
            remaining_days=data.get("remainingDays")
        )

@dataclass
class ProductConsumption:
    """Modèle pour la consommation d'un produit"""
    product_id: int
    name: str
    zone: Optional[str] = None
    
    total_qty: float = 0.0
    daily_quantities: List[dict] = field(default_factory=list)
    monthly_quantities: List[dict] = field(default_factory=list)
