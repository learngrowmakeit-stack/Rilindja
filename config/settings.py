import os
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, unquote
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.environ.get('RILINDJA_STATE_DIR', BASE_DIR / 'var'))
STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
DEBUG = os.environ.get('RILINDJA_DEBUG', '0') == '1'
SECRET_KEY = os.environ.get('RILINDJA_SECRET_KEY')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('Vendosni RILINDJA_SECRET_KEY për mjedisin e prodhimit.')
    key_path = STATE_DIR / 'development.key'
    if not key_path.exists():
        from django.core.management.utils import get_random_secret_key
        try:
            with key_path.open('x') as handle:
                os.chmod(key_path, 0o600)
                handle.write(get_random_secret_key())
        except FileExistsError:
            pass
    SECRET_KEY = key_path.read_text()
ALLOWED_HOSTS = os.environ.get('RILINDJA_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
ON_RENDER = os.environ.get('RENDER') == 'true'
render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if ON_RENDER and render_host:
    ALLOWED_HOSTS.append(render_host)
    CSRF_TRUSTED_ORIGINS = ['https://' + render_host]
if ON_RENDER:
    # Only enable this behind Render's managed HTTPS reverse proxy.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
                  'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'school']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'whitenoise.middleware.WhiteNoiseMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
              'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
              'django.contrib.auth.middleware.AuthenticationMiddleware', 'school.middleware.ActiveAccountMiddleware',
              'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True,
              'OPTIONS': {'context_processors': ['django.template.context_processors.request',
              'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages',
              'school.context.navigation']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': STATE_DIR / 'school.sqlite3', 'OPTIONS': {'timeout': 20}}}
if os.environ.get('RILINDJA_DB_NAME'):
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': os.environ['RILINDJA_DB_NAME'],
        'USER': os.environ.get('RILINDJA_DB_USER', ''), 'PASSWORD': os.environ.get('RILINDJA_DB_PASSWORD', ''),
        'HOST': os.environ.get('RILINDJA_DB_HOST', 'localhost'), 'PORT': os.environ.get('RILINDJA_DB_PORT', '5432')}}
database_url = os.environ.get('RILINDJA_DATABASE_URL')
if database_url:
    try:
        parsed = urlsplit(database_url)
        if parsed.scheme not in ('postgres', 'postgresql') or not parsed.hostname or not parsed.path.strip('/'):
            raise ValueError
        sslmode = parse_qs(parsed.query).get('sslmode', ['require'])[0]
        if sslmode not in ('require', 'verify-ca', 'verify-full'):
            raise ValueError
        DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': unquote(parsed.path.lstrip('/')),
            'USER': unquote(parsed.username or ''), 'PASSWORD': unquote(parsed.password or ''),
            'HOST': parsed.hostname, 'PORT': str(parsed.port or 5432), 'CONN_MAX_AGE': 60,
            'CONN_HEALTH_CHECKS': True, 'OPTIONS': {'sslmode': sslmode}}}
    except (ValueError, TypeError):
        raise ImproperlyConfigured('RILINDJA_DATABASE_URL duhet të jetë URL PostgreSQL e vlefshme me TLS.') from None
if ON_RENDER:
    if DEBUG:
        raise ImproperlyConfigured('Render kërkon RILINDJA_DEBUG=0.')
    if DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
        raise ImproperlyConfigured('Render kërkon databazë PostgreSQL; vendosni RILINDJA_DATABASE_URL.')
    if 'RILINDJA_STATE_DIR' not in os.environ:
        raise ImproperlyConfigured('Vendosni RILINDJA_STATE_DIR në diskun e qëndrueshëm për dokumentet private.')
AUTH_USER_MODEL = 'school.User'
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'sq'
TIME_ZONE = 'Europe/Skopje'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
            'staticfiles': {'BACKEND': ('django.contrib.staticfiles.storage.StaticFilesStorage' if DEBUG
                                      else 'whitenoise.storage.CompressedManifestStaticFilesStorage')}}
MEDIA_ROOT = STATE_DIR / 'documents'
# No public MEDIA_URL: every download passes authorization in a view.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/hyrje/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/hyrje/'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
DATA_UPLOAD_MAX_MEMORY_SIZE = 22 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 16000
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
EMAIL_BACKEND = os.environ.get('RILINDJA_EMAIL_BACKEND', 'django.core.mail.backends.filebased.EmailBackend')
EMAIL_FILE_PATH = STATE_DIR / 'mail'
EMAIL_HOST = os.environ.get('RILINDJA_EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('RILINDJA_EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('RILINDJA_EMAIL_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('RILINDJA_EMAIL_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('RILINDJA_FROM_EMAIL', 'shkolla@example.invalid')
