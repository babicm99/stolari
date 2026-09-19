from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('offers', '0015_distributor_material_element_material'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserMaterialPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('country', models.CharField(blank=True, default='', max_length=100)),
                ('cities', models.JSONField(blank=True, default=list)),
                ('distributors', models.ManyToManyField(
                    blank=True,
                    related_name='user_preferences',
                    to='offers.distributor',
                )),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='material_preference',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'User Material Preference',
                'verbose_name_plural': 'User Material Preferences',
            },
        ),
    ]
