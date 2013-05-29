#!/usr/bin/env python
import os
import sys
import logging

from coverage import coverage

from django.conf import settings

from oscar.defaults import OSCAR_SETTINGS
from oscar import OSCAR_MAIN_TEMPLATE_DIR, OSCAR_CORE_APPS


location = lambda x: os.path.join(
    os.path.dirname(os.path.realpath(__file__)), x)


def configure():
    if settings.configured:
        return

    pairs = dict(
        RECURLY_SUBDOMAIN = os.environ.get('RECURLY_SUBDOMAIN'),
        RECURLY_API_KEY = os.environ.get('RECURLY_API_KEY'),
        RECURLY_PRIVATE_KEY = os.environ.get('RECURLY_PRIVATE_KEY'),
        RECURLY_DEFAULT_CURRENCY = os.environ.get('RECURLY_DEFAULT_CURRENCY', 'USD'),
        USE_TZ = True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        MEDIA_ROOT=location('public/media'),
        MEDIA_URL='/media/',
        STATIC_URL='/static/',
        STATICFILES_DIRS=(location('static/'),),
        STATIC_ROOT=location('public'),
        STATICFILES_FINDERS=(
            'django.contrib.staticfiles.finders.FileSystemFinder',
            'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        ),
        TEMPLATE_LOADERS=(
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ),
        MIDDLEWARE_CLASSES=(
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'oscar.apps.basket.middleware.BasketMiddleware',
        ),
        ROOT_URLCONF='sandbox.sandbox.urls',
        TEMPLATE_DIRS=(
            location('templates'),
            os.path.join(OSCAR_MAIN_TEMPLATE_DIR, 'templates'),
            OSCAR_MAIN_TEMPLATE_DIR,
        ),
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'django.contrib.admin',
            'django.contrib.gis',
            'compressor',
        ] + OSCAR_CORE_APPS + [
            'oscar_recurly',
        ],
        AUTHENTICATION_BACKENDS=(
            'oscar.apps.customer.auth_backends.Emailbackend',
            'django.contrib.auth.backends.ModelBackend',
        ),
        LOGIN_REDIRECT_URL='/accounts/',
        APPEND_SLASH=True,
        HAYSTACK_CONNECTIONS={
            'default': {
                'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
            },
        },
        GEOIP_PATH='sandbox/geoip',
        COMPRESS_ENABLED=False,
        NOSE_ARGS=['-s', '-x', '--with-spec'],
    )

    default_settings = OSCAR_SETTINGS
    pairs.update(default_settings)

    # Look for a settings_local module that provides overrides for these test
    # settings.
    try:
        import settings_local
    except ImportError:
        pass
    else:
        keys = [key for key in dir(settings_local) if not key.startswith('__')]
        overrides = dict([(key, getattr(settings_local, key)) for key in keys])
        pairs.update(overrides)

    settings.configure(**pairs)


logging.disable(logging.CRITICAL)


def run_tests(*test_args):
    from django_nose import NoseTestSuiteRunner
    test_runner = NoseTestSuiteRunner()
    
    if not test_args:
        test_args = ['tests']
    c = coverage(source=['oscar_recurly'], omit=['*migrations*', '*tests*'])
    c.start()
    num_failures = test_runner.run_tests(test_args)
    c.stop()
    if num_failures:
        sys.exit(num_failures)
    print "Generating HTML coverage report"
    c.html_report()


if __name__ == '__main__':
    configure()
    run_tests(*sys.argv[1:])