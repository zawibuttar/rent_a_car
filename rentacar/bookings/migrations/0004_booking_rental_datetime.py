# Generated manually for multi-type rentals

from datetime import datetime, time

from django.db import migrations, models
from django.utils import timezone


def forwards_copy_dates(apps, schema_editor):
    Booking = apps.get_model('bookings', 'Booking')
    for booking in Booking.objects.all():
        start_date = booking.start_date
        end_date = booking.end_date
        if start_date and end_date:
            booking.rental_type = 'daily'
            booking.start_at = timezone.make_aware(
                datetime.combine(start_date, time.min)
            )
            booking.end_at = timezone.make_aware(
                datetime.combine(end_date, time(23, 59, 59))
            )
            booking.save(update_fields=['rental_type', 'start_at', 'end_at'])


def backwards_copy_dates(apps, schema_editor):
    Booking = apps.get_model('bookings', 'Booking')
    for booking in Booking.objects.all():
        if booking.start_at and booking.end_at:
            local_start = timezone.localtime(booking.start_at)
            local_end = timezone.localtime(booking.end_at)
            booking.start_date = local_start.date()
            booking.end_date = local_end.date()
            booking.save(update_fields=['start_date', 'end_date'])


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_alter_booking_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='rental_type',
            field=models.CharField(
                choices=[
                    ('hourly', 'Hourly'),
                    ('daily', 'Daily'),
                    ('weekly', 'Weekly'),
                    ('monthly', 'Monthly'),
                ],
                default='daily',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='start_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='end_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(forwards_copy_dates, backwards_copy_dates),
        migrations.RemoveField(
            model_name='booking',
            name='start_date',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='end_date',
        ),
        migrations.AlterField(
            model_name='booking',
            name='start_at',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='booking',
            name='end_at',
            field=models.DateTimeField(),
        ),
    ]
