from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def admin_login(request):
    return render(request, 'login_admin.html')

def user_login(request):
    return render(request, 'login_user.html')
