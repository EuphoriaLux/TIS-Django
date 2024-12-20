# Generated by Django 5.0.6 on 2024-11-19 20:53

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cruises', '0001_initial'),
        ('quotes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled'), ('completed', 'Completed'), ('refunded', 'Refunded')], default='pending', max_length=20)),
                ('payment_status', models.CharField(choices=[('unpaid', 'Unpaid'), ('partially_paid', 'Partially Paid'), ('paid', 'Fully Paid'), ('refunded', 'Refunded')], default='unpaid', max_length=20)),
                ('base_price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('amount_paid', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('discount_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('special_requests', models.TextField(blank=True)),
                ('internal_notes', models.TextField(blank=True)),
                ('cancellation_reason', models.TextField(blank=True)),
                ('confirmation_number', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('applied_promotion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bookings', to='cruises.promotion')),
                ('cabin_category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bookings', to='cruises.cabincategory')),
                ('cruise_session', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bookings', to='cruises.cruisesession')),
                ('quote', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='booking', to='quotes.quote')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bookings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BookingAdditionalService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('service_type', models.CharField(choices=[('transfer', 'Transfer'), ('insurance', 'Insurance'), ('beverage', 'Beverage Package'), ('dining', 'Dining Package'), ('internet', 'Internet Package'), ('spa', 'Spa Package'), ('other', 'Other')], default='other', max_length=20)),
                ('service_name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('is_per_person', models.BooleanField(default=False)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='additional_services', to='bookings.booking')),
            ],
            options={
                'ordering': ['booking', 'service_type', 'service_name'],
            },
        ),
        migrations.CreateModel(
            name='Passenger',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, validators=[django.core.validators.EmailValidator()])),
                ('phone', models.CharField(max_length=20)),
                ('date_of_birth', models.DateField()),
                ('nationality', models.CharField(max_length=100)),
                ('passport_number', models.CharField(max_length=50)),
                ('passport_expiry_date', models.DateField()),
                ('passport_issued_country', models.CharField(max_length=100)),
                ('dietary_requirements', models.TextField(blank=True)),
                ('medical_requirements', models.TextField(blank=True)),
                ('is_lead_passenger', models.BooleanField(default=False)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='passengers', to='bookings.booking')),
            ],
            options={
                'ordering': ['-is_lead_passenger', 'last_name', 'first_name'],
            },
        ),
        migrations.CreateModel(
            name='ExcursionBooking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('special_requirements', models.TextField(blank=True)),
                ('pickup_location', models.CharField(blank=True, max_length=200)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='excursion_bookings', to='bookings.booking')),
                ('cruise_excursion', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bookings', to='cruises.cruiseexcursion')),
                ('passengers', models.ManyToManyField(related_name='booked_excursions', to='bookings.passenger')),
            ],
            options={
                'ordering': ['booking', 'cruise_excursion'],
            },
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['status', 'payment_status'], name='bookings_bo_status_92d418_idx'),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['user', 'status'], name='bookings_bo_user_id_69a5d5_idx'),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['cruise_session', 'cabin_category'], name='bookings_bo_cruise__1168f4_idx'),
        ),
        migrations.AddIndex(
            model_name='passenger',
            index=models.Index(fields=['booking', 'is_lead_passenger'], name='bookings_pa_booking_bab741_idx'),
        ),
        migrations.AddIndex(
            model_name='passenger',
            index=models.Index(fields=['passport_number'], name='bookings_pa_passpor_46fe9c_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='excursionbooking',
            unique_together={('booking', 'cruise_excursion')},
        ),
    ]
