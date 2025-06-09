from datetime import datetime

from api.models import HandForecasts


class HandForecastsHandler:
    """
    Класс для работы с прогнозами
    """

    @staticmethod
    def get_forecast(city: str, date: datetime) -> dict | None:
        """
        Метод для получения прогноза погоды из бд
        :param city:
        :param date:
        :return: dict or None
        """
        forcast = HandForecasts.objects.filter(city=city, date=date).first()
        if forcast:
            formated_data = {
                            "min_temperature": forcast.min_temperature,
                            "max_temperature": forcast.max_temperature}
            return formated_data

        return None
