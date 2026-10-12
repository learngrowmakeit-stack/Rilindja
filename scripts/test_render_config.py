"""Verify deployment configuration locally without contacting a Render account or database."""
import os
import secrets
import subprocess
import sys
import tempfile
import socket
import time
import http.client
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    with tempfile.TemporaryDirectory(prefix='rilindja-render-check-') as temp:
        runtime = os.environ.copy()
        runtime['PATH'] = str(Path(sys.executable).parent) + os.pathsep + runtime.get('PATH','')
        runtime.update(RILINDJA_DEBUG='0',RILINDJA_SECRET_KEY=secrets.token_urlsafe(64),RILINDJA_STATE_DIR=temp)
        # A fake local address for parsing only; never connects to a database.
        render = {**runtime,'RENDER':'true','RENDER_EXTERNAL_HOSTNAME':'rilindja-test.onrender.com',
                  'RILINDJA_DATABASE_URL':'postgresql://test_user@localhost:5432/test_database?sslmode=require'}
        checks = """
from config import settings as s
assert not s.DEBUG
assert s.SECURE_PROXY_SSL_HEADER == ('HTTP_X_FORWARDED_PROTO', 'https')
assert 'rilindja-test.onrender.com' in s.ALLOWED_HOSTS
assert s.CSRF_TRUSTED_ORIGINS == ['https://rilindja-test.onrender.com']
assert s.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql'
assert s.DATABASES['default']['OPTIONS']['sslmode'] == 'require'
assert s.SESSION_COOKIE_SECURE and s.CSRF_COOKIE_SECURE
print('Render settings: PostgreSQL/TLS, exact host and HTTPS cookies verified')
"""
        subprocess.run([sys.executable,'-c',checks],cwd=ROOT,env=render,check=True)
        for key,value in [('RILINDJA_DATABASE_URL',''),('RILINDJA_DATABASE_URL','postgres://localhost/db?sslmode=disable'),
                          ('RILINDJA_DEBUG','1')]:
            failed = subprocess.run([sys.executable,'-c','from config import settings'],cwd=ROOT,env={**render,key:value},
                                    stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            assert failed.returncode != 0, 'Unsafe production setting unexpectedly accepted'
        print('Render settings: missing database, disabled TLS and DEBUG are rejected')
        subprocess.run(['bash','scripts/render_build.sh'],cwd=ROOT,env=runtime,check=True)
        subprocess.run([sys.executable,'manage.py','migrate','--noinput'],cwd=ROOT,env=runtime,check=True,stdout=subprocess.DEVNULL)
        smoke = """
import os
os.environ['DJANGO_SETTINGS_MODULE']='config.settings'
import django
django.setup()
from django.test import Client
client=Client()
r=client.get('/hyrje/',secure=True)
assert r.status_code==200 and 'Hyni në shkollën tuaj digjitale' in r.content.decode()
from django.contrib.staticfiles.storage import staticfiles_storage
url=staticfiles_storage.url('school/style.css')
r=client.get(url,secure=True)
assert r.status_code==200 and r['Content-Type'].startswith('text/css')
assert client.get('/hyrje/').status_code==301
assert client.get('/media/private.pdf',secure=True).status_code==404
print('Production WSGI: HTTPS login, hashed static stylesheet, HTTPS redirect and private media verified')
"""
        subprocess.run([sys.executable,'-c',smoke],cwd=ROOT,env=runtime,check=True)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            port = sock.getsockname()[1]
        with open(Path(temp)/'gunicorn.log','w') as log:
            server = subprocess.Popen(['bash','scripts/render_start.sh'],cwd=ROOT,
                env={**runtime,'PORT':str(port),'WEB_CONCURRENCY':'1'},stdout=log,stderr=log)
            try:
                for attempt in range(100):
                    if server.poll() is not None:
                        raise RuntimeError('Gunicorn startup failed; inspect deployment settings.')
                    try:
                        connection = http.client.HTTPConnection('127.0.0.1',port,timeout=1)
                        connection.request('GET','/hyrje/')
                        response = connection.getresponse()
                        assert response.status == 301 and response.getheader('Location').startswith('https://')
                        assert 'gunicorn' in response.getheader('Server','').lower()
                        response.read()
                        connection.close()
                        break
                    except OSError: time.sleep(.1)
                else: raise RuntimeError('Gunicorn did not respond.')
                print('Start script: migrations, Gunicorn bind and enforced HTTPS verified')
            finally:
                server.terminate()
                server.wait(timeout=15)

if __name__ == '__main__': main()
