
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0008_rating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offer',
            name='category',
            field=models.CharField(choices=[('cleaning', '🧹 Чистене'), ('groceries', '🛒 Пазаруване'), ('transport', '🚗 Транспорт'), ('tech', '💻 Помощ с техника'), ('gardening', '🌿 Помощ с градината'), ('cooking', '🍲 Готвене'), ('other', '✨ Друго')], max_length=50),
        ),
        migrations.AlterField(
            model_name='user',
            name='user_type',
            field=models.CharField(choices=[('worker', 'Доброволец/Работник'), ('needer', 'Търсещ помощ')], default='needer', max_length=10),
        ),
        migrations.CreateModel(
            name='WorkerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('skills', models.TextField(blank=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='worker_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
