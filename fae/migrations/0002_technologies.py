# Generated by Django 4.2.3 on 2023-07-13 06:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fae', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Technologies',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('application_name', models.CharField(max_length=50)),
                ('block_names', models.CharField(max_length=100)),
            ],
        ),
    ]