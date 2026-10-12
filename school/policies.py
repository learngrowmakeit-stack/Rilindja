from django.db.models import Q
from .models import *

ACADEMIC_READ = {'admin', 'director', 'pedagogue'}
STUDENT_WRITE = {'admin', 'secretary'}
TEACHERS = {'teacher', 'homeroom'}
MODULES = {
    'students': ('Nxënësit', Student, {'admin','director','secretary','pedagogue','teacher','homeroom'}, STUDENT_WRITE),
    'enrollments': ('Regjistrimet në klasa', Enrollment, {'admin','director','secretary','pedagogue','teacher','homeroom'}, STUDENT_WRITE),
    'classes': ('Klasat dhe paralelet', Classroom, {'admin','director','secretary','pedagogue','teacher','homeroom'}, {'admin'}),
    'subjects': ('Lëndët', Subject, {'admin','director','pedagogue','teacher','homeroom'}, {'admin'}),
    'assignments': ('Caktimet e mësimdhënësve', Assignment, {'admin','director','pedagogue','teacher','homeroom'}, {'admin'}),
    'years': ('Vitet shkollore dhe rregullat', SchoolYear, {'admin','director','secretary','pedagogue','teacher','homeroom'}, {'admin'}),
    'periods': ('Periudhat', Period, {'admin','director','pedagogue','teacher','homeroom'}, {'admin'}),
    'types': ('Llojet dhe peshat e vlerësimit', AssessmentType, {'admin','director','pedagogue','teacher','homeroom'}, {'admin'}),
    'grades': ('Notat dhe vlerësimet', Grade, ACADEMIC_READ | TEACHERS, {'admin'} | TEACHERS),
    'attendance': ('Vijueshmëria dhe mungesat', Attendance, ACADEMIC_READ | TEACHERS, {'admin'} | TEACHERS),
    'documents': ('Dokumentacioni dhe tabelat', Document, {r for r, _ in ROLES}, {r for r, _ in ROLES}),
    'cases': ('Hapësira profesionale e psikologut', PsychologyCase, {'psychologist'}, {'psychologist'}),
    'schedule': ('Orari mësimor', Schedule, {'admin','director','pedagogue','teacher','homeroom'}, {'admin','director'}),
    'events': ('Kalendari i aktiviteteve', Event, {r for r, _ in ROLES}, {'admin','director','psychologist'}),
    'protocol': ('Protokolli dhe kërkesat', Protocol, {'admin','director','secretary'}, {'admin','secretary'}),
    'audit': ('Historiku i veprimeve', Audit, {'admin'}, set()),
    'settings': ('Konfigurimi i shkollës', SchoolSettings, {'admin'}, {'admin'}),
    'permissions': ('Lejet e moduleve sipas roleve', ModulePermission, {'admin'}, {'admin'}),
}

def allowed(user, module, write=False):
    if user.role not in MODULES[module][3 if write else 2]: return False
    rule = ModulePermission.objects.filter(role=user.role,module=module).first()
    return not rule or (rule.can_view and (not write or rule.can_edit))

def classes_for(user):
    qs = Classroom.objects.all()
    if user.role in TEACHERS:
        qs = qs.filter(Q(assignment__teacher=user) | Q(homeroom=user)).distinct()
    return qs

def assignments_for(user, write=False):
    qs = Assignment.objects.select_related('classroom__year', 'subject', 'teacher')
    if user.role in TEACHERS:
        qs = qs.filter(teacher=user) if write or user.role == 'teacher' else qs.filter(Q(teacher=user) | Q(classroom__homeroom=user))
    return qs

def document_allowed(user, document, action='view'):
    if not allowed(user,'documents'): return False
    if document.kind == 'psychological':
        # Even administrators/directors need an explicit personal grant.
        return document.owner_id == user.id or document.access.filter(user=user, **{action: True}).exists()
    if document.owner_id == user.id:
        return action not in ('edit', 'delete') or not document.read_only
    if user.role == 'admin': return True
    if document.kind == 'pedagogical' and user.role in ('director', 'pedagogue'):
        return action in ('view', 'download')
    if action in ('edit', 'delete') and document.read_only: return False
    return document.access.filter(Q(role=user.role) | Q(user=user), **{action: True}).exists()

def documents_for(user):
    if not allowed(user,'documents'): return Document.objects.none()
    personal = Q(owner=user) | Q(access__user=user, access__view=True)
    normal = ~Q(kind='psychological')
    if user.role == 'admin': rule = normal | personal
    else:
        rule = personal | (normal & Q(access__role=user.role, access__view=True))
        if user.role in ('director', 'pedagogue'): rule |= Q(kind='pedagogical')
    return Document.objects.filter(rule).distinct().select_related('owner', 'year', 'classroom', 'subject')

def scoped(user, module):
    model = MODULES[module][1]
    if not allowed(user,module): return model.objects.none()
    if module == 'documents': return documents_for(user)
    if module == 'cases': return PsychologyCase.objects.filter(Q(psychologist=user) | Q(authorized=user)).distinct()
    if module == 'events': return Event.objects.filter(Q(owner=user) | Q(participants=user)).distinct()
    qs = model.objects.all()
    if module == 'protocol': return qs.filter(Q(document__isnull=True) | Q(document__in=documents_for(user)))
    if user.role in TEACHERS:
        if module == 'classes': return classes_for(user)
        if module == 'students': return qs.filter(enrollment__classroom__in=classes_for(user)).distinct()
        if module == 'enrollments': return qs.filter(classroom__in=classes_for(user))
        if module == 'assignments': return assignments_for(user)
        if module == 'grades': return qs.filter(assignment__in=assignments_for(user))
        if module == 'attendance': return qs.filter(enrollment__classroom__in=classes_for(user))
        if module == 'schedule': return qs.filter(assignment__classroom__in=classes_for(user))
    return qs

def writable(user, module, obj=None):
    if not allowed(user,module,write=True): return False
    if obj is None: return True
    if module == 'documents': return document_allowed(user, obj, 'edit')
    if module == 'cases': return obj.psychologist_id == user.id
    if module == 'events': return obj.owner_id == user.id
    if module == 'grades' and user.role in TEACHERS: return obj.assignment.teacher_id == user.id
    if module == 'attendance' and user.role in TEACHERS: return obj.enrollment.classroom in classes_for(user)
    return True

def year_of(obj):
    if isinstance(obj, SchoolYear): return obj
    if hasattr(obj, 'year'): return obj.year
    if hasattr(obj, 'classroom') and obj.classroom: return obj.classroom.year
    if hasattr(obj, 'enrollment'): return obj.enrollment.classroom.year
    if hasattr(obj, 'assignment'): return obj.assignment.classroom.year
    return None
