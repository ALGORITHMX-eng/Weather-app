from flask import Flask, request, jsonify
from flask_cors import CORS
from collections import OrderedDict
from datetime import datetime
import urllib.request
import json

app = Flask(__name__)
CORS(app)

API_KEY = "62acfe029ef72824cce2ced7d280874e"

def fetch_json(url):
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

@app.route("/weather", methods=["POST"])
def get_weather():
    data = request.get_json()
    city = data.get("city")
    
    if not city:
        return jsonify({"error": "City is required"}), 400

    # Current weather
    current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={API_KEY}"
    try:
        current_data = fetch_json(current_url)
    except:
        return jsonify({"error": "City not found or API error"}), 400

    lat = current_data["coord"]["lat"]
    lon = current_data["coord"]["lon"]

    current = {
        "temp": current_data["main"]["temp"],
        "feels_like": current_data["main"]["feels_like"],
        "description": current_data["weather"][0]["description"],
        "icon": current_data["weather"][0]["icon"],
        "humidity": current_data["main"]["humidity"],
        "pressure": current_data["main"]["pressure"],
        "visibility": current_data.get("visibility", 0) / 1000,
        "wind_speed": current_data["wind"]["speed"],
        "sunrise": datetime.fromtimestamp(current_data["sys"]["sunrise"]).strftime("%H:%M"),
        "sunset": datetime.fromtimestamp(current_data["sys"]["sunset"]).strftime("%H:%M"),
        "city": current_data["name"],
        "country": current_data["sys"]["country"],
        "date": datetime.now().strftime("%d %b %Y"),
    }

    # 5-day forecast
    forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={API_KEY}"
    forecast_data = fetch_json(forecast_url)
    daily_forecast = OrderedDict()
    for item in forecast_data['list']:
        date_str = item['dt_txt'].split(" ")[0]
        temp = item['main']['temp']
        desc = item['weather'][0]["description"]
        icon = item['weather'][0]["icon"]

        if date_str not in daily_forecast:
            daily_forecast[date_str] = {"temps": [], "desc": desc, "icon": icon}
        daily_forecast[date_str]["temps"].append(temp)

    forecast_result = []
    count = 0
    for date_str, info in daily_forecast.items():
        if count >= 5:
            break
        day_name = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a")
        forecast_result.append({
            "day": day_name,
            "date": date_str,
            "min_temp": min(info["temps"]),
            "max_temp": max(info["temps"]),
            "description": info["desc"],
            "icon": info["icon"]
        })
        count += 1

    # Air Quality
    air_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    air_data = fetch_json(air_url)["list"][0]

    aqi_map = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
    air_quality = {
        "aqi": aqi_map.get(air_data["main"]["aqi"], "Unknown"),
        "pm2_5": air_data["components"]["pm2_5"],
        "pm10": air_data["components"]["pm10"],
        "co": air_data["components"]["co"],
        "no": air_data["components"]["no"],
        "no2": air_data["components"]["no2"],
        "o3": air_data["components"]["o3"],
        "so2": air_data["components"]["so2"],
        "nh3": air_data["components"]["nh3"]
    }

    return jsonify({
        "current": current,
        "forecast": forecast_result,
        "air_quality": air_quality
    })

if __name__ == "__main__":
    app.run(debug=True)