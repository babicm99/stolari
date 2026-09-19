from django.db import migrations


class Migration(migrations.Migration):
    """Rename models without dropping data.

    Order matters so SQLite table names do not collide:
    offers_element → offers_offerelement
    offers_elementsubtype → offers_element
    offers_elementsubtypeelements → offers_elementsubtype
    """

    dependencies = [
        ('offers', '0017_remove_material_city_country'),
    ]

    operations = [
        migrations.RenameModel(old_name='Element', new_name='OfferElement'),
        migrations.RenameModel(old_name='ElementSubType', new_name='Element'),
        migrations.RenameModel(old_name='ElementSubTypeElements', new_name='ElementSubType'),
    ]
