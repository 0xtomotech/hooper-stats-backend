import requests
from django.conf import settings

BASE_URL = "https://api.sportradar.com/nba/trial/v8/en"


def get_sportradar_data(endpoint):
    url = f"{BASE_URL}/{endpoint}?api_key={settings.SPORTRADAR_API_KEY}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
