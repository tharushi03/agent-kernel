# main.py - Complete Vehicle Buy Assistant with Real-Time Scraping
import json
import os
from agentkernel import Session
from datetime import datetime
import uuid

# Import new features
try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    COLOR_ENABLED = True
except ImportError:
    COLOR_ENABLED = False

try:
    from tqdm import tqdm
    TQDM_ENABLED = True
except ImportError:
    TQDM_ENABLED = False

# Import new tools
from tools.financing import calculate_emi, format_financing_info, calculate_total_cost
from tools.compare import compare_vehicles, compare_by_attribute, find_best_value
from tools.pii_handler import PIIGuardian, redact_all_pii, check_for_pii
from tools.utils import export_to_csv, create_comparison_table, format_recommendation_report, print_vehicle_card

# Import vehicle API (Parse.bot)
try:
    from tools.vehicle_api import fetch_vehicles_from_api
    API_ENABLED = True
except ImportError:
    API_ENABLED = False

# Import web scraper
try:
    from tools.vehicle_scraper import get_realtime_vehicles
    SCRAPER_ENABLED = True
except ImportError:
    SCRAPER_ENABLED = False

PREFERENCES_FILE = "user_preferences.json"
pii_guardian = PIIGuardian(auto_redact=True)


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

# ---------- Vehicle Data with Real-Time Scraping ----------
def load_vehicles():
    """
    Load vehicles with multi-source priority chain:
      1. Parse.bot API (real Riyasewana data - most reliable)
      2. Web scraping fallback (Riyasewana + PatPat)
      3. Local Sri Lankan vehicles.json (always works offline)
    """
    vehicles = []
    cache_path = os.path.join(os.path.dirname(__file__), 'data', 'cached_vehicles.json')

    # ── Priority 1: Parse.bot API ──────────────────────────────
    if API_ENABLED:
        try:
            print_colored("  📡 Trying Parse.bot / Riyasewana API...", Fore.CYAN if COLOR_ENABLED else None)
            vehicles = fetch_vehicles_from_api(limit=20)
            if vehicles and len(vehicles) >= 5:
                print_colored(f"\n✅ Loaded {len(vehicles)} real-time listings from API!\n",
                              Fore.GREEN if COLOR_ENABLED else None)
                # Cache successful API response
                try:
                    with open(cache_path, 'w') as f:
                        json.dump(vehicles, f, indent=2)
                except Exception:
                    pass
                return vehicles
        except Exception as e:
            print_colored(f"⚠️ API failed: {str(e)[:80]}", Fore.YELLOW if COLOR_ENABLED else None)

    # ── Priority 2: Web scraping ───────────────────────────────
    if SCRAPER_ENABLED:
        try:
            print_colored("  📡 Trying web scraping (Riyasewana + PatPat)...",
                          Fore.CYAN if COLOR_ENABLED else None)
            vehicles = get_realtime_vehicles(limit_per_site=10, use_cache=True,
                                             cache_file=cache_path)
            if vehicles and len(vehicles) >= 3:
                print_colored(f"\n✅ Loaded {len(vehicles)} real-time listings from scraping!\n",
                              Fore.GREEN if COLOR_ENABLED else None)
                return vehicles
        except Exception as e:
            print_colored(f"⚠️ Scraping failed: {str(e)[:80]}",
                          Fore.YELLOW if COLOR_ENABLED else None)

    # ── Priority 3: Cached results ─────────────────────────────
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
            if cached and len(cached) >= 3:
                print_colored(f"\n✅ Loaded {len(cached)} vehicles from cache\n",
                              Fore.GREEN if COLOR_ENABLED else None)
                return cached
        except Exception:
            pass

    # ── Priority 4: Local Sri Lankan database (always works) ───
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'vehicles.json')
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                data = json.load(f)
            vehicles = data.get('vehicles', [])
            print_colored(f"\n✅ Loaded {len(vehicles)} vehicles from local Sri Lankan database\n",
                          Fore.GREEN if COLOR_ENABLED else None)
            return vehicles
    except Exception as e:
        print_colored(f"❌ Error loading vehicles: {e}\n", Fore.RED if COLOR_ENABLED else None)

    return []


