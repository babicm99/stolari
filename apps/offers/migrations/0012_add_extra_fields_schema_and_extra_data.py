# Generated manually for extra_fields_schema and extra_data

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0011_alter_elementsubtypeelements_element_discount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='elementsubtype',
            name='extra_fields_schema',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='JSON list of extra input definitions shown when this sub-type is selected (e.g. for Ladice).',
                verbose_name='Extra fields schema',
            ),
        ),
        migrations.AddField(
            model_name='element',
            name='extra_data',
            field=models.JSONField(blank=True, default=dict, verbose_name='Extra data'),
        ),
    ]
