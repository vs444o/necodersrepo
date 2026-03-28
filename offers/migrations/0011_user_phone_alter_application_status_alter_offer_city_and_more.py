
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0010_merge_20260327_1834'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='application',
            name='status',
            field=models.CharField(choices=[('pending', 'Изчакване'), ('accepted', 'Прието'), ('rejected', 'Отхвърлено')], default='pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='offer',
            name='city',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='offer',
            name='offer_type',
            field=models.CharField(choices=[('paid', 'Платена'), ('volunteer', 'Доброволна')], max_length=20),
        ),
        migrations.AlterField(
            model_name='offer',
            name='status',
            field=models.CharField(choices=[('waiting', 'Чака отговор'), ('accepted', 'Прието'), ('completed', 'Завършено')], db_index=True, default='waiting', max_length=20),
        ),
    ]
