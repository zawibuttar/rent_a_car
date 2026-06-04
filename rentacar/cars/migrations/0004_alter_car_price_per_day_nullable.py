from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0003_car_rental_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='car',
            name='price_per_day',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
