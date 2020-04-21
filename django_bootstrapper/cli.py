"""Console script for django_bootstrapper."""
import os
import argparse
from getpass import getpass
from fabric import Connection, Config
from cookiecutter.main import cookiecutter

OS_PREREQS = [
    'git',
    'build-essential',
    'python3-dev',
    'python3-pip',
    'nginx',
    'postgresql',
    'libpq-dev',
]

PYTHON_PREREQS = [
    'virtualenv',
    'supervisor'
]

HOST = 'indus'
PORT = 64599


def install_os_package(c, package):
    with c:
        print('Installing OS package {0}'.format(package))
        c.sudo('apt-get -y -q install {0}'.format(package))


def install_python_package(c, package):
    with c:
        print('Installing Python package {0}'.format(package))
        c.sudo('pip3 install {0} -q --exists-action i'.format(package))


def install_prerequisites(c):
    '''Installs all the base OS required packages. These include
    Linux binaries as well as some global python packages.
    '''
    os_packages = ' '.join(OS_PREREQS)
    install_os_package(c, os_packages)

    py_packages = ' '.join(PYTHON_PREREQS)
    install_python_package(c, py_packages)


def install_certbot(conn):
    '''Install certbot ACME agent for switching site to HTTPS.
    Once the django app is installed and tested to be working, you can issue
    the following to make certbot to switch the site to HTTPS:
        $ sudo certbot --nginx
    '''
    print('1')
    conn.sudo('apt-get -y -q update')
    print('2')
    conn.sudo('apt-get -y -q install software-properties-common')
    print('3')
    conn.sudo('add-apt-repository -y universe')
    print('4')
    conn.sudo('add-apt-repository -y ppa:certbot/certbot')
    print('5')
    conn.sudo('apt-get -y -q update')
    print('6')
    conn.sudo('apt-get -y -q install certbot python-certbot-nginx')


def install_supervisor_service(conn):
    '''Supervisor when installed does not create the linux auto-start
    script. This function fixes that.
    '''
    result = conn.sudo('ls /etc/init.d/supervisord', hide=True, warn=True)
    if result.return_code != 0:

        data_folder = os.path.join(os.path.dirname(__file__), 'data')
        conn.put(os.path.join(data_folder, 'supervisord'), '/tmp')
        conn.put(os.path.join(data_folder, 'supervisord.conf'), '/tmp')
        conn.sudo('cp /tmp/supervisord.conf /etc')
        conn.sudo('cp /tmp/supervisord /etc/init.d')
        conn.sudo('update-rc.d supervisord defaults')
        # start supervisord, which requires interactive login
        # So we login as root from within sudo
        conn.sudo("service supervisord start")


def create_group(c, group):
    '''Creates the user group 'group'.'''
    result = c.sudo('getent group {0}'.format(group), hide=True, warn=True)
    if result.return_code != 0:
        print("Creating group '{0}' for automation accounts...".format(group))
        c.sudo('groupadd --system {0}'.format(group), hide=True)
    else:
        print("Group '{0}' already exists".format(group))


def create_user(c, user, group):
    '''Creates the user account, with the user's home directory set 
    to {group}/{user}'''
    result = c.sudo('grep "{0}:" /etc/passwd'.format(user), hide=True, warn=True)
    if result.return_code != 0:
        print("Creating automation user account '{0}'...".format(user))
        c.sudo('useradd --system --gid {0} --shell /bin/bash --home /{0}/{1} {1}'.format(group, user), hide=True)
    else:
        print("User '{0}' already exists".format(user))


def create_automation_account(c, options):
    '''Creates the automation user group & account.'''
    USER = options.app
    GROUP = 'webapps'
    HOME_FOLDER = '/{0}/{1}'.format(GROUP, USER)
    c.sudo('mkdir -p {0}'.format(HOME_FOLDER), hide=True)
    # create group if it doesn't exist
    create_group(c, GROUP)
    create_user(c, USER, GROUP)
    # change ownership of the automation account home folder to the
    # user just created
    # change ownership of the app folder to the newly created user account
    print("Setting ownership of {0} and its descendents to {1}:{2}...".format(
        HOME_FOLDER, USER, GROUP))
    c.sudo('chown -R {0}:{1} {2}'.format(USER, GROUP, HOME_FOLDER), hide=True)
    # give group execution rights in the folder;
    # TODO: is this necessary? why?
    c.sudo('chmod g+x {0}'.format(HOME_FOLDER), hide=True)


def create_virtualenv(conn, options):
    print('Creating virtual environment...')
    conn.sudo('sudo -i -u {0} virtualenv -p python3 .'.format(options.app))


def upgrade_pip(conn, options):
    print('Upgrading pip...')
    conn.sudo("sudo -i -u {0} bash -c 'source ./bin/activate && pip install -U pip'".format(options.app), hide=True)


