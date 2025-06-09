import pytest

pytestmark = pytest.mark.django_db
import pytest
from rest_framework import status
from unittest.mock import patch
from api.models import HandForecasts


import pytest


@pytest.mark.django_db
class TestCurrentWeatherView:

    url = "/api/weather/current"

    def test_success(self, api_client, user):
        api_client.force_authenticate(user=user)

        with patch("external_api.openweathermap_client.OpenWeatherClient.get_current_weather") as mock_weather, \
             patch("external_api.worldtime_client.CityTimeClient.get_time") as mock_time:

            mock_weather.return_value = 21.5
            mock_time.return_value = "2025-06-07 14:00:00"

            response = api_client.get(self.url, {"city": "Moscow"})

            assert response.status_code == status.HTTP_200_OK
            assert response.data["temperature"] == 21.5
            assert response.data["local_time"] == "2025-06-07 14:00:00"

    def test_missing_city_param(self, api_client, user):
        api_client.force_authenticate(user=user)

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "city" in response.data

    def test_openweather_client_error(self, api_client, user):
        api_client.force_authenticate(user=user)

        with patch("external_api.openweathermap_client.OpenWeatherClient.get_current_weather") as mock_weather:
            mock_weather.side_effect = Exception("City not found")

            response = api_client.get(self.url, {"city": "Nowhere"})

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "error" in response.data

    def test_citytime_client_error(self, api_client, user):
        api_client.force_authenticate(user=user)

        with patch("external_api.openweathermap_client.OpenWeatherClient.get_current_weather") as mock_weather, \
             patch("external_api.worldtime_client.CityTimeClient.get_time") as mock_time:

            mock_weather.return_value = 22.0
            mock_time.side_effect = Exception("Time not found")

            response = api_client.get(self.url, {"city": "Tokyo"})

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "error" in response.data



@pytest.mark.django_db
class TestForecastView:
    forecast_url = "/api/weather/forecast"

    def test_get_forecast_from_db(self, api_client, user):
        api_client.force_authenticate(user=user)

        # Предварительно создаём объект прогноза
        HandForecasts.objects.create(
            city="Moscow",
            date="2025-06-10",
            min_temperature=12.3,
            max_temperature=21.7
        )

        response = api_client.get(TestForecastView.forecast_url, {"city": "Moscow", "date": "10.06.2025"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["min_temperature"] == 12.3
        assert response.data["max_temperature"] == 21.7

    def test_get_forecast_from_external_api(self, api_client, user):
        api_client.force_authenticate(user=user)

        mock_forecast = {
            "date": "2025-06-10",
            "min_temperature": 10.0,
            "max_temperature": 20.0
        }

        with patch("external_api.openweathermap_client.OpenWeatherClient.get_forecast_by_date") as mock_method:
            mock_method.return_value = mock_forecast

            response = api_client.get(TestForecastView.forecast_url, {"city": "Moscow", "date": "10.06.2025"})

            assert response.status_code == status.HTTP_200_OK
            assert response.data == mock_forecast

    def test_post_forecast_create(self, api_client, user):
        api_client.force_authenticate(user=user)

        data = {
            "city": "Paris",
            "date": "10.06.2025",
            "min_temperature": 13.5,
            "max_temperature": 22.2
        }

        response = api_client.post(TestForecastView.forecast_url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert HandForecasts.objects.filter(city="Paris", date="2025-06-10").exists()

    def test_post_forecast_update(self, api_client, user):
        api_client.force_authenticate(user=user)

        HandForecasts.objects.create(
            city="Berlin",
            date="2025-06-10",
            min_temperature=10,
            max_temperature=18
        )

        updated_data = {
            "city": "Berlin",
            "date": "10.06.2025",
            "min_temperature": 11.0,
            "max_temperature": 19.5
        }

        response = api_client.post(TestForecastView.forecast_url, updated_data)

        assert response.status_code == status.HTTP_200_OK
        forecast = HandForecasts.objects.get(city="Berlin", date="2025-06-10")
        assert forecast.min_temperature == 11.0
        assert forecast.max_temperature == 19.5
