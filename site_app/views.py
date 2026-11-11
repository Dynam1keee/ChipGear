from django.shortcuts import render

def error_view(request, exception=None, status=500):
    # Визначити статус помилки
    if exception:
        status_code = 404 if hasattr(exception, 'status_code') and exception.status_code == 404 else 500
    else:
        status_code = status
    
    return render(request, '404_page.html', status=status_code)