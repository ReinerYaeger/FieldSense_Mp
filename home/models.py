from django.db import models
from django.contrib.gis.db import models as gis_model
from django.db.models import Avg
from django.db.models.functions import Coalesce


# Create your models here.
class SensorGroup(gis_model.Model):
    sensor_group_name = gis_model.CharField(primary_key=True, max_length=255)
    sensor_group_location = gis_model.PointField()
    creation_date = gis_model.DateTimeField(null=False)

    def __str__(self):
        return self.sensor_group_name.__str__()

    class Meta:
        db_table = 'sensor_group'
        verbose_name_plural = 'sensor_group'




class SensorCollectedData(gis_model.Model):
    sensor_group_name = gis_model.ForeignKey(SensorGroup, on_delete=gis_model.CASCADE)
    sensor_name = gis_model.CharField(max_length=10)
    sensor_data = gis_model.FloatField()
    sensor_date_time = gis_model.DateTimeField(null=False)

    def __str__(self):
        return self.sensor_group_name.__str__()

    class Meta:
        db_table = 'sensor_collected_data'
        verbose_name_plural = 'sensor_data'



class SensorGroupManager(gis_model.Manager):

    def get_sensor_avg_per_time(self, start_date, end_date):
        return self.annotate(
            sensor_avg=Coalesce(Avg('sensor_collected_data'), 0.000000)
        ).filter(
            sensorcollecteddata__sensor_date_time__gte=start_date,
            sensorcollecteddata__sensor_date_time__lte=end_date
        )

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    info = models.CharField(max_length=100, default='')
    price = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name
