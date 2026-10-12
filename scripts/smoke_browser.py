"""Real browser smoke test in a disposable database. Requires playwright and Chromium."""
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['RILINDJA_DEBUG'] = '1'

def run():
    with tempfile.TemporaryDirectory(prefix='rilindja-browser-') as temp:
        os.environ['RILINDJA_STATE_DIR'] = temp
        import django
        django.setup()
        from django.core.management import call_command
        from school.models import User, SchoolSettings, SchoolYear, Classroom, Student, Enrollment
        from playwright.sync_api import sync_playwright
        call_command('migrate',verbosity=0)
        password = secrets.token_urlsafe(32)
        User.objects.create_user(username='browser@school.test',email='browser@school.test',password=password,
            first_name='TEST',last_name='Administratori',role='admin',status='active',is_active=True)
        SchoolSettings.objects.create(name='TEST · Shkolla Rilindja')
        year = SchoolYear.objects.create(name='TEST 2026/27')
        classroom = Classroom.objects.create(year=year,level=3,parallel='A')
        student = Student.objects.create(first_name='TEST Arta',last_name='Shembull',registration_number='BROWSER-TEST')
        Enrollment.objects.create(student=student,classroom=classroom,starts=date(2026,9,1))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            port = sock.getsockname()[1]
        with open(Path(temp)/'server.log','w') as log:
            server = subprocess.Popen([sys.executable,str(ROOT/'manage.py'),'runserver',f'127.0.0.1:{port}','--noreload'],
                cwd=ROOT,env=os.environ.copy(),stdout=log,stderr=log)
            try:
                import urllib.request
                url = f'http://127.0.0.1:{port}'
                for _ in range(100):
                    try:
                        urllib.request.urlopen(url+'/hyrje/',timeout=1)
                        break
                    except OSError: time.sleep(.1)
                else: raise RuntimeError('Server failed to start: '+(Path(temp)/'server.log').read_text())
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
                    for label,viewport in [('desktop',{'width':1440,'height':1000}),('mobile',{'width':390,'height':844})]:
                        page = browser.new_page(viewport=viewport)
                        errors = []
                        page.on('pageerror',lambda error: errors.append(str(error)))
                        page.goto(url+'/hyrje/')
                        page.get_by_label('Email-i zyrtar').fill('browser@school.test')
                        page.locator('input[name=password]').fill(password)
                        page.get_by_role('button',name='Hyr në sistem').click()
                        page.get_by_role('heading',name='Përmbledhja e shkollës').wait_for()
                        assert page.locator('.cards').inner_text().find('Nxënës')>=0
                        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),label+' dashboard overflow'
                        page.goto(url+'/modulet/students/')
                        page.get_by_placeholder('Kërko në regjistër').fill('Arta')
                        page.get_by_role('button',name='Filtro',exact=True).click()
                        page.get_by_role('cell',name='TEST Arta',exact=True).wait_for()
                        page.get_by_role('link',name='Profili',exact=True).click()
                        page.get_by_role('heading',name='TEST Arta Shembull').wait_for()
                        page.goto(url+'/modulet/subjects/shto/')
                        page.get_by_label('Lënda').fill('TEST Lënda '+label)
                        page.get_by_role('button',name='Ruaj',exact=True).click()
                        page.get_by_role('cell',name='TEST Lënda '+label,exact=True).wait_for()
                        assert not errors,errors
                        page.goto(url+'/')
                        page.get_by_role('button',name='Dil nga llogaria').click()
                        page.get_by_role('heading',name='Hyni në shkollën tuaj digjitale').wait_for()
                        page.close()
                        print(label+': login, dashboard, student search/profile, persistent create and logout passed')
                    browser.close()
                backup = Path(temp)/'verified-backup.tar.gz'
                restored = Path(temp)/'restored'
                call_command('backup_school',output=str(backup),verbosity=0)
                call_command('restore_school',backup=str(backup),destination=str(restored),verbosity=0)
                import sqlite3
                with sqlite3.connect(restored/'school.sqlite3') as connection:
                    assert connection.execute('SELECT COUNT(*) FROM school_student').fetchone()[0] == 1
                    assert connection.execute('SELECT COUNT(*) FROM school_subject').fetchone()[0] == 2
                print('backup/restore: browser-created records survive verified recovery')
            finally:
                server.terminate()
                server.wait(timeout=10)

if __name__ == '__main__': run()
