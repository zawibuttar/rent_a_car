# Generated manually for multi-type rentals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0002_alter_car_brand_alter_car_car_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='car',
            name='rent_hourly',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='car',
            name='rent_daily',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='car',
            name='rent_weekly',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='car',
            name='rent_monthly',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='car',
            name='price_per_hour',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='car',
            name='price_per_week',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='car',
            name='price_per_month',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
