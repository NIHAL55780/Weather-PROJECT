from django.shortcuts import render
from django.conf import settings
import requests
import datetime

# Constants
KELVIN_TO_CELSIUS = 273.15
FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast?q={}&appid={}&units=metric'

def index(request):
    api_key = settings.OPENWEATHERMAP_API_KEY

    weather_data, daily_forecasts = None, None
    if request.method == 'POST':
        city = request.POST.get('city')
        weather_data, daily_forecasts = fetch_weather_and_forecast(city, api_key)

    context = {
        'weather_data': weather_data,
        'daily_forecasts': daily_forecasts,
    }

    return render(request, 'weather_app/index.html', context)

def fetch_weather_and_forecast(city, api_key):
    if not city:
        return None, None

    try:
        # Fetch forecast data
        forecast_response = requests.get(FORECAST_URL.format(city, api_key))
        forecast_response.raise_for_status()  # Raises HTTPError for bad responses
        forecast_data = forecast_response.json()

        # Get the first item in the list for current weather-like data
        current_weather = forecast_data['list'][0]

        weather = {
            'city': city,
            'temperature': round(current_weather['main']['temp'], 2),
            'description': current_weather['weather'][0]['description'],
            'icon': current_weather['weather'][0]['icon'],
            'wind_speed': current_weather['wind']['speed']
        }

        # Process daily forecast data by grouping entries into days
        daily_forecasts = []
        current_date = None
        day_data = {}

        for entry in forecast_data['list']:
            date = datetime.datetime.fromtimestamp(entry['dt']).date()
            if date != current_date:
                if day_data:
                    daily_forecasts.append(day_data)
                current_date = date
                day_data = {
                    'day': current_date.strftime('%A'),
                    'min_temp': round(entry['main']['temp_min'], 2),
                    'max_temp': round(entry['main']['temp_max'], 2),
                    'description': entry['weather'][0]['description'],
                    'icon': entry['weather'][0]['icon'],
                    'wind_speed': entry['wind']['speed']
                }
            else:
                # Update min and max temps for the day
                day_data['min_temp'] = min(day_data['min_temp'], round(entry['main']['temp_min'], 2))
                day_data['max_temp'] = max(day_data['max_temp'], round(entry['main']['temp_max'], 2))

        if day_data:
            daily_forecasts.append(day_data)

        return weather, daily_forecasts

    except requests.RequestException as e:
        print(f"Network error: {e}")
        return None, None
    except KeyError as e:
        print(f"Error processing data: {e}")
        print(f"Data received: {forecast_data}")
        return None, None