def create_folders(conn, options):
    '''Creates folder such as nginx, logs, static & media'''
    print('Creating standard folders...')
    conn.sudo("sudo -i -u {0} bash -c 'mkdir logs nginx static media'".format(options.app), hide=True, warn=True)


def create_unix_socket(conn, options):
    '''Create the unix socket through which nginx can forward
    HTTP requests to Gunicorn WSGI'''
    print('Creating UNIX socket for gunicorn...')
    py_cmd = r"""python -c "import socket as s; sock = s.socket(s.AF_UNIX); sock.bind(\'./nginx/gunicorn.sock\')" """
    # The '$' before 'source ./bin/activate...' is bash specific way of 
    # triggering special handling for the string literals that follow it.
    # With the leading '$', bash allows the literal to have backslash
    # escape character to insert special characters such as embedded quotes,
    # newlines, carriate returns, tabs, etc.
    # Without it we cannot embedd the single quote in the statement:
    # sock.bind('nginx/gunicorn.sock')
    conn.sudo("sudo -i -u {0} bash -c $'source ./bin/activate; {1}'".format(options.app, py_cmd), hide=True)


def generate_secret_key(conn, options):
    '''Generate Django secret key'''
    print("Generating Django secrety key...")
    key = conn.sudo("openssl rand -base64 48", hide=True).stdout.split('\n')[0]
    conn.sudo("sudo -i -u {0} bash -c $'echo {1} > ./.django_secret_key'".format(options.app, key), hide=True)


def generate_db_password(conn, options):
    '''Generate random string to be used as DB password'''
    print("Creating secure password for database role...")
    password = conn.sudo("openssl rand -base64 32", hide=True).stdout.split('\n')[0]
    conn.sudo("sudo -i -u {0} bash -c $'echo {1} > ./.django_db_password'".format(options.app, password), hide=True)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', help="Remote host IP address or hostname")
    parser.add_argument('app', help="Name of the app, usually a single word without any dash or underscore")
    parser.add_argument('domain', help="Domain name, like example.com. To specify a subdomain, specify the full subdomain.")
    parser.add_argument('--port', type=int, help="Host SSH port, if it is different from the standard 22.", default=22)
    parser.add_argument('--password', help="Sudo password. If not specified, you'll be prompted for one.")
    parser.add_argument('--no_input', type=bool, help="Skip prompting for input while generating project template.", default=False)
    parser.add_argument('--overwrite_if_exists', type=bool, help='If the project template target directory exists, overwrite its contents.', default=False)
    parser.add_argument('--output_dir', help='Output directory where the generated project bootstrap code is to be saved.', default='.')

    return parser.parse_args()

def main():
    '''
    To be invoked with the arguments:
        -h --host Host IP address or resolvable name
        -p --port Host SSH port, if it's different from the standard 22
        -a --appname Name of the app, usually a single word without any 
                dash or underscorec
        -d --domain Domain name, typically of the format example.com. If
                the app is for a subdomain, specify the full subdomain.
    '''
    options = parse_arguments()

    # Get sudo password from environment
    if not options.password:
        options.password = getpass('Enter sudo password: ')

    if not options.password:
        print('Sudo password is required.')
        exit(1)

    try:
        config = Config(overrides={'sudo': {'password': options.password}})
        conn = Connection(options.host, port=options.port, config=config)

        # install_prerequisites(conn)
        # install_certbot(conn)
        # install_supervisor_service(conn)

        # create_automation_account(conn, options)

        # create_virtualenv(conn, options)
        # upgrade_pip(conn, options)
        # create_folders(conn, options)
        # create_unix_socket(conn, options)

        # generate_secret_key(conn, options)
        # generate_db_password(conn, options)

        # print(
        #     "Remote prepped for deployment.\n"
        #         "Now going on to create project template."
        # )

        slug = options.app.lower().replace(' ', '_')
        project_folder = os.path.join(os.path.dirname(__file__), 'project')
        cookiecutter(
            project_folder,
            extra_context={
                'app_name': options.app,
                'project_slug': slug,
                'directory_name': slug,
                'user_group': 'webapps',
                'user_name': slug,
                'domain': options.domain,
                'host': options.host,
                'port': options.port
            },
            overwrite_if_exists=options.overwrite_if_exists,
            no_input=options.no_input,
            output_dir=options.output_dir
        )

        print("Done!\n"
            "Folder {0} has the project template.\n"
            "You may run the following (in sequence) from the project folder\n:"
            "to build & depoly the project to the remote server:\n"
            "    0. git init && git add --all && git commit -a -m \"initial commit\" \n"
            "    1. npm i\n"
            "    2. gulp\n"
            "    3. fab deploy\n".format(slug)
        )

    except Exception as ex:
        print('Exception: {0}'.format(str(ex)))
        exit(1)

    exit(0)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
