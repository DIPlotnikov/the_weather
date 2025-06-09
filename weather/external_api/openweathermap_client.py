import os
import sys
from datetime import datetime
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
                'min_temperature': day['main']['temp_min'],
                'max_temperature': day['main']['temp_max'],
            }
                for day in forecast_list
            }

            return forecast

        except requests.RequestException as e:
            logger.error(e)
            raise OpenWeatherClientError("Ошибка соединения") from e

    def get_forecast_by_date(self, city: str, date: datetime) -> dict:
        """
        Получение прогноза погоды на указанный город на указанную дату

        :param city: str
        :param date: дата в формате dd.mm.yyyy

        :return: dict: {
                        "min_temperature": 11.1,
                        "max_temperature": 24.5
                        }
        """
        forecast_data = self.get_forecast(city)
        return forecast_data.get(str(date))


if __name__ == '__main__':
    client = OpenWeatherClient()
    print(client.get_current_weather("London"))
    print(client.get_forecast("Moscow"))
    print(client.get_forecast_by_date("Moscow", "2025-06-10"))
