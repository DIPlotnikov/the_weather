import os
import sys
from pathlib import Path

import django
import requests
import dotenv
import logging

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather.settings')
django.setup()

from external_api.decorators import cached_data

logger = logging.getLogger('openweathermap_logger')
dotenv.load_dotenv()

from django.core.cache import cache


class OpenWeatherClientError(Exception):
    """
    Ошибка взаимодействия с API OpenWeather
    """
    pass


class OpenWeatherClient:
    """
    Класс для взаимодействия с API OpenWeather
    """

    def __init__(self):
        self.base_url = os.getenv("OPENWEATHER_BASE_URL")
        self.api_key = os.getenv("OPENWEATHER_API_KEY")

    @cached_data("current_weather")
    def get_current_weather(self, city: str) -> float:
        """
        Получение текущей погоды указанного города

        :param city:
        :return: float
        """
        try:
            response = requests.get(
                f"{self.base_url}/weather",
                params={"q": city, "appid": self.api_key, "units": "metric"}
            )
            data = response.json()

            if response.status_code != 200:
                logger.error(f"Ошибка API: {response.text}")
                raise OpenWeatherClientError(f"Ошибка API: {response.json()['message']}")

            temperature = data["main"]["temp"]

            return temperature

        except requests.RequestException as e:
            logger.error(e)
            raise OpenWeatherClientError("Ошибка соединения") from e

    @cached_data("forecast")
    def get_forecast(self, city: str) -> dict:
        """
        Получение прогноза погоды на указанный город на 30 дней

        :param city:
        :return: dict
        """
        try:
            response = requests.get(
                f"{self.base_url}/forecast",
                params={"q": city, "appid": self.api_key, "units": "metric"}
            )
            data = response.json()
            logger.info(data)

            if response.status_code != 200:
                logger.error(f"Ошибка API: {response.text}")
                raise OpenWeatherClientError(f"Ошибка API: {response.json()['message']}")

            forecast_list = data["list"]
            forecast = {day['dt_txt'].split()[0]: {
                'temp_max': day['main']['temp_max'],
                'temp_min': day['main']['temp_min']
            }
                for day in forecast_list
            }

            return forecast

        except requests.RequestException as e:
            logger.error(e)
            raise OpenWeatherClientError("Ошибка соединения") from e


if __name__ == '__main__':
    client = OpenWeatherClient()
    print(client.get_current_weather("London"))
    print(client.get_forecast("Moscow"))
