# Generated by Django 3.1.12 on 2025-05-30 21:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ProgramingoApp', '0002_userprofile_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='question_type',
            field=models.CharField(choices=[('multiple_choice', 'Multiple Choice'), ('type_in', 'Type-in')], default='multiple_choice', max_length=20),
        ),
    ]
