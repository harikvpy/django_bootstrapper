===================
django-bootstrapper
===================

Django project bootstrapper that includes scripts to deploy the project to a Linux server.


How to use
----------

* Install the package from this repo using pip. Package will add the command `django_bootstrapper` to the path.
* Use the `django_bootstrapper` command to prep the remote system and generate a local django project template.
  You may use `django_bootstrapper --help` to see the various command line options supported by this command.
* If you're deploying a pure TLD site, that is one without a subdomain, be sure to update nginx/production.conf
  to include www.<domain-name> after <domain-name>.
