from .models import SchoolSettings, Notification, PsychologyCase
from .policies import MODULES, allowed

def navigation(request):
    user = request.user
    return {'school_name': (SchoolSettings.objects.first().name if SchoolSettings.objects.exists() else 'Shkolla fillore Rilindja – Llojan'),
            'navigation': [(key, value[0]) for key, value in MODULES.items() if user.is_authenticated and allowed(user,key)],
            'can_success': user.is_authenticated and allowed(user,'grades'),
            'has_authorized_cases': user.is_authenticated and PsychologyCase.objects.filter(authorized=user).exists(),
            'unread_count': Notification.objects.filter(recipient=user, read=False).count() if user.is_authenticated else 0}
