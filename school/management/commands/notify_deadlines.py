from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from school.models import Document, Notification, Audit, User

class Command(BaseCommand):
    help = 'Njofton përgjegjësit për afatet pedagogjike në 7 ditët e ardhshme; i përsëritshëm një herë në ditë.'
    def handle(self,*args,**options):
        today = timezone.localdate()
        count = 0
        for document in Document.objects.filter(kind='pedagogical',year__archived=False,due_date__lte=today+timedelta(days=7),
            status__in=['draft','changes'],owner__status='active'):
            title = 'Afati i dokumentacionit pedagogjik'
            body = f'{document.title} · Afati: {document.due_date}'
            if not Notification.objects.filter(recipient=document.owner,title=title,body=body,created_at__date=today).exists():
                Notification.objects.create(recipient=document.owner,title=title,body=body)
                count += 1
        self.stdout.write(f'U krijuan {count} njoftime të afateve.')
