import hashlib
import json
import os
import sqlite3
import subprocess
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

class Command(BaseCommand):
    help = 'Kopje rezervë konsistente e databazës dhe skedarëve privatë; ruajeni në destinacion të enkriptuar.'
    def add_arguments(self, parser): parser.add_argument('--output', required=True)
    def handle(self,*args,**options):
        output = Path(options['output']).resolve()
        if output.exists(): raise CommandError('Destinacioni ekziston; nuk mbishkruhet.')
        output.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        db = settings.DATABASES['default']
        old_umask = os.umask(0o077)
        try:
            with TemporaryDirectory() as temp:
                root = Path(temp)
                sqlite = db['ENGINE'].endswith('sqlite3')
                filename = 'database.sqlite3' if sqlite else 'database.dump'
                if sqlite:
                    with sqlite3.connect(db['NAME']) as source, sqlite3.connect(root / filename) as target: source.backup(target)
                else:
                    env = os.environ.copy()
                    env['PGPASSWORD'] = db.get('PASSWORD','')
                    subprocess.run(['pg_dump','--format=custom','--no-owner','--host',db['HOST'],'--port',db['PORT'],
                        '--username',db['USER'],'--file',str(root / filename),db['NAME']],env=env,check=True)
                manifest = {'created':timezone.now().isoformat(),'engine':db['ENGINE'],
                            'database_sha256':hashlib.sha256((root / filename).read_bytes()).hexdigest()}
                (root / 'manifest.json').write_text(json.dumps(manifest))
                with tarfile.open(output,'x:gz') as archive:
                    archive.add(root / filename,arcname=filename)
                    archive.add(root / 'manifest.json',arcname='manifest.json')
                    if settings.MEDIA_ROOT.exists(): archive.add(settings.MEDIA_ROOT,arcname='documents')
            self.stdout.write(self.style.SUCCESS(f'Kopja u ruajt: {output} (leje 0600).'))
        except (OSError, subprocess.CalledProcessError) as error: raise CommandError(str(error))
        finally: os.umask(old_umask)
