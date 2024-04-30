# Generated by Django 5.0.2 on 2024-04-19 09:40

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accountapp', '0002_initial'),
        ('orderapp', '0003_delete_payment'),
        ('userapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
                ('price', models.FloatField()),
                ('payed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_deleted', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accountapp.account')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='orderapp.orderdetails')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userapp.userprofile')),
            ],
        ),
    ]