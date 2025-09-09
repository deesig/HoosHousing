from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('listing_service', '0001_initial'),
    ]
    operations = [
        migrations.AddField(
            model_name='property',
            name='region',
            field=models.CharField(
                max_length=30,
                choices=[
                    ('central_grounds',     'Central Grounds'),
                    ('north_grounds',       'North Grounds'),
                    ('rugby_corridor',      'Rugby Road Corridor'),
                    ('university_corner',   'West Main / University Corner'),
                    ('jpa',                 'Jefferson Park Avenue'),
                    ('downtown_mall',       'Downtown Mall / City Center'),
                    ('barracks_road',       'Barracks Road Area'),
                    ('frys_spring',         'Fry\'s Spring'),
                    ('greenbrier',          'Greenbrier / Barracks West'),
                    ('pantops',             'Pantops & Meadow Creek'),
                    ('shadwell',            'Shadwell & Ivy'),
                ],
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name='property',
            name='proximity',
            field=models.CharField(
                max_length=20,
                choices=[
                        ('on_grounds',      'On-Grounds Housing'),
                        ('within_0_5_mi',   'Within 0.5 mi of Grounds'),
                        ('0_5_to_1_mi',     '0.5-1 mi from Grounds'),
                        ('1_to_2_mi',       '1-2 mi from Grounds'),
                        ('charlottesville', 'Charlottesville City'),
                        ('albemarle',       'Albemarle County'),
                ],
                blank=True,
            ),
        ),
    ]
