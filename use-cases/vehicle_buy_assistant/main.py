# main.py - Complete Vehicle Buy Assistant with File Persistence
import json
import os
from agentkernel import Session
from datetime import datetime
import uuid

PREFERENCES_FILE = "user_preferences.json"

# ---------- File Persistence Functions ----------
def save_preferences_to_file(session_id, preferences):
    data = {}
    if os.path.exists(PREFERENCES_FILE):
        with open(PREFERENCES_FILE, 'r') as f:
            data = json.load(f)
    data[session_id] = preferences
    with open(PREFERENCES_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"💾 Preferences saved to {PREFERENCES_FILE}")

def load_preferences_from_file(session_id):
    if not os.path.exists(PREFERENCES_FILE):
        return None
    with open(PREFERENCES_FILE, 'r') as f:
        data = json.load(f)
    return data.get(session_id, None)

# ---------- Vehicle Data ----------
def load_vehicles():
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'vehicles.json')
    with open(data_path, 'r') as f:
        data = json.load(f)
    return data['vehicles']

def search_vehicles(preferences, vehicles):
    results = []
    for vehicle in vehicles:
        score = 0
        matches = []
        
        if preferences.get('budget'):
            try:
                budget = int(''.join(filter(str.isdigit, preferences['budget'])))
                if vehicle['price'] <= budget:
                    score += 3
                    matches.append(f"💰 Within budget (${vehicle['price']:,})")
            except:
                pass
        
        if preferences.get('type'):
            for word in preferences['type'].lower().split():
                if word in vehicle['type'].lower():
                    score += 2
                    matches.append(f"🚗 Matches {vehicle['type']}")
                    break
        
        if preferences.get('usage'):
            usage = preferences['usage'].lower()
            if 'family' in usage and vehicle['type'] in ['SUV', 'Minivan']:
                score += 2
                matches.append("👨‍👩‍👧‍👦 Great for families")
            elif 'commuting' in usage and vehicle.get('mpg', 0) >= 25:
                score += 2
                matches.append("⛽ Good for commuting")
        
        if preferences.get('features'):
            features_lower = preferences['features'].lower()
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
                'matches': matches
            })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:5]

# ---------- Memory Management Functions ----------
def save_search_history(session, search_results):
    nv_cache = session.get_non_volatile_cache()
    history = nv_cache.get("search_history", [])
    history.append({
        'timestamp': datetime.now().isoformat(),
        'results': search_results
    })
    if len(history) > 10:
        history = history[-10:]
    nv_cache.set("search_history", history)
    return history

def get_search_history(session):
    nv_cache = session.get_non_volatile_cache()
    return nv_cache.get("search_history", [])

# ---------- Conversation State ----------
class ConversationState:
    def __init__(self, session, session_id):
        self.session = session
        self.session_id = session_id
        self.nv_cache = session.get_non_volatile_cache()
        self.v_cache = session.get_volatile_cache()
    
    @property
    def step(self):
        return self.nv_cache.get("conversation_step", "budget")
    
    @step.setter
    def step(self, value):
        self.nv_cache.set("conversation_step", value)
    
    def get_preferences(self):
        return self.nv_cache.get("user_preferences", {})
    
    def update_preference(self, key, value):
        prefs = self.get_preferences()
        prefs[key] = value
        prefs['last_updated'] = datetime.now().isoformat()
        self.nv_cache.set("user_preferences", prefs)
        save_preferences_to_file(self.session_id, prefs)
    
    def load_from_file(self):
        prefs = load_preferences_from_file(self.session_id)
        if prefs:
            self.nv_cache.set("user_preferences", prefs)
            return True
        return False

