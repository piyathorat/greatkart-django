import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greatkart.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

user_name = "admin"
email = "piyathorat669@gmail.com"
password = "1234"
first_name = "Admin"
last_name = "User"

if not User.objects.filter(user_name=user_name).exists():
    User.objects.create_superuser(
        user_name=user_name,
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=password
    )
    print("Superuser created successfully")
else:
    print("Superuser already exists")
