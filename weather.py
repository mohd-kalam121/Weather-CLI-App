import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
HISTORY_FILE = "history.json"

def get_aqi_advisory(aqi):
    if aqi == 1: return "Good", "Air quality is ideal for outdoor activities."
    elif aqi == 2: return "Fair", "Air quality is generally acceptable."
    elif aqi == 3: return "Moderate", "Sensitive individuals should reduce outdoor activity."
    elif aqi == 4: return "Poor", "Everyone may begin to experience health effects."
    elif aqi == 5: return "Very Poor", "Health warnings of emergency conditions."
    return "Unknown", "No advisory available."

def load_history():
    """Reads the history file safely."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_history(entry):
    """Saves the latest search, keeping only the last 5."""
    history = load_history()
    history.insert(0, entry)  # Put new search at the top
    history = history[:5]     # Keep only the latest 5
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def show_history():
    """Prints the history log to the terminal."""
    history = load_history()
    if not history:
        print("No search history available yet.")
        return
    print("\n--- Last 5 Searches ---")
    for i, item in enumerate(history, 1):
        print(f"{i}. {item['city']}: {item['temp']}°C | {item['desc']} | AQI: {item['aqi']}")
    print("-----------------------\n")

def fetch_weather(city):
    if not API_KEY:
        print("Error: API key is missing. Check your .env file.")
        return

    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(weather_url, timeout=5)
        
        if response.status_code == 404:
            print(f"Error: City '{city}' not found.")
            return
            
        response.raise_for_status()
        data = response.json()
        
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        desc = data['weather'][0]['description'].capitalize()
        lat = data['coord']['lat']
        lon = data['coord']['lon']
        city_name = data['name']

        aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        aqi_response = requests.get(aqi_url, timeout=5)
        aqi_response.raise_for_status()
        aqi_data = aqi_response.json()
        
        aqi_value = aqi_data.get('list', [{}])[0].get('main', {}).get('aqi', 0)
        aqi_category, advisory = get_aqi_advisory(aqi_value)

        print(f"\n# Output")
        print(f"Weather in {city_name}")
        print(f"Temperature: {temp:.0f}°C (Feels like {feels_like:.0f}°C)")
        print(f"Humidity: {humidity}% | Wind Speed: {wind_speed} km/h | Condition: {desc}")
        print(f"Air Quality Index: {aqi_value} - {aqi_category}")
        print(f"Advisory: {advisory}\n")

        # Save this successful query to our JSON file
        save_history({
            "city": city_name,
            "temp": round(temp),
            "desc": desc,
            "aqi": aqi_value
        })

    except requests.exceptions.RequestException:
        print("Network error. Please check your internet connection.")
    except KeyError:
        print("Error: Unexpected data format received from API.")

if __name__ == "__main__":
    print("=== Weather Dashboard ===")
    
    # Requirement: Display last search on startup
    startup_history = load_history()
    if startup_history:
        last = startup_history[0]
        print(f"[Last Search: {last['city']} - {last['temp']}°C, {last['desc']}]")

    while True:
        # We use a while loop so the user can type multiple cities without restarting
        city_input = input("Enter city name (or type 'history' / 'exit'): ").strip()
        
        if city_input.lower() == 'exit':
            print("Goodbye!")
            break
        elif city_input.lower() == 'history':
            show_history()
        elif city_input:
            fetch_weather(city_input)