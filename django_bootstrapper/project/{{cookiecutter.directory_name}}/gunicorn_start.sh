#!/bin/bash
# Makes the following assumptions:
#
#  1. All applications are located in a subfolder within /webapps
#  2. Each app gets a dedicated subfolder <appname> under /webapps. This will
#     be referred to as the app folder.
#  3. The group account 'webapps' exists and each app is to be executed
#     under the user account <appname>.
#  4. The app folder and all its recursive contents are owned by
#     <appname>:webapps.
#  5. The django app is stored under /webapps/<appname>/app folder.
#

cd /webapps/{{cookiecutter.directory_name}}
source ./prepare_env.sh

SOCKFILE=/webapps/{{cookiecutter.directory_name}}/nginx/gunicorn.sock  # we will communicte using this unix socket
USER={{cookiecutter.user_name}}     # the user to run as
GROUP={{cookiecutter.user_group}}   # the group to run as
NUM_WORKERS=3                       # how many worker processes should Gunicorn spawn
DJANGO_WSGI_MODULE=config.wsgi      # WSGI module name

echo "Starting {{cookiecutter.project_slug}} as `whoami`"

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec ./bin/gunicorn ${DJANGO_WSGI_MODULE}:application --name {{cookiecutter.project_slug}} --workers $NUM_WORKERS --user=$USER --group=$GROUP --bind=unix:$SOCKFILE --log-level=debug --log-file=-
