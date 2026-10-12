import uuid
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q

ROLES = [('admin', 'Administratori'), ('director', 'Drejtori'), ('secretary', 'Sekretari'),
         ('pedagogue', 'Pedagogu'), ('psychologist', 'Psikologu'), ('teacher', 'Mësimdhënësi'),
         ('homeroom', 'Mësimdhënësi kujdestar'), ('staff', 'Personeli i autorizuar')]

class User(AbstractUser):
    email = models.EmailField('Email-i zyrtar', unique=True)
    role = models.CharField('Roli', max_length=20, choices=ROLES, default='staff')
    status = models.CharField('Statusi', max_length=12, choices=[('pending', 'Në pritje të miratimit'),
        ('active', 'Aktiv'), ('blocked', 'Bllokuar'), ('disabled', 'Çaktivizuar')], default='pending')
    phone = models.CharField('Telefoni', max_length=40, blank=True)
    position = models.CharField('Pozita e kërkuar', max_length=100, blank=True)
    teaching_subject = models.CharField('Lënda e kërkuar', max_length=100, blank=True)
    duties = models.TextField('Klasat / detyrat e kërkuara', blank=True)

    def __str__(self):
        return self.get_full_name() or self.username

class Record(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        abstract = True

class SchoolSettings(models.Model):
    name = models.CharField('Emri i shkollës', max_length=200, default='Shkolla fillore Rilindja – Llojan')
    logo = models.ImageField('Logo', upload_to='branding/', blank=True)
    retention_years = models.PositiveIntegerField('Afati i ruajtjes në vite', default=10)
    def __str__(self): return self.name

class SchoolYear(Record):
    name = models.CharField('Viti shkollor', max_length=20, unique=True)
    archived = models.BooleanField('Arkivuar', default=False)
    # Rules are versioned per year; archived years cannot be edited via app.
    average_method = models.CharField('Metoda e mesatares', max_length=20,
        choices=[('equal_subjects', 'Peshë e barabartë për lëndët')], default='equal_subjects')
    pass_threshold = models.DecimalField('Pragu kalues', max_digits=3, decimal_places=2, default=Decimal('1.50'),
        validators=[MinValueValidator(1), MaxValueValidator(5)])
    def __str__(self): return self.name

class Period(Record):
    year = models.ForeignKey(SchoolYear, on_delete=models.PROTECT, verbose_name='Viti shkollor')
    name = models.CharField('Periudha', max_length=80)
    starts = models.DateField('Fillimi')
    ends = models.DateField('Përfundimi')
    class Meta:
        ordering = ['starts']
        constraints = [models.UniqueConstraint(fields=['year', 'name'], name='unique_period'),
                       models.CheckConstraint(condition=Q(ends__gte=models.F('starts')), name='period_dates')]
    def clean(self):
        if self.ends and self.starts and self.ends < self.starts: raise ValidationError('Datat nuk janë të vlefshme.')
    def __str__(self): return f'{self.year} / {self.name}'

class Classroom(Record):
    year = models.ForeignKey(SchoolYear, on_delete=models.PROTECT, verbose_name='Viti shkollor')
    level = models.PositiveSmallIntegerField('Klasa', validators=[MinValueValidator(1), MaxValueValidator(9)])
    parallel = models.CharField('Paralelja', max_length=10)
    homeroom = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Kujdestari')
    class Meta:
        ordering = ['level', 'parallel']
        constraints = [models.UniqueConstraint(fields=['year', 'level', 'parallel'], name='unique_class')]
    def __str__(self): return f'{self.level}-{self.parallel} ({self.year})'

class Subject(Record):
    name = models.CharField('Lënda', max_length=100, unique=True)
    def __str__(self): return self.name

class Assignment(Record):
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT, verbose_name='Klasa')
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, verbose_name='Lënda')
    teacher = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='Mësimdhënësi')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['classroom', 'subject'], name='unique_assignment')]
    def clean(self):
        if self.teacher_id and (self.teacher.role not in ('teacher', 'homeroom') or self.teacher.status != 'active'):
            raise ValidationError('Zgjidhni një mësimdhënës aktiv.')
    def __str__(self): return f'{self.classroom} / {self.subject}'

