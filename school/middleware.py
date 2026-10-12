from django.contrib.auth import logout

class ActiveAccountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and (not request.user.is_active or request.user.status != 'active'):
            logout(request)
        response = self.get_response(request)
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-store'
        return response
