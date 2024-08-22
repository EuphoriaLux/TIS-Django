# Generated by Django 5.0.6 on 2024-08-14 08:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cruises', '0003_brand_delete_destination_delete_destinationcompany'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='cruise_category',
        ),
        migrations.RemoveField(
            model_name='cruisecategory',
            name='cruise',
        ),
        migrations.RemoveField(
            model_name='cruisecategory',
            name='price',
        ),
        migrations.CreateModel(
            name='CruiseCategoryPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cruises.cruisecategory')),
                ('cruise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cruises.cruise')),
            ],
        ),
        migrations.AddField(
            model_name='booking',
            name='cruise_category_price',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='cruises.cruisecategoryprice'),
        ),
        migrations.AddField(
            model_name='cruise',
            name='categories',
            field=models.ManyToManyField(through='cruises.CruiseCategoryPrice', to='cruises.cruisecategory'),
        ),
    ]