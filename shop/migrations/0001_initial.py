# shop/migrations/0001_initial.py

import django.db.models.deletion
from django.db import migrations, models
from django.conf import settings

class Migration(migrations.Migration):

    # Это первая миграция
    initial = True 

    dependencies = [
        # Обязательная зависимость от модели пользователя
        migrations.swappable_dependency(settings.AUTH_USER_MODEL), 
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            # В `fields` достаточно указать только поле `user`,
            # так как именно оно создает зависимость.
            # Все остальные поля будут добавлены на следующем шаге.
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                # Добавляем user, чтобы миграция знала о OneToOneField
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='customer', to=settings.AUTH_USER_MODEL)),
                # Вам не нужно перечислять все остальные поля,
                # потому что они уже есть в вашей физической таблице.
            ],
            options={
                'db_table': 'customer',
                'managed': True,
            },
        ),
    ]