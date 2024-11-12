from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse

# Ana sayfa view
def index(request):
    return render(request, 'index.html')

# Admin giriş sayfası view
def admin_login(request):
    if request.method == 'POST':
        # Giriş işlemlerini burada yapın
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Admin doğrulama işlemi (örnek olarak eklenmiştir)
        if username == "admin" and password == "admin123":  # Burada veritabanı doğrulaması yapılabilir
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Geçersiz kullanıcı adı veya şifre.')
    return render(request, 'login_admin.html')

# Kullanıcı giriş sayfası view
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Kullanıcı doğrulama işlemi (örnek olarak eklenmiştir)
        if username == "user" and password == "user123":  # Burada veritabanı doğrulaması yapılabilir
            return redirect('user_dashboard')
        else:
            messages.error(request, 'Geçersiz kullanıcı adı veya şifre.')
    return render(request, 'login_user.html')

# Admin kontrol paneli view
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

# Kullanıcı kontrol paneli view
def user_dashboard(request):
    return render(request, 'user_dashboard.html')

# Şifre sıfırlama sayfası view
def password_reset(request):
    if request.method == 'POST':
        # Şifre sıfırlama işlemleri yapılabilir
        messages.success(request, 'Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.')
        return redirect('password_reset_confirmation')
    return render(request, 'password_reset.html')

# Şifre sıfırlama onay sayfası view
def password_reset_confirmation(request):
    return render(request, 'password_reset_confirmation.html')

# Yeni kullanıcı kayıt sayfası view
def signup(request):
    if request.method == 'POST':
        # Kayıt işlemleri yapılabilir
        messages.success(request, 'Kayıt işleminiz başarıyla tamamlandı.')
        return redirect('index')
    return render(request, 'signup.html')
