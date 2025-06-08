import os
import sys
import logging

import django
import requests
import dotenv
from pathlib import Path
from geopy.geocoders import Nominatim

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather.settings')
django.setup()

dotenv.load_dotenv()

logger = logging.getLogger('city_time_logger')


class CityTimeClientError(Exception):
    """
    Ошибка взаимодействия с API получения времени по координатам
    """
    pass


class CityTimeClient:
    """
    Класс для получения текущего времени в заданном городе
    """

    def __init__(self):
        self.api_key = os.getenv("WORLD_TIME_API_KEY")
        self.api_url = os.getenv("WORLD_TIME_API_URL",)

    def get_time(self, city: str) -> str:
        """
        Получение локального времени указанного города

        :param city: Название города (например, 'London', 'Moscow')
        :return: строка времени в формате HH:MM
        """
        try:
            geolocator = Nominatim(user_agent="city_time_app")
            location = geolocator.geocode(city)

            if not location:
                logger.error(f"Город '{city}' не найден.")
                raise CityTimeClientError(f"Город '{city}' не найден.")

            lat = location.latitude
            lon = location.longitude

            response = requests.get(
                self.api_url,
                headers={"X-Api-Key": self.api_key},
                params={"lat": lat, "lon": lon}
            )

            if response.status_code != 200:
                logger.error(f"Ошибка API: {response.status_code} – {response.text}")
                raise CityTimeClientError(f"Ошибка API: {response.json()['message'] }")

            data = response.json()
            time_str = data.get("datetime", "").split()[1].rsplit(":", 1)[0]
            return time_str

        except requests.RequestException as e:
            logger.error(f"Ошибка соединения: {e}")
            raise CityTimeClientError("Ошибка соединения") from e



if __name__ == '__main__':
    client = CityTimeClient()
    print(client.get_time("London"))
    print(client.get_time("New York"))
    print(client.get_time("Moscow"))

