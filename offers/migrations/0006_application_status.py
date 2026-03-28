
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0005_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending', max_length=20),
        ),
    ]
