import json
import os


class VehicleSearchTool:
    """
    Tool for searching the vehicle database.
    Used by the Market Agent.
    """

    def __init__(self):
        self.vehicles = self._load_vehicles()

    def _load_vehicles(self):
        """Load vehicle database from JSON."""
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'vehicles.json')
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('vehicles', [])
        except FileNotFoundError:
            return self._get_fallback_vehicles()

    def _get_fallback_vehicles(self):
        """Fallback vehicle data."""
        return [
            {"id": 1, "make": "Toyota", "model": "RAV4", "year": 2024, "type": "SUV", "price": 29500, "mpg": 28, "safety_rating": 5, "features": ["Backup Camera", "Adaptive Cruise"], "description": "Reliable family SUV"},
            {"id": 2, "make": "Honda", "model": "CR-V", "year": 2024, "type": "SUV", "price": 28800, "mpg": 27, "safety_rating": 5, "features": ["Honda Sensing", "Apple CarPlay"], "description": "Comfortable SUV with great safety"},
            {"id": 3, "make": "Mazda", "model": "CX-5", "year": 2024, "type": "SUV", "price": 27500, "mpg": 24, "safety_rating": 5, "features": ["Sporty Handling", "Premium Interior"], "description": "Sporty SUV with premium feel"},
            {"id": 4, "make": "Tesla", "model": "Model Y", "year": 2024, "type": "Electric", "price": 45000, "mpg": 0, "safety_rating": 5, "features": ["Autopilot", "Large Screen"], "description": "Electric SUV with cutting-edge tech"},
            {"id": 5, "make": "Ford", "model": "Escape", "year": 2024, "type": "SUV", "price": 26500, "mpg": 26, "safety_rating": 4, "features": ["Co-Pilot360", "Hybrid Option"], "description": "Affordable SUV with good fuel efficiency"},
        ]

    def search(self, preferences):
        """Search vehicles by preferences and return matching results."""
        results = []
        for vehicle in self.vehicles:
            score = 0
            matches = []

            if preferences.get('budget'):
                try:
                    budget = int(''.join(filter(str.isdigit, str(preferences['budget']))))
                    if vehicle['price'] <= budget:
                        score += 3
                        matches.append(f"💰 Within budget (${vehicle['price']:,})")
                except (TypeError, ValueError):
                    pass

            if preferences.get('type'):
                preferred_type = str(preferences['type']).lower()
                if preferred_type in str(vehicle['type']).lower():
                    score += 2
                    matches.append(f"🚗 Matches {vehicle['type']}")

            if preferences.get('usage'):
                usage = str(preferences['usage']).lower()
                if 'family' in usage and vehicle['type'] in ['SUV', 'Minivan']:
                    score += 2
                    matches.append("👨‍👩‍👧‍👦 Great for families")
                elif 'commuting' in usage and vehicle.get('mpg', 0) >= 25:
                    score += 2
                    matches.append("⛽ Good for commuting")

            if preferences.get('features'):
                features_lower = str(preferences['features']).lower()
                if 'safety' in features_lower and vehicle['safety_rating'] >= 4:
                    score += 2
                    matches.append(f"🛡️ Safety rating {vehicle['safety_rating']}/5")
                if 'backup' in features_lower and 'Backup Camera' in vehicle['features']:
                    score += 1
                    matches.append("📷 Has backup camera")

            if score > 0:
                results.append({
                    'vehicle': vehicle,
                    'score': score,
                    'matches': matches,
                })

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:5]

    def get_vehicle_by_id(self, vehicle_id):
        """Get a specific vehicle by ID."""
        for vehicle in self.vehicles:
            if vehicle['id'] == vehicle_id:
                return vehicle
        return None

    def get_all_makes(self):
        """Get list of all makes."""
        return sorted(set(vehicle['make'] for vehicle in self.vehicles))

    def get_vehicle_count(self):
        """Get total number of vehicles."""
        return len(self.vehicles)