class Student(Record):
    first_name = models.CharField('Emri', max_length=80)
    last_name = models.CharField('Mbiemri', max_length=80)
    registration_number = models.CharField('Numri i regjistrit', max_length=40, unique=True)
    birth_date = models.DateField('Datëlindja', null=True, blank=True)
    guardian_contact = models.CharField('Kontakti i prindit / kujdestarit', max_length=100, blank=True)
    class Meta: ordering = ['last_name', 'first_name']
    def __str__(self): return f'{self.first_name} {self.last_name}'

class Enrollment(Record):
    student = models.ForeignKey(Student, on_delete=models.PROTECT, verbose_name='Nxënësi')
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT, verbose_name='Klasa')
    starts = models.DateField('Data e regjistrimit')
    ends = models.DateField('Data e transferimit', null=True, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student', 'classroom'], condition=Q(ends__isnull=True), name='active_enrollment'),
                       models.CheckConstraint(condition=Q(ends__isnull=True) | Q(ends__gte=models.F('starts')), name='enrollment_dates')]
    def clean(self):
        if self.student_id and self.classroom_id and not self.ends:
            duplicate = Enrollment.objects.filter(student=self.student, classroom__year=self.classroom.year, ends__isnull=True).exclude(pk=self.pk)
            if duplicate.exists(): raise ValidationError('Nxënësi është regjistruar tashmë në këtë vit. Përdorni transferimin.')
    def __str__(self): return f'{self.student} / {self.classroom}'

class AssessmentType(Record):
    year = models.ForeignKey(SchoolYear, on_delete=models.PROTECT, verbose_name='Viti shkollor')
    name = models.CharField('Lloji i vlerësimit', max_length=100)
    weight = models.DecimalField('Pesha', max_digits=6, decimal_places=2, default=1, validators=[MinValueValidator(Decimal('0.01'))])
    class Meta:
        constraints = [models.UniqueConstraint(fields=['year', 'name'], name='unique_assessment_type'),
                       models.CheckConstraint(condition=Q(weight__gt=0), name='positive_weight')]
    def __str__(self): return f'{self.name} × {self.weight}'

class Grade(Record):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.PROTECT, verbose_name='Nxënësi / klasa')
    assignment = models.ForeignKey(Assignment, on_delete=models.PROTECT, verbose_name='Lënda / mësimdhënësi')
    period = models.ForeignKey(Period, on_delete=models.PROTECT, verbose_name='Periudha')
    assessment_type = models.ForeignKey(AssessmentType, on_delete=models.PROTECT, verbose_name='Lloji')
    value = models.PositiveSmallIntegerField('Nota', validators=[MinValueValidator(1), MaxValueValidator(5)])
    weight = models.DecimalField(max_digits=6, decimal_places=2, editable=False)
    date = models.DateField('Data')
    author = models.ForeignKey(User, on_delete=models.PROTECT, editable=False)
    revision = models.PositiveIntegerField(default=1, editable=False)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(value__gte=1, value__lte=5), name='grade_range'),
                       models.CheckConstraint(condition=Q(weight__gt=0), name='grade_weight')]
    def clean(self):
        if not all([self.enrollment_id, self.assignment_id, self.period_id, self.assessment_type_id]): return
        if self.enrollment.classroom_id != self.assignment.classroom_id: raise ValidationError('Nxënësi nuk i përket kësaj klase.')
        year = self.assignment.classroom.year_id
        if self.period.year_id != year or self.assessment_type.year_id != year: raise ValidationError('Vitet shkollore nuk përputhen.')
        if self.date and not self.period.starts <= self.date <= self.period.ends: raise ValidationError('Data është jashtë periudhës.')
        if self.date and (self.date < self.enrollment.starts or (self.enrollment.ends and self.date > self.enrollment.ends)):
            raise ValidationError('Data është jashtë regjistrimit të nxënësit.')
    def __str__(self): return f'{self.enrollment.student} / {self.assignment.subject}: {self.value}'

class GradeHistory(Record):
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT)
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    previous = models.JSONField(null=True)
    current = models.JSONField()
    class Meta: ordering = ['-created_at']

class Attendance(Record):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.PROTECT, verbose_name='Nxënësi / klasa')
    date = models.DateField('Data')
    status = models.CharField('Prania', max_length=15, choices=[('present', 'I pranishëm'), ('absent', 'Mungon'), ('late', 'Me vonesë'), ('excused', 'Mungesë e arsyetuar')])
    reason = models.CharField('Arsyetimi', max_length=250, blank=True)
    author = models.ForeignKey(User, on_delete=models.PROTECT, editable=False)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['enrollment', 'date'], name='unique_attendance')]
    def clean(self):
        if self.enrollment_id and self.date and (self.date < self.enrollment.starts or (self.enrollment.ends and self.date > self.enrollment.ends)):
            raise ValidationError('Data është jashtë regjistrimit të nxënësit.')
    def __str__(self): return f'{self.enrollment.student} / {self.date} / {self.get_status_display()}'

