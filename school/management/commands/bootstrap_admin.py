from getpass import getpass
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from school.models import User, SchoolSettings
from school.services import audit

class Command(BaseCommand):
    help = 'Krijon administratorin e parë vetëm nga terminali i besuar, pa fjalëkalim të paracaktuar.'
    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--name', default='Administratori i shkollës')
    def handle(self, *args, **options):
        if User.objects.filter(role='admin').exists(): raise CommandError('Administratori ekziston; përdorni panelin për llogari të tjera.')
        email = options['email'].strip().lower()
        from django.core.validators import validate_email
        try: validate_email(email)
        except ValidationError as error: raise CommandError(str(error))
        if User.objects.filter(email__iexact=email).exists(): raise CommandError('Email-i është në përdorim.')
        password = getpass('Fjalëkalimi (të paktën 12 shenja): ')
        if password != getpass('Konfirmoni fjalëkalimin: '): raise CommandError('Fjalëkalimet nuk përputhen.')
        user = User(username=email,email=email,first_name=options['name'],role='admin',status='active',is_active=True)
        try: validate_password(password,user)
        except ValidationError as error: raise CommandError(str(error))
        with transaction.atomic():
            user.set_password(password)
            user.save()
            SchoolSettings.objects.get_or_create(pk=1)
            audit(user,'Konfigurimi i administratorit të parë',user.pk)
        self.stdout.write(self.style.SUCCESS('Administratori u krijua. Fjalëkalimi nuk u shfaq dhe nuk u ruajt në tekst.'))
