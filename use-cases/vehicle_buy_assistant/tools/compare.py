"""
Vehicle Comparison Tool
Allows users to compare multiple vehicles side-by-side
"""

def compare_vehicles(vehicles, attributes=None):
    """
    Compare multiple vehicles side by side
    
    Args:
        vehicles: List of vehicle dictionaries to compare (2-5 vehicles)
        attributes: Specific attributes to compare (default: all key attributes)
    
    Returns:
        Formatted comparison string
    """
    if not vehicles or len(vehicles) < 2:
        return "❌ Please provide at least 2 vehicles to compare."
    
    if len(vehicles) > 5:
        vehicles = vehicles[:5]
    
    # Default attributes to compare
    if not attributes:
        attributes = ['make', 'model', 'year', 'type', 'price', 'mpg', 'safety_rating', 'features', 'description']
    
    # Build comparison table
    comparison = "\n📊 VEHICLE COMPARISON\n"
    comparison += "=" * 120 + "\n"
    
    # Header row with vehicle names
    header = f"{'Attribute':<20} | "
    for vehicle in vehicles:
        vehicle_name = f"{vehicle['make']} {vehicle['model']} ({vehicle['year']})"
        header += f"{vehicle_name:<24} | "
    comparison += header + "\n"
    comparison += "-" * 120 + "\n"
    
    # Price row
    price_row = f"{'💰 Price':<20} | "
    for vehicle in vehicles:
        price_row += f"${vehicle['price']:>22,} | "
    comparison += price_row + "\n"
    
    # Type row
    type_row = f"{'🚗 Type':<20} | "
    for vehicle in vehicles:
        type_row += f"{vehicle['type']:>24} | "
    comparison += type_row + "\n"
    
    # MPG row
    mpg_row = f"{'⛽ Fuel Efficiency':<20} | "
    for vehicle in vehicles:
        mpg = vehicle.get('mpg', 0)
        mpg_str = f"{mpg} MPG" if mpg > 0 else "Electric"
        mpg_row += f"{mpg_str:>24} | "
    comparison += mpg_row + "\n"
    
    # Safety rating row
    safety_row = f"{'🛡️ Safety Rating':<20} | "
    for vehicle in vehicles:
        rating = vehicle.get('safety_rating', 0)
        safety_row += f"{rating}/5 {'⭐' * rating:<19} | "
    comparison += safety_row + "\n"
    
    comparison += "-" * 120 + "\n"
    
    # Features
    comparison += f"{'📋 Key Features':<20} | \n"
    for vehicle in vehicles:
        vehicle_name = f"{vehicle['make']} {vehicle['model']}"
        features = vehicle.get('features', [])
        for i, feature in enumerate(features):
            if i == 0:
                comparison += f"{'':>20}   • {feature}\n"
            else:
                comparison += f"{'':>20}   • {feature}\n"
    
    comparison += "=" * 120 + "\n"
    
    return comparison


def compare_by_attribute(vehicles, attribute):
    """
    Compare vehicles by a specific attribute
    
    Args:
        vehicles: List of vehicle dictionaries
        attribute: Attribute to compare on (e.g., 'price', 'mpg', 'safety_rating')
    
    Returns:
        Sorted list of vehicles by attribute
    """
    valid_attributes = ['price', 'mpg', 'safety_rating', 'year']
    
    if attribute not in valid_attributes:
        return f"❌ Can't compare by '{attribute}'. Valid options: {', '.join(valid_attributes)}"
    
    sorted_vehicles = sorted(vehicles, key=lambda v: v.get(attribute, 0))
    
    comparison = f"\n📊 VEHICLES SORTED BY {attribute.upper()}\n"
    comparison += "=" * 60 + "\n"
    
    for i, vehicle in enumerate(sorted_vehicles, 1):
        value = vehicle.get(attribute, 'N/A')
        if attribute == 'price':
            value = f"${value:,}"
        elif attribute == 'mpg':
            value = f"{value} MPG"
        
        comparison += f"{i}. {vehicle['make']} {vehicle['model']} - {attribute}: {value}\n"
    
    comparison += "=" * 60 + "\n"
    
    return comparison


def find_best_value(vehicles):
    """
    Find the best value vehicle (best features per dollar)
    
    Args:
        vehicles: List of vehicle dictionaries
    
    Returns:
        Best value vehicle and analysis
    """
    if not vehicles:
        return "❌ No vehicles to analyze."
    
    # Calculate value score: (safety_rating * 10 + mpg) / price
    best_vehicle = None
    best_score = 0
    
    for vehicle in vehicles:
        price = vehicle.get('price', 1)
        safety = vehicle.get('safety_rating', 0)
        mpg = vehicle.get('mpg', 20) if vehicle.get('mpg', 0) > 0 else 20  # Default 20 for electric
        
        # Value score formula
        value_score = ((safety * 10) + mpg) / (price / 1000)  # Normalize by thousands
        
        if value_score > best_score:
            best_score = value_score
            best_vehicle = vehicle
    
    if best_vehicle:
        result = f"""
🏆 BEST VALUE VEHICLE
{'=' * 50}
{best_vehicle['make']} {best_vehicle['model']}
Price: ${best_vehicle['price']:,}
Safety Rating: {best_vehicle['safety_rating']}/5
Fuel Efficiency: {best_vehicle.get('mpg', 0)} MPG
Value Score: {best_score:.2f}

Why it's a great value:
✅ Excellent safety rating
✅ Good fuel efficiency
✅ Competitive pricing
✅ Reliable brand
{'=' * 50}
"""
        return result
    
    return "❌ Could not determine best value."


def compare_price_vs_features(vehicles):
    """
    Compare vehicles on price vs features ratio
    
    Args:
        vehicles: List of vehicle dictionaries
    
    Returns:
        Analysis of price vs features
    """
    comparison = "\n💰 PRICE VS FEATURES ANALYSIS\n"
    comparison += "=" * 70 + "\n"
    
    for vehicle in vehicles:
        price = vehicle.get('price', 0)
        features_count = len(vehicle.get('features', []))
        safety = vehicle.get('safety_rating', 0)
        
        # Calculate feature value
        feature_value = (features_count + (safety * 2)) / (price / 10000)
        
        comparison += f"\n{vehicle['make']} {vehicle['model']}\n"
        comparison += f"  💰 Price: ${price:,}\n"
        comparison += f"  📋 Features: {features_count}\n"
        comparison += f"  🛡️ Safety: {safety}/5\n"
        comparison += f"  ⭐ Feature Value: {feature_value:.2f}\n"
    
    comparison += "=" * 70 + "\n"
    
    return comparison