DOCUMENT_STATUSES = [('draft', 'Draft'), ('submitted', 'Dorëzuar'), ('review', 'Në shqyrtim'), ('changes', 'Kërkon plotësim'), ('approved', 'Miratuar')]

class Document(Record):
    title = models.CharField('Titulli', max_length=200)
    description = models.TextField('Përshkrimi', blank=True)
    category = models.CharField('Kategoria', max_length=100)
    kind = models.CharField('Moduli', max_length=20, choices=[('pedagogical', 'Dokumentacioni pedagogjik'), ('shared', 'Tabelat dhe dokumentet e përbashkëta'), ('psychological', 'Dokumentacioni psikologjik')])
    owner = models.ForeignKey(User, on_delete=models.PROTECT, editable=False)
    year = models.ForeignKey(SchoolYear, on_delete=models.PROTECT, verbose_name='Viti shkollor')
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Klasa')
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Lënda')
    status = models.CharField('Statusi', max_length=15, choices=DOCUMENT_STATUSES, default='draft')
    read_only = models.BooleanField('Vetëm për lexim', default=False)
    due_date = models.DateField('Afati i dorëzimit',null=True,blank=True)
    def clean(self):
        if self.classroom_id and self.classroom.year_id != self.year_id: raise ValidationError('Klasa dhe viti nuk përputhen.')
    def __str__(self): return self.title

def private_path(instance, filename):
    return f'{instance.document_id}/{uuid.uuid4().hex}{__import__("pathlib").Path(filename).suffix.lower()}'

class DocumentVersion(Record):
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name='versions')
    number = models.PositiveIntegerField()
    file = models.FileField(upload_to=private_path)
    original_name = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    class Meta:
        ordering = ['-number']
        constraints = [models.UniqueConstraint(fields=['document', 'number'], name='unique_version')]
    def __str__(self): return f'{self.document} v{self.number}'

class DocumentPermission(Record):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='access')
    role = models.CharField('Roli', max_length=20, choices=ROLES, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Përdoruesi')
    view = models.BooleanField('Shikim', default=True)
    download = models.BooleanField('Shkarkim', default=True)
    edit = models.BooleanField('Ndryshim', default=False)
    delete = models.BooleanField('Fshirje', default=False)
    def clean(self):
        if bool(self.role) == bool(self.user_id): raise ValidationError('Zgjidhni vetëm rol ose përdorues.')
        if self.document_id and self.document.kind == 'psychological' and self.role:
            raise ValidationError('Dokumentet konfidenciale kërkojnë autorizim individual.')
    class Meta:
        constraints = [models.CheckConstraint(condition=(Q(role='', user__isnull=False) | (~Q(role='') & Q(user__isnull=True))), name='permission_target')]
    def __str__(self): return f'{self.document} / {self.user or self.get_role_display()}'

class DocumentComment(Record):
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    text = models.TextField('Komenti')
    status = models.CharField(max_length=15, choices=DOCUMENT_STATUSES)

class PsychologyCase(Record):
    student = models.ForeignKey(Student, on_delete=models.PROTECT, verbose_name='Nxënësi')
    psychologist = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='Psikologu')
    authorized = models.ManyToManyField(User, related_name='authorized_cases', blank=True, verbose_name='Persona të autorizuar')
    title = models.CharField('Titulli', max_length=150)
    notes = models.TextField('Shënime profesionale')
    support_plan = models.TextField('Plani i mbështetjes', blank=True)
    next_meeting = models.DateTimeField('Takimi i radhës', null=True, blank=True)
    closed = models.BooleanField('Mbyllur', default=False)
    def clean(self):
        if self.psychologist_id and self.psychologist.role != 'psychologist': raise ValidationError('Përgjegjësi duhet të jetë psikolog.')
    def __str__(self): return self.title

