# Generated manually for UserCoefficientPreference

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('offers', '0013_element_ladice_explicit_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserCoefficientPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coefficient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='offers.coefficient')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='offers.coefficientgroup')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coefficient_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Coefficient Preference',
                'verbose_name_plural': 'User Coefficient Preferences',
                'unique_together': {('user', 'group')},
            },
        ),
    ]
