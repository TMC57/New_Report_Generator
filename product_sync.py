def sync_product_names(total_qty, stock_levels_grouped):
    """
    Synchronise les noms de produits dans total_qty avec ceux de stock_levels_grouped
    en utilisant les productId comme référence.
    
    Args:
        total_qty: dict contenant la structure avec owners -> facilities -> products
        stock_levels_grouped: dict contenant la structure de référence pour les noms
    
    Returns:
        total_qty: dict modifié avec les noms de produits synchronisés
        corrections_count: int nombre de corrections effectuées
    """
    corrections_count = 0
    
    # Créer un index des noms de produits depuis stock_levels_grouped
    stock_product_names = {}
    
    for owner in stock_levels_grouped.get("owners", []):
        for facility in owner.get("facilities", []):
            for product in facility.get("products", []):
                product_id = product.get("productId")
                product_name = product.get("name")
                if product_id and product_name:
                    stock_product_names[product_id] = product_name
    
    print(f"📋 Index créé avec {len(stock_product_names)} produits de référence")
    
    # Parcourir total_qty et corriger les noms si nécessaire
    for owner in total_qty.get("owners", []):
        for facility in owner.get("facilities", []):
            for product in facility.get("products", []):
                product_id = product.get("productId")
                current_name = product.get("name", "")
                
                if product_id in stock_product_names:
                    reference_name = stock_product_names[product_id]
                    
                    # Comparer les noms (insensible à la casse pour éviter les faux positifs)
                    if current_name.lower() != reference_name.lower():
                        print(f"🔄 ID {product_id}: '{current_name}' → '{reference_name}'")
                        product["name"] = reference_name
                        corrections_count += 1
                else:
                    print(f"⚠️  Produit ID {product_id} ('{current_name}') introuvable dans stock_levels")
    
    print(f"✅ Synchronisation terminée : {corrections_count} corrections effectuées")
    return total_qty, corrections_count