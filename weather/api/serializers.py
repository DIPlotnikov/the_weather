import os
from datetime import datetime

from django.utils import timezone
from rest_framework import serializers

from api.models import HandForecasts


class CurrentWeatherSerializer(serializers.Serializer):
    city = serializers.CharField()

    def validate_city(self, value):
        if not value:
            raise serializers.ValidationError("Обязательное поле: city")
        return value


class ForecastGetSerializer(serializers.Serializer):
    city = serializers.CharField()
    date = serializers.DateField(
        input_formats=["%d.%m.%Y"]
    )

    def validate_city(self, value):
        if not value:
            raise serializers.ValidationError("Обязательное поле: city")
        return value

    def validate_date(self, value):
        if not value:
            raise serializers.ValidationError("Обязательное поле: date")
        if value < timezone.now().date():
            raise serializers.ValidationError("Дата не может быть в прошлом")
        delta_days = int(os.getenv("DELTA_DAYS", 10))
        if value > timezone.now().date() + timezone.timedelta(days=delta_days):
            raise serializers.ValidationError(f"Дата не может быть больше {delta_days} дней в будущем")
        return value

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["date"] = str(instance.date.strftime("%Y-%m-%d"))  # преобразуем в нужный формат
        return ret


class HandForecastUpdateSerializer(serializers.Serializer):
    city = serializers.CharField(required=True, max_length=100)
    date = serializers.CharField(required=True)
    min_temperature = serializers.FloatField(required=True)
    max_temperature = serializers.FloatField(required=True)

    def validate_date(self, value):
        """Валидация даты"""
        try:
            value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise serializers.ValidationError("Неверный формат даты. Используйте dd.MM.yyyy")
        # Проверка прошлого
        if value < timezone.now().date():
            raise serializers.ValidationError("Дата не может быть в прошлом")

        # Проверка будущего (макс +10 дней)
        delta_days = int(os.getenv("DELTA_DAYS", 10))
        max_date = timezone.now().date() + timezone.timedelta(days=delta_days)

        if value > max_date:
            raise serializers.ValidationError(
                f"Дата не может быть больше {delta_days} дней в будущем"
            )

        return value

    def validate(self, data):
        """Валидация взаимосвязи полей"""
        # Проверка температур
        min_temp = data.get('min_temperature')
        max_temp = data.get('max_temperature')

        if min_temp is not None and max_temp is not None and min_temp > max_temp:
            raise serializers.ValidationError({
                "min_temperature": "Минимальная температура не может быть больше максимальной",
                "max_temperature": "Максимальная температура не может быть меньше минимальной"
            })

        return data

