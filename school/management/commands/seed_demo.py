from datetime import date
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from school.models import *

class Command(BaseCommand):
    help = 'Krijon vetëm regjistra demonstrimi të shënuar qartë; pa përdorues, fjalëkalime ose nota të sajuara.'
    @transaction.atomic
    def handle(self,*args,**options):
        year,_ = SchoolYear.objects.get_or_create(name='DEMO 2026/2027')
        for name,start,end in [('Tremujori I',date(2026,9,1),date(2026,11,30)),('Tremujori II',date(2026,12,1),date(2027,2,28)),('Tremujori III',date(2027,3,1),date(2027,6,30))]:
            Period.objects.get_or_create(year=year,name=name,defaults={'starts':start,'ends':end})
        for name,weight in [('Test',2),('Përgjigje me gojë',1),('Detyrë',1)]:
            AssessmentType.objects.get_or_create(year=year,name=name,defaults={'weight':weight})
        for name in ['Gjuhë shqipe','Matematikë','Shkenca natyrore']: Subject.objects.get_or_create(name=name)
        for level in [3,4,5]:
            classroom,_ = Classroom.objects.get_or_create(year=year,level=level,parallel='A')
            for index in range(1,5):
                student,_ = Student.objects.get_or_create(registration_number=f'DEMO-{level}-{index}',defaults={'first_name':f'DEMO Nxënës {index}','last_name':f'Klasa {level}'})
                Enrollment.objects.get_or_create(student=student,classroom=classroom,defaults={'starts':date(2026,9,1)})
        self.stdout.write(self.style.SUCCESS('Regjistrat DEMO u krijuan; caktimet dhe notat duhet të plotësohen nga përdoruesit e autorizuar.'))
