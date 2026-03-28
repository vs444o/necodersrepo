
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0006_application_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='offer',
            name='city',
            field=models.CharField(default='Sofia', max_length=100),
            preserve_default=False,
        ),
    ]
