pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('Superuser', 'superuser@gmail.com', '123456')" | python manage.py shell