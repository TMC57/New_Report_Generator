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


def add_missing_facilities(total_qty, devices_list):
    """
    Ajoute les facilities manquantes de devices_list dans total_qty.
    
    Args:
        total_qty: dict contenant la structure avec owners -> facilities -> products
        devices_list: dict contenant la liste des devices avec facilityId, owner, etc.
    
    Returns:
        total_qty: dict modifié avec les facilities manquantes ajoutées
        added_count: int nombre de facilities ajoutées
    """
    added_count = 0
    
    # Créer un index des facilities existantes dans total_qty par facilityId
    existing_facilities = set()
    for owner in total_qty.get("owners", []):
        for facility in owner.get("facilities", []):
            facility_id = facility.get("facilityId")
            if facility_id:
                existing_facilities.add(facility_id)
    
    print(f"📋 {len(existing_facilities)} facilities existantes dans total_qty")
    
    # Créer un index des owners dans total_qty
    owners_index = {}
    for owner in total_qty.get("owners", []):
        owner_name = owner.get("owner")
        if owner_name:
            owners_index[owner_name] = owner
    
    # Parcourir devices_list pour trouver les facilities manquantes
    for device_facility in devices_list.get("data", []):
        facility_id = device_facility.get("facilityId")
        facility_name = device_facility.get("facilityName")
        owner_name = device_facility.get("owner")
        
        if facility_id and facility_id not in existing_facilities:
            print(f"➕ Ajout facility manquante: ID {facility_id} - {facility_name} (Owner: {owner_name})")
            
            # Trouver ou créer l'owner dans total_qty
            if owner_name not in owners_index:
                # Créer un nouveau owner
                new_owner = {
                    "owner": owner_name,
                    "totalQty": 0.0,
                    "facilities": []
                }
                total_qty.setdefault("owners", []).append(new_owner)
                owners_index[owner_name] = new_owner
                print(f"  🏢 Nouvel owner créé: {owner_name}")
            
            # Ajouter la facility à l'owner
            new_facility = {
                "facilityId": facility_id,
                "facilityName": facility_name,
                "totalQty": 0.0,
                "products": []
            }
            owners_index[owner_name]["facilities"].append(new_facility)
            existing_facilities.add(facility_id)
            added_count += 1
    
    print(f"✅ Ajout terminé : {added_count} facilities ajoutées")
    return total_qty, added_count