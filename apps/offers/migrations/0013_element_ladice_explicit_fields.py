# Replace extra_data with explicit Ladice fields on Element

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0012_add_extra_fields_schema_and_extra_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='element',
            name='dubina_ladice',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='DUBINA LADICE'),
        ),
        migrations.AddField(
            model_name='element',
            name='visina_fronte_1',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='VISINA 1. FRONTE'),
        ),
        migrations.AddField(
            model_name='element',
            name='visina_fronte_2',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='VISINA 2. FRONTE'),
        ),
        migrations.AddField(
            model_name='element',
            name='visina_fronte_3',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='VISINA 3. FRONTE'),
        ),
        migrations.AddField(
            model_name='element',
            name='visina_fronte_4',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='VISINA 4. FRONTE'),
        ),
        migrations.RemoveField(
            model_name='element',
            name='extra_data',
        ),
    ]