class Schedule(Record):
    assignment = models.ForeignKey(Assignment, on_delete=models.PROTECT, verbose_name='Klasa / lënda')
    weekday = models.PositiveSmallIntegerField('Dita', choices=[(0,'E hënë'),(1,'E martë'),(2,'E mërkurë'),(3,'E enjte'),(4,'E premte')])
    starts = models.TimeField('Fillimi')
    ends = models.TimeField('Përfundimi')
    room = models.CharField('Kabineti', max_length=80)
    def clean(self):
        if not self.starts or not self.ends or not self.assignment_id: return
        if self.ends <= self.starts: raise ValidationError('Ora e përfundimit duhet të jetë pas fillimit.')
        conflict = Schedule.objects.filter(assignment__classroom__year=self.assignment.classroom.year,
            weekday=self.weekday, starts__lt=self.ends, ends__gt=self.starts).exclude(pk=self.pk).filter(
            Q(assignment__classroom=self.assignment.classroom) | Q(assignment__teacher=self.assignment.teacher) | Q(room=self.room))
        if conflict.exists(): raise ValidationError('Mbivendosje e klasës, mësimdhënësit ose kabinetit.')
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(ends__gt=models.F('starts')), name='schedule_times')]
    def __str__(self): return f'{self.get_weekday_display()} {self.starts}–{self.ends}: {self.assignment}'

class Event(Record):
    title = models.CharField('Aktiviteti / takimi', max_length=200)
    starts = models.DateTimeField('Fillimi')
    ends = models.DateTimeField('Përfundimi')
    description = models.TextField('Përshkrimi', blank=True)
    participants = models.ManyToManyField(User, verbose_name='Pjesëmarrësit')
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name='owned_events', editable=False)
    def clean(self):
        if self.starts and self.ends and self.ends <= self.starts: raise ValidationError('Datat nuk janë të vlefshme.')
    def __str__(self): return self.title

class Protocol(Record):
    number = models.CharField('Numri i protokollit', max_length=80, unique=True)
    title = models.CharField('Titulli', max_length=200)
    direction = models.CharField('Drejtimi', max_length=10, choices=[('incoming','Hyrës'),('outgoing','Dalës'),('request','Kërkesë për dokument')])
    date = models.DateField('Data')
    correspondent = models.CharField('Dërguesi / marrësi', max_length=200)
    document = models.ForeignKey(Document, on_delete=models.PROTECT, blank=True, null=True, verbose_name='Dokumenti')
    status = models.CharField('Statusi', max_length=100, default='Në pritje')
    def __str__(self): return f'{self.number}: {self.title}'

class Notification(Record):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    read = models.BooleanField(default=False)
    class Meta: ordering = ['-created_at']
    def __str__(self): return self.title

class Audit(Record):
    actor = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    action = models.CharField(max_length=100)
    target = models.CharField(max_length=150)
    details = models.JSONField(default=dict)
    class Meta: ordering = ['-created_at']
    def __str__(self): return f'{self.created_at}: {self.action} / {self.actor}'

class LoginAttempt(models.Model):
    key = models.CharField(max_length=64, unique=True)
    failures = models.PositiveIntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)

class ImportBatch(Record):
    checksum = models.CharField(max_length=64)
    module = models.CharField(max_length=20)
    year = models.ForeignKey(SchoolYear, on_delete=models.PROTECT)
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    count = models.PositiveIntegerField()
    class Meta:
        constraints = [models.UniqueConstraint(fields=['checksum','module','year'],name='unique_import_batch')]

class ModulePermission(Record):
    role = models.CharField('Roli', max_length=20, choices=ROLES)
    module = models.CharField('Moduli', max_length=30, choices=[
        ('students','Nxënësit'),('enrollments','Regjistrimet'),('classes','Klasat'),('subjects','Lëndët'),
        ('assignments','Caktimet'),('years','Vitet'),('periods','Periudhat'),('types','Peshat'),('grades','Notat'),
        ('attendance','Vijueshmëria'),('documents','Dokumentet'),('cases','Psikologu'),('schedule','Orari'),
        ('events','Kalendari'),('protocol','Protokolli')])
    can_view = models.BooleanField('Lejo shikimin brenda përgjegjësive të rolit',default=True)
    can_edit = models.BooleanField('Lejo ndryshimin brenda përgjegjësive të rolit',default=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['role','module'],name='unique_module_permission')]
    def clean(self):
        if self.role=='admin': raise ValidationError('Autorizimet bazë administrative nuk çaktivizohen.')
        if self.can_edit and not self.can_view: raise ValidationError('Ndryshimi kërkon leje për shikim.')
    def __str__(self): return f'{self.get_role_display()} / {self.get_module_display()}'
