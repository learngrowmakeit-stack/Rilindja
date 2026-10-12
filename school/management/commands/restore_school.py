import hashlib
import json
import os
import shutil
import sqlite3
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Rikuperon një kopje SQLite në një dosje TË RE; nuk mbishkruan mjedisin aktual.'
    def add_arguments(self,parser):
        parser.add_argument('--backup',required=True)
        parser.add_argument('--destination',required=True)
    def handle(self,*args,**options):
        destination = Path(options['destination']).resolve()
        if destination.exists(): raise CommandError('Përdorni destinacion të ri. Ndalni shërbimin para ndërrimit të databazës.')
        with TemporaryDirectory() as temp:
            with tarfile.open(options['backup'],'r:gz') as archive:
                archive.extractall(temp,filter='data')
            root = Path(temp)
            manifest = json.loads((root / 'manifest.json').read_text())
            if not manifest['engine'].endswith('sqlite3'): raise CommandError('Për PostgreSQL përdorni pg_restore në databazë të re.')
            database = root / 'database.sqlite3'
            if hashlib.sha256(database.read_bytes()).hexdigest() != manifest['database_sha256']: raise CommandError('Verifikimi i databazës dështoi.')
            with sqlite3.connect(database) as connection:
                if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok': raise CommandError('Databaza është e dëmtuar.')
            destination.mkdir(mode=0o700,parents=True)
            shutil.copy2(database,destination / 'school.sqlite3')
            os.chmod(destination / 'school.sqlite3',0o600)
            if (root / 'documents').exists(): shutil.copytree(root / 'documents',destination / 'documents')
        self.stdout.write(self.style.SUCCESS('Rikuperimi u verifikua. Vendosni RILINDJA_STATE_DIR në destinacionin e ri vetëm pas kontrollit.'))
