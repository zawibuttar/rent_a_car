# Generated manually — adds 'luxury_car' category choice

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0005_car_category_car_cars_car_categor_bda24c_idx'),
    ]

    operations = [
        migrations.AlterField(
            model_name='car',
            name='category',
            field=models.CharField(
                choices=[
                    ('car', 'Car'),
                    ('luxury_car', 'Luxury Car'),
                    ('loader', 'Loader'),
                    ('dumper', 'Dumper'),
                ],
                db_index=True,
                default='car',
                max_length=20,
            ),
        ),
    ]
