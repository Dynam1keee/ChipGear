from django.shortcuts import render


def error_view(request, exception=None, status=500):
    return render(request, '404_page.html', status=status)


# Django calls each handler for its own kind of error, so the status code
# is known from the handler and does not have to be guessed from the exception.
def bad_request_view(request, exception=None):
    return error_view(request, exception, status=400)


def permission_denied_view(request, exception=None):
    return error_view(request, exception, status=403)


def not_found_view(request, exception=None):
    return error_view(request, exception, status=404)


def server_error_view(request):
    return error_view(request, status=500)
