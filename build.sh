pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(correo='superuser@gmail.com', password='123456', nombre_usuario='Superuser')" | python manage.py shell