# ---------- Main CLI ----------
def main():
    print("🚗 Welcome to the Vehicle Buy Assistant!")
    print("💡 Powered by Agent Kernel Memory Management")
    print("   - Your preferences are remembered across sessions")
    print("   - Search history is saved")
    print("   - Type 'exit' to quit\n")
    
    vehicles = load_vehicles()
    
    session_id = input("Enter your name (or press Enter for new session): ").strip()
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
    
    session = Session(id=f"user_{session_id}")
    state = ConversationState(session, session_id)
    
    # Try to load preferences from file
    has_file_prefs = state.load_from_file()
    
    prefs = state.get_preferences()
    if prefs:
        print(f"\n👋 Welcome back! I remember your preferences:")
        print(f"   Budget: {prefs.get('budget', 'Not set')}")
        print(f"   Type: {prefs.get('type', 'Not set')}")
        print(f"   Usage: {prefs.get('usage', 'Not set')}")
        print(f"   Features: {prefs.get('features', 'Not set')}")
        if has_file_prefs:
            print("   💾 Loaded from file!")
        print("   Let's continue your search!\n")
    else:
        print("👋 Welcome! Let's find your perfect car!\n")
    
    history = get_search_history(session)
    if history:
        print(f"📚 You've done {len(history)} previous searches.\n")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye! Your preferences are saved for next time!")
                break
            
            if user_input.lower() in ['history', 'show history']:
                history = get_search_history(session)
                if history:
                    print("\n📚 Your Search History:")
                    for i, entry in enumerate(history[-3:], 1):
                        print(f"  {i}. {entry['timestamp'][:10]} - {len(entry['results'])} vehicles found")
                else:
                    print("📭 No search history yet.")
                continue
            
            # --- FIXED: Show Preferences with file fallback ---
            if user_input.lower() in ['preferences', 'show preferences', 'show prefs']:
                prefs = state.get_preferences()
                
                # If cache is empty, try loading from file
                if not prefs:
                    prefs = load_preferences_from_file(state.session_id)
                    if prefs:
                        # Restore to cache so it works next time too
                        state.nv_cache.set("user_preferences", prefs)
                
                if prefs:
                    print("\n📋 Your Saved Preferences:")
                    print(f"   Budget: {prefs.get('budget', 'Not set')}")
                    print(f"   Vehicle Type: {prefs.get('type', 'Not set')}")
                    print(f"   Usage: {prefs.get('usage', 'Not set')}")
                    print(f"   Features: {prefs.get('features', 'Not set')}")
                    print(f"   Last Updated: {prefs.get('last_updated', 'Unknown')}")
                    print("   💾 Saved to file! It will persist after exit.")
                else:
                    print("📭 No preferences saved yet. Complete a search to save your preferences!")
                continue
            
            # --- Normal Conversation ---
            step = state.step
            
            if step == "budget":
                if any(char.isdigit() for char in user_input):
                    state.update_preference('budget', user_input)
                    state.step = "type"
                    print("🤖 Great! What type of vehicle do you prefer?")
                    print("   (SUV, Sedan, Truck, Electric, or Hybrid)")
                else:
                    print("🤖 Please tell me your budget (e.g., 'under $30,000' or '$25k')")
            
            elif step == "type":
                vehicle_types = ['suv', 'sedan', 'truck', 'electric', 'hybrid']
                if any(typ in user_input.lower() for typ in vehicle_types):
                    state.update_preference('type', user_input)
                    state.step = "usage"
                    print("🤖 What will you use the car for?")
                    print("   (commuting, family, off-road, business)")
                else:
                    print("🤖 Please specify a vehicle type: SUV, Sedan, Truck, Electric, or Hybrid")
            
            elif step == "usage":
                usage_keywords = ['commuting', 'family', 'off-road', 'business', 'work']
                if any(usage in user_input.lower() for usage in usage_keywords):
                    state.update_preference('usage', user_input)
                    state.step = "features"
                    print("🤖 Any must-have features?")
                    print("   (safety, backup camera, adaptive cruise, etc.)")
                else:
                    print("🤖 Please tell me how you'll use the car:")
                    print("   commuting, family, off-road, or business")
            
            elif step == "features":
                state.update_preference('features', user_input)
                state.step = "searching"
                
                final_prefs = state.get_preferences()
                print("\n🔍 Searching for matching vehicles...")
                print(f"   Budget: {final_prefs.get('budget', 'Not specified')}")
                print(f"   Type: {final_prefs.get('type', 'Not specified')}")
                print(f"   Usage: {final_prefs.get('usage', 'Not specified')}")
                print(f"   Features: {final_prefs.get('features', 'Not specified')}\n")
                
                results = search_vehicles(final_prefs, vehicles)
                save_search_history(session, results)
                
                if results:
                    print("🚗 Top Recommendations:\n")
                    for i, result in enumerate(results[:3], 1):
                        v = result['vehicle']
                        print(f"{i}. {v['make']} {v['model']} ({v['year']})")
                        print(f"   💰 Price: ${v['price']:,}")
                        print(f"   ⛽ MPG: {v['mpg']}")
                        print(f"   🛡️ Safety: {v['safety_rating']}/5")
                        print(f"   📝 {v['description']}")
                        print(f"   ✅ {', '.join(result['matches'])}")
                        print()
                    
                    print("💡 Type 'history' to see past searches")
                    print("💡 Type 'show preferences' to see saved preferences")
                    print("💡 Type 'exit' to quit (your preferences are saved!)")
                    
                    state.step = "budget"
                    print("\n🔄 Starting new search! Your history and preferences are saved.")
                else:
                    print("😅 No exact matches found. Try adjusting your preferences!")
                    state.step = "budget"
                    print("\n🔄 Let's try again with different preferences.")
            
            elif step == "searching":
                print("🤖 I'm still searching... Please complete your preferences first!")
            
            else:
                state.step = "budget"
                print("🤖 Let's start over. What's your budget?")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Your preferences are saved!")
            break
        except Exception as e:
            print(f"⚠️ An error occurred: {e}")
            print("Please try again.")

if __name__ == "__main__":
    main()