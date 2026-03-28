
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0002_offer_address_user_address_user_latitude_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='offer',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='offer',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]
