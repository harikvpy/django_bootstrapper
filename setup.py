#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'cookiecutter',
]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Hari Mahadevan",
    author_email='hari@smallpearl.com',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="BBDjango project bootstrapper that includes scrits to deploy the project to a Linux server",
    entry_points={
        'console_scripts': [
            'django_bootstrapper=django_bootstrapper.cli:main',
        ],
    },
    install_requires=requirements,
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='django_bootstrapper',
    name='django_bootstrapper',
    packages=find_packages(include=[
        'django_bootstrapper', 'django_bootstrapper.*'
        ]),
    package_data={
        'django_bootstrapper': [
            'data/*',
            'data/**/*',
            'project/*',
            'project/**/*'
        ]
    },
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/harikvpy/django_bootstrapper',
    version='0.1.0',
    zip_safe=False,
)
