from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0016_usermaterialpreference'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='material',
            name='city',
        ),
        migrations.RemoveField(
            model_name='material',
            name='country',
        ),
    ]
