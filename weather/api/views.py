from datetime import datetime

from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.handlers import HandForecastsHandler
from api.models import HandForecasts
from api.serializers import CurrentWeatherSerializer, ForecastGetSerializer, HandForecastUpdateSerializer
from external_api.openweathermap_client import OpenWeatherClient, OpenWeatherClientError
from external_api.worldtime_client import CityTimeClient, CityTimeClientError


class CurrentWeatherView(APIView):
    """
    Представление для получения текущей погоды
    """

    # permission_classes = [AllowAny]

    def get(self, request):

        serializer = CurrentWeatherSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        city = serializer.validated_data["city"]
        try:
            temperature = OpenWeatherClient().get_current_weather(city)
            local_time = CityTimeClient().get_time(city)

            return Response({
                "temperature": temperature,
                "local_time": local_time
            })

        except OpenWeatherClientError as e:
            return Response(
                {"error": f"Ошибка работы с API OpenWeather - {e}"},
                status=status.HTTP_404_NOT_FOUND
            )
        except CityTimeClientError as e:
            return Response(
                {"error": f"Ошибка работы с API WorldTime - {e}"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ForecastView(APIView):
    # permission_classes = [AllowAny]

    def get(self, request):
        """
        Метод для получения прогноза погоды на указанную дату
        """
        serializer = ForecastGetSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        city = serializer.validated_data["city"]
        date = serializer.validated_data["date"]

        try:
            forecast_from_db = HandForecastsHandler.get_forecast(city, date)
            if forecast_from_db:
                return Response(forecast_from_db)

            forecast = OpenWeatherClient().get_forecast_by_date(city, date)
            return Response(forecast)

        except OpenWeatherClientError as e:
            return Response(
                {"error": f"Ошибка работы с API OpenWeather - {e}"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """
        Метод для обновления прогноза погоды на указанную дату вручную
        """
        serializer = HandForecastUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            validated_data = serializer.validated_data
            forecast, created = HandForecasts.objects.update_or_create(
                city=validated_data['city'],
                date=validated_data['date'],
                defaults={
                    'min_temperature': validated_data['min_temperature'],
                    'max_temperature': validated_data['max_temperature']
                }
            )

            return Response(
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
