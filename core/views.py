# core/views.py

from django.shortcuts import render

def custom_403_handler(request, exception):
    """
    هندلر سفارشی برای ارور 403
    """
    return render(request, 'core/403.html', status=403)  # تغییر از 'core/403.html' به '403.html'