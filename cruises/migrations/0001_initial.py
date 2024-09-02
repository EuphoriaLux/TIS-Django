# Generated by Django 5.0.6 on 2024-09-02 08:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=120, unique=True)),
                ('description', models.TextField()),
                ('logo', models.ImageField(blank=True, null=True, upload_to='brand_logos/')),
                ('website', models.URLField(blank=True)),
                ('featured', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CabinType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('capacity', models.PositiveIntegerField()),
                ('deck', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CruiseCompany',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=120, unique=True)),
                ('description', models.TextField()),
                ('logo', models.ImageField(blank=True, null=True, upload_to='company_logos/')),
                ('website', models.URLField(blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CruiseType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField()),
                ('name_de', models.CharField(max_length=100)),
                ('name_fr', models.CharField(max_length=100)),
                ('description_de', models.TextField()),
                ('description_fr', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Port',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('country', models.CharField(max_length=100)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('description', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Cruise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, max_length=220, unique=True)),
                ('description', models.TextField()),
                ('image', models.ImageField(blank=True, null=True, upload_to='cruise_images/')),
                ('image_url', models.URLField(blank=True, max_length=1000, null=True)),
                ('flyer_pdf', models.FileField(blank=True, null=True, upload_to='cruise_flyers/')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cruises.cruisecompany')),
                ('cruise_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cruises.cruisetype')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CruiseSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('capacity', models.PositiveIntegerField()),
                ('is_summer_special', models.BooleanField(default=False, verbose_name='Summer Special')),
                ('summer_special_type', models.CharField(blank=True, choices=[('upgrade', 'Free Cabin Upgrade'), ('single_discount', 'Reduced Single Cabin Supplement')], max_length=50, null=True, verbose_name='Summer Special Type')),
                ('cruise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='cruises.cruise')),
            ],
            options={
                'unique_together': {('cruise', 'start_date', 'end_date')},
            },
        ),
        migrations.CreateModel(
            name='CabinTypeEquipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('cabin_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cruises.cabintype')),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cruises.equipment')),
            ],
            options={
                'unique_together': {('cabin_type', 'equipment')},
            },
        ),
        migrations.AddField(
            model_name='cabintype',
            name='equipment',
            field=models.ManyToManyField(through='cruises.CabinTypeEquipment', to='cruises.equipment'),
        ),
        migrations.CreateModel(
            name='Excursion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('duration', models.DurationField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('port', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cruises.port')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CruiseItinerary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('day', models.PositiveIntegerField()),
                ('port', models.CharField(max_length=100)),
                ('arrival_time', models.TimeField(blank=True, null=True)),
                ('departure_time', models.TimeField(blank=True, null=True)),
                ('description', models.TextField()),
                ('cruise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itineraries', to='cruises.cruise')),
            ],
            options={
                'ordering': ['cruise', 'day'],
                'unique_together': {('cruise', 'day')},
            },
        ),
        migrations.CreateModel(
            name='CruiseCabinPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('cabin_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cruises.cabintype')),
                ('cruise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cruises.cruise')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cruises.cruisesession')),
            ],
            options={
                'unique_together': {('cruise', 'cabin_type', 'session')},
            },
        ),
        migrations.CreateModel(
            name='CruiseExcursion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('available_date', models.DateField()),
                ('cruise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cruises.cruise')),
                ('excursion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cruises.excursion')),
            ],
            options={
                'unique_together': {('cruise', 'excursion', 'available_date')},
            },
        ),
    ]
