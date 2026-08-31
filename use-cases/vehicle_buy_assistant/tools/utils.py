"""
Utility functions for Vehicle Buy Assistant
Export, formatting, and helper functions
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path


def export_to_csv(results, filename=None):
    """
    Export search results to CSV file
    
    Args:
        results: List of search result dictionaries
        filename: Output filename (default: recommendations_TIMESTAMP.csv)
    
    Returns:
        Path to created CSV file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recommendations_{timestamp}.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if not results:
                return f"❌ No results to export."
            
            # Get all field names from first result
            fieldnames = ['rank', 'make', 'model', 'year', 'type', 'price', 'mpg', 'safety_rating', 'features', 'description', 'match_score']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, result in enumerate(results, 1):
                vehicle = result.get('vehicle', {})
                row = {
                    'rank': i,
                    'make': vehicle.get('make', ''),
                    'model': vehicle.get('model', ''),
                    'year': vehicle.get('year', ''),
                    'type': vehicle.get('type', ''),
                    'price': vehicle.get('price', ''),
                    'mpg': vehicle.get('mpg', ''),
                    'safety_rating': vehicle.get('safety_rating', ''),
                    'features': '; '.join(vehicle.get('features', [])),
                    'description': vehicle.get('description', ''),
                    'match_score': result.get('score', 0)
                }
                writer.writerow(row)
        
        return f"✅ Exported {len(results)} vehicles to {filename}"
    
    except Exception as e:
        return f"❌ Export failed: {str(e)}"


def export_to_json(data, filename=None):
    """
    Export data to JSON file
    
    Args:
        data: Data to export
        filename: Output filename (default: data_TIMESTAMP.json)
    
    Returns:
        Path to created JSON file
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        return f"✅ Exported to {filename}"
    
    except Exception as e:
        return f"❌ Export failed: {str(e)}"


def print_vehicle_card(vehicle, show_features=True):
    """
    Print a formatted vehicle card
    
    Args:
        vehicle: Vehicle dictionary
        show_features: Whether to show features list
    
    Returns:
        Formatted string
    """
    card = f"""
{'='*60}
🚗 {vehicle['make']} {vehicle['model']} ({vehicle['year']})
{'='*60}
Type:           {vehicle['type']}
Price:          ${vehicle['price']:,}
Fuel Efficiency: {vehicle.get('mpg', 0)} MPG
Safety Rating:   {vehicle['safety_rating']}/5 {'⭐' * vehicle['safety_rating']}

📝 {vehicle['description']}
{'='*60}
"""
    
    if show_features:
        card += "✨ Key Features:\n"
        for i, feature in enumerate(vehicle.get('features', []), 1):
            card += f"   {i}. {feature}\n"
        card += "=" * 60 + "\n"
    
    return card


def format_recommendation_report(recommendations):
    """
    Format recommendations as a detailed report
    
    Args:
        recommendations: List of recommendation dictionaries
    
    Returns:
        Formatted report string
    """
    if not recommendations:
        return "❌ No recommendations available."
    
    report = f"\n{'='*70}\n"
    report += f"{'🚗 VEHICLE RECOMMENDATION REPORT':^70}\n"
    report += f"{'Generated: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^70}\n"
    report += f"{'='*70}\n\n"
    
    report += f"📊 Summary: {len(recommendations)} vehicles recommended\n\n"
    
    for i, rec in enumerate(recommendations, 1):
        vehicle = rec.get('vehicle', {})
        matches = rec.get('matches', [])
        score = rec.get('score', 0)
        
        report += f"\n{'─'*70}\n"
        report += f"#{i} - {vehicle['make']} {vehicle['model']}\n"
        report += f"{'─'*70}\n"
        report += f"Price: ${vehicle['price']:,} | MPG: {vehicle.get('mpg', 0)} | Safety: {vehicle['safety_rating']}/5\n"
        report += f"Match Score: {score}/10\n\n"
        report += "Why this vehicle matches:\n"
        
        for match in matches:
            report += f"  ✅ {match}\n"
        
        report += f"\nDescription: {vehicle['description']}\n"
    
    report += f"\n{'='*70}\n"
    report += f"{'End of Report':^70}\n"
    report += f"{'='*70}\n"
    
    return report


def create_comparison_table(vehicles):
    """
    Create a text-based comparison table
    
    Args:
        vehicles: List of vehicle dictionaries
    
    Returns:
        Formatted table string
    """
    if len(vehicles) < 2:
        return "❌ Need at least 2 vehicles to compare."
    
    table = "\n" + "="*120 + "\n"
    table += f"{'VEHICLE COMPARISON':<20}"
    
    for vehicle in vehicles[:5]:  # Max 5 vehicles
        name = f"{vehicle['make']} {vehicle['model']}"
        table += f" | {name:<20}"
    
    table += "\n" + "-"*120 + "\n"
    
    # Price row
    table += f"{'💰 PRICE':<20}"
    for vehicle in vehicles[:5]:
        table += f" | ${vehicle['price']:>18,}"
    table += "\n"
    
    # Type row
    table += f"{'🚗 TYPE':<20}"
    for vehicle in vehicles[:5]:
        table += f" | {vehicle['type']:>20}"
    table += "\n"
    
    # MPG row
    table += f"{'⛽ FUEL EFFICIENCY':<20}"
    for vehicle in vehicles[:5]:
        mpg = vehicle.get('mpg', 0)
        mpg_str = f"{mpg} MPG" if mpg > 0 else "Electric"
        table += f" | {mpg_str:>20}"
    table += "\n"
    
    # Safety row
    table += f"{'🛡️ SAFETY RATING':<20}"
    for vehicle in vehicles[:5]:
        rating = vehicle.get('safety_rating', 0)
        table += f" | {rating}/5{' ⭐' * rating:<15}"
    table += "\n"
    
    table += "="*120 + "\n"
    
    return table


def save_preferences(preferences, filename='user_preferences.json'):
    """
    Save user preferences to file
    
    Args:
        preferences: Preferences dictionary
        filename: Output filename
    
    Returns:
        Status message
    """
    try:
        # Load existing preferences if file exists
        existing = {}
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                existing = json.load(f)
        
        # Add timestamp
        preferences['saved_at'] = datetime.now().isoformat()
        
        # Save
        with open(filename, 'w') as f:
            json.dump(existing, f, indent=2)
        
        return f"✅ Preferences saved to {filename}"
    
    except Exception as e:
        return f"❌ Failed to save preferences: {str(e)}"


def load_preferences(filename='user_preferences.json'):
    """
    Load user preferences from file
    
    Args:
        filename: Input filename
    
    Returns:
        Preferences dictionary or None
    """
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"❌ Failed to load preferences: {str(e)}")
        return None


def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=40, fill='█'):
    """
    Create a simple progress bar (alternative to tqdm)
    
    Args:
        iteration: Current iteration
        total: Total iterations
        prefix: Prefix text
        suffix: Suffix text
        decimals: Decimal places for percentage
        length: Length of progress bar
        fill: Character to fill with
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='')
    
    # Print new line on complete
    if iteration == total:
        print()


def format_price(price):
    """Format price with proper currency formatting"""
    return f"${price:,.2f}"


def format_safety_rating(rating):
    """Format safety rating with stars"""
    return f"{rating}/5 {'⭐' * rating}"


def highlight_matches(matches_list):
    """Format a list of matches with emojis"""
    return "\n".join([f"  ✅ {match}" for match in matches_list])
