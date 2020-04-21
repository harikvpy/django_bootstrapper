APPFOLDERPATH=/{{ cookiecutter.user_group }}/{{ cookiecutter.directory_name }}
DJANGODIR=$APPFOLDERPATH/app

export DJANGO_SETTINGS_MODULE=config.production # settings file for the app
export PYTHONPATH=$DJANGODIR:$PYTHONPATH
export DJANGO_SECRET_KEY=`cat ./.django_secret_key`
export DJANGO_DB_PASSWORD=`cat ./.django_db_password`

source ./bin/activate
cd $APPFOLDERPATH
