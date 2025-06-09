from django.db import models


class HandForecasts(models.Model):
    """
    Модель для хранения прогнозов, сохраненных вручную
    """
    city = models.CharField(max_length=100)
    date = models.DateField()
    min_temperature = models.FloatField()
    max_temperature = models.FloatField()

    class Meta:
        unique_together = ('city', 'date')
