
## First statrt

1. create venv

        virtualenv -p python3 venv
        source venv/bin/activate
        pip3 install django
        pip3 install Pillow
        pip3 install django-crispy-forms
    
2. make migrations

        cd simple_votings
        python3 manage.py migrate
    
## Other starts second and more

  
        source venv/bin/activate

         cd simple_votings
  
         python manage.py makemigrations
         python manage.py migrate

        python manage.py runserver


## If nothing works
Delete db.sqlite3, than delete directory migrations in the simple_votings_app and run commands

    python manage.py makemigrations simple_votings_app
    python manage.py migrate
