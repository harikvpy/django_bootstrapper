# pylint: skip-file

from .base import *

DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'u8$#q#v3url(p^=++m$ru(0*g@amz@+&crsct70s_f2%6y8k#u'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Recaptcha test keys
#RECAPTCHA_PUBLIC_KEY = ''
#RECAPTCHA_PRIVATE_KEY = ''