def search_vehicles(preferences, vehicles):
    """
    Search and rank vehicles based on user preferences
    Handles both scraped and local vehicle data formats
    """
    results = []
    
    for vehicle in vehicles:
        score = 0
        matches = []
        
        # Safe field access for scraped data
        vehicle_type = vehicle.get('type', 'Unknown').lower()
        vehicle_price = vehicle.get('price', 0)
        vehicle_mpg = vehicle.get('mpg', 0)
        vehicle_safety = vehicle.get('safety_rating', 4)
        vehicle_features = vehicle.get('features', [])
        
        # Budget matching
        if preferences.get('budget'):
            try:
                budget = int(''.join(filter(str.isdigit, preferences['budget'])))
                if vehicle_price <= budget:
                    score += 3
                    matches.append(f"💰 Within budget (${vehicle_price:,})" if vehicle_price else f"💰 Within budget")
                elif vehicle_price <= budget * 1.15:  # Allow 15% flexibility
                    score += 2
                    matches.append(f"💰 Slightly over budget")
            except:
                pass
        
        # Type matching
        if preferences.get('type'):
            pref_type = preferences['type'].lower()
            if any(word in vehicle_type for word in pref_type.split()):
                score += 2
                matches.append(f"🚗 Matches {vehicle.get('type', 'Type')}")
        
        # Usage matching
        if preferences.get('usage'):
            usage = preferences['usage'].lower()
            if 'family' in usage and vehicle_type in ['suv', 'minivan', 'luxury suv', 'hatchback']:
                score += 2
                matches.append("👨‍👩‍👧‍👦 Great for families")
            elif 'commuting' in usage and vehicle_mpg >= 20:
                score += 2
                matches.append(f"⛽ Good for commuting ({vehicle_mpg} MPG)")
            elif 'off-road' in usage and vehicle_type in ['suv', 'truck']:
                score += 2
                matches.append("🏔️ Great for off-road")
            elif 'business' in usage and vehicle_type in ['sedan', 'luxury suv']:
                score += 2
                matches.append("💼 Professional appearance")
        
        # Features matching
        if preferences.get('features'):
            features_lower = preferences['features'].lower()
            if 'safety' in features_lower and vehicle_safety >= 4:
                score += 2
                matches.append(f"🛡️ Safety rating {vehicle_safety}/5")
            if 'efficiency' in features_lower and vehicle_mpg >= 25:
                score += 1
                matches.append(f"⛽ Efficient ({vehicle_mpg} MPG)")
            if ('technology' in features_lower or 'tech' in features_lower) and vehicle_features:
                score += 1
                matches.append("📱 Modern technology")
        
        if score > 0:
            results.append({
                'vehicle': vehicle,
                'score': score,
                'matches': matches
            })
    
    # Sort by score and return top results
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:10]


# ---------- New Feature Functions ----------
def show_financing_options(vehicles, selected_indices=None):
    """Show financing options for selected vehicles"""
    if selected_indices:
        selected = [vehicles[i-1] for i in selected_indices if 0 < i <= len(vehicles)]
    else:
        selected = vehicles[:3]
    
    for vehicle in selected:
        print(format_financing_info(vehicle))
        print()


def show_comparison(results):
    """Show vehicle comparison"""
    vehicles = [result['vehicle'] for result in results[:5]]
    
    if len(vehicles) < 2:
        print_colored("❌ Need at least 2 vehicles to compare.", Fore.RED)
        return
    
    print(create_comparison_table(vehicles))


def show_detailed_report(results):
    """Show detailed recommendation report"""
    print(format_recommendation_report(results))


def find_best_fit(results):
    """Find and display the best value vehicle"""
    vehicles = [result['vehicle'] for result in results]
    print(find_best_value(vehicles))


def handle_csv_export(results):
    """Export recommendations to CSV"""
    if not results:
        print_colored("❌ No results to export.", Fore.RED)
        return
    
    message = export_to_csv(results)
    print_colored(message, Fore.GREEN if "✅" in message else Fore.RED)


