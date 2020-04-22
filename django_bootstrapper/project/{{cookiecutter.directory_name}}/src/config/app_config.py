'''
App configuration that is read by base.py and appended to it's settings.
This will allow base.py to remain untouched such that it can be regenerated
from the original project template, if necessary.
'''
import os

# This is already defined in base.py. But we can redefine it as long as it
# results in the same value.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# List site's private apps along with additional thirdparty apps. 
# These will be added to the settings.INSTALLED_APPS after django's
# standard apps.
SITE_APPS = [
    'public'
]
