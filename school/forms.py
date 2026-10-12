from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import *
from .policies import *
from .services import validate_upload

class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'position', 'teaching_subject', 'duties']
        labels = {'first_name': 'Emri', 'last_name': 'Mbiemri'}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = self.fields['last_name'].required = True
        self.fields['password1'].label = 'Fjalëkalimi'
        self.fields['password2'].label = 'Konfirmimi i fjalëkalimit'
    def clean_email(self):
        value = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=value).exists(): raise ValidationError('Ky email është regjistruar tashmë.')
        return value
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.role, user.status, user.is_active = 'staff', 'pending', False
        if commit: user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Email-i zyrtar')
    password = forms.CharField(label='Fjalëkalimi', widget=forms.PasswordInput)

class UserApprovalForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['role', 'status']

class AdminCreationForm(RegistrationForm):
    class Meta(RegistrationForm.Meta):
        fields = RegistrationForm.Meta.fields + ['role','status']
    def save(self,commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        user.status = self.cleaned_data['status']
        user.is_active = user.status == 'active'
        if commit: user.save()
        return user

class UploadForm(forms.Form):
    file = forms.FileField(label='Skedari (PDF, DOCX, XLSX ose CSV; deri 20 MB)')
    def clean_file(self):
        file = self.cleaned_data['file']
        validate_upload(file)
        return file

class ReviewForm(forms.Form):
    status = forms.ChoiceField(label='Statusi', choices=DOCUMENT_STATUSES)
    comment = forms.CharField(label='Komenti', widget=forms.Textarea)

class TransferForm(forms.Form):
    destination = forms.ModelChoiceField(label='Klasa e re', queryset=Classroom.objects.filter(year__archived=False))
    date = forms.DateField(label='Data e transferimit', widget=forms.DateInput(attrs={'type': 'date'}))

def record_form(module, user, data=None, files=None, instance=None):
    model = MODULES[module][1]
    exclude = ['created_at', 'author', 'owner', 'weight', 'revision'] if module == 'grades' else ['created_at', 'author', 'owner']
    if module == 'documents': exclude += ['status']
    cls = forms.modelform_factory(model, exclude=exclude, widgets={
        f.name: (forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d') if isinstance(f, models.DateField) and not isinstance(f, models.DateTimeField)
                 else forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M') if isinstance(f, models.DateTimeField)
                 else forms.TimeInput(attrs={'type': 'time'}) )
        for f in model._meta.fields if isinstance(f, (models.DateField, models.TimeField))})
    form = cls(data=data, files=files, instance=instance)
    if module == 'grades':
        form.fields['expected_revision'] = forms.IntegerField(initial=instance.revision if instance else 0, widget=forms.HiddenInput)
    for name, field in form.fields.items():
        if isinstance(field, forms.ModelChoiceField):
            related = field.queryset.model
            if related == Document: field.queryset = documents_for(user)
            if related == Classroom: field.queryset = classes_for(user).filter(year__archived=False)
            if related == Assignment: field.queryset = assignments_for(user, write=module == 'grades').filter(classroom__year__archived=False)
            if related == Enrollment: field.queryset = scoped(user, 'enrollments').filter(classroom__year__archived=False)
            if related in (SchoolYear, Period, AssessmentType):
                field.queryset = field.queryset.filter(archived=False) if related == SchoolYear else field.queryset.filter(year__archived=False)
            if related == Student and user.role in TEACHERS: field.queryset = scoped(user, 'students')
            if related == User: field.queryset = field.queryset.filter(status='active', is_active=True)
    if module == 'cases':
        form.fields['psychologist'].queryset = User.objects.filter(pk=user.pk)
    if module == 'documents':
        kinds = [('shared','Tabelat dhe dokumentet e përbashkëta')]
        if user.role in TEACHERS | {'admin','director','pedagogue'}: kinds.insert(0, ('pedagogical','Dokumentacioni pedagogjik'))
        if user.role == 'psychologist': kinds.append(('psychological','Dokumentacioni psikologjik'))
        form.fields['kind'].choices = kinds
        if instance: form.fields.pop('kind')
    return form