def print_colored(text, color=None):
    """Print colored text if colorama is available"""
    if COLOR_ENABLED and color:
        print(color + text + Style.RESET_ALL)
    else:
        print(text)

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
    print("   - Type 'help' for all commands")
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
        print_colored(f"\n👋 Welcome back! I remember your preferences:", Fore.GREEN if COLOR_ENABLED else None)
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
    
    latest_results = []  # Store latest search results for use with commands
    
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
            
            # --- New Commands ---
            if user_input.lower() == 'help':
                print_colored("\n📖 AVAILABLE COMMANDS:", Fore.CYAN if COLOR_ENABLED else None)
                print("""
  Core Commands:
    • history          - Show past searches
    • preferences      - Show saved preferences
    • export csv       - Export results to CSV
    
  Analysis Commands (use after search):
    • compare          - Compare vehicles side-by-side
    • financing        - Show monthly payment estimates
    • best value       - Find best value vehicle
    • report           - Show detailed report
    
  System Commands:
    • help             - Show this help message
    • exit/quit/bye    - Exit the program
    • restart          - Start a new search
                """)
                continue
            
            if user_input.lower() == 'export csv':
                if latest_results:
                    handle_csv_export(latest_results)
                else:
                    print_colored("❌ No search results to export. Complete a search first.", Fore.RED if COLOR_ENABLED else None)
                continue
            
            if user_input.lower() == 'compare':
                if latest_results:
                    show_comparison(latest_results)
                else:
                    print_colored("❌ No results to compare. Complete a search first.", Fore.RED if COLOR_ENABLED else None)
                continue
            
            if user_input.lower() == 'financing':
                if latest_results:
                    vehicles = [r['vehicle'] for r in latest_results]
                    show_financing_options(vehicles)
                else:
                    print_colored("❌ No results. Complete a search first.", Fore.RED if COLOR_ENABLED else None)
                continue
            
            if user_input.lower() == 'best value':
                if latest_results:
                    find_best_fit(latest_results)
                else:
                    print_colored("❌ No results. Complete a search first.", Fore.RED if COLOR_ENABLED else None)
                continue
            
            if user_input.lower() == 'report':
                if latest_results:
                    show_detailed_report(latest_results)
                else:
                    print_colored("❌ No results. Complete a search first.", Fore.RED if COLOR_ENABLED else None)
                continue
            
            if user_input.lower() == 'restart':
                state.step = "budget"
                state.nv_cache.set("user_preferences", {})
                print_colored("\n🔄 Starting fresh! What's your budget?", Fore.CYAN if COLOR_ENABLED else None)
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
                
                # Simulate progress with tqdm if available
                search_items = vehicles if TQDM_ENABLED else [None]
                if TQDM_ENABLED:
                    for _ in tqdm(search_items, desc="Searching vehicles", ncols=60):
                        pass
                
                results = search_vehicles(final_prefs, vehicles)
                latest_results = results  # Store for later commands
                save_search_history(session, results)
                
                if results:
                    print_colored("🚗 Top Recommendations:\n", Fore.GREEN if COLOR_ENABLED else None)
                    for i, result in enumerate(results[:5], 1):
                        v = result['vehicle']
                        price = v.get('price', 0)
                        # Format price: LKR for local/API data, USD for legacy data
                        if price > 500000:  # LKR prices are typically > 500k
                            price_str = f"Rs. {price:,}"
                        elif price > 0:
                            price_str = f"${price:,}"
                        else:
                            price_str = "Price on request"
                        source = v.get('source', '')
                        print(f"{i}. {v['make']} {v['model']} ({v['year']}) [{source}]")
                        print(f"   💰 Price: {price_str}")
                        if v.get('mileage'):
                            print(f"   🛣️  Mileage: {v['mileage']:,} km")
                        if v.get('city'):
                            print(f"   📍 Location: {v['city']}")
                        if v.get('fuel'):
                            print(f"   ⛽ Fuel: {v['fuel']}")
                        elif v.get('mpg'):
                            print(f"   ⛽ MPG: {v['mpg']}")
                        print(f"   🛡️ Safety: {v['safety_rating']}/5")
                        print(f"   📝 {v['description']}")
                        print(f"   ✅ Matches: {', '.join(result['matches'])}")
                        print()
                    
                    print_colored("💡 Available Commands:", Fore.CYAN if COLOR_ENABLED else None)
                    print("   • compare       - Compare vehicles side-by-side")
                    print("   • financing     - Show monthly payment estimates")
                    print("   • best value    - Find the best value option")
                    print("   • export csv    - Export to CSV file")
                    print("   • report        - Show detailed analysis")
                    print("   • history       - See past searches")
                    print("   • help          - Show all commands")
                    
                    state.step = "budget"
                    print_colored("\n🔄 Starting new search! Your history and preferences are saved.", Fore.CYAN if COLOR_ENABLED else None)
                else:
                    print_colored("😅 No exact matches found. Try adjusting your preferences!", Fore.YELLOW if COLOR_ENABLED else None)
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