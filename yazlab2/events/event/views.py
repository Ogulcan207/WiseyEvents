import mysql.connector
from django.shortcuts import render, redirect
from django.contrib import messages
import bcrypt

# Veritabanı bağlantısını kurma fonksiyonu
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="200!Voxor",
        database="akillietkinlik"
    )

# Kullanıcı doğrulama fonksiyonu
def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        hashed_password = result[0]
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            return True
    return False

# Admin doğrulama fonksiyonu
def verify_admin(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM admin WHERE username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        hashed_password = result[0]
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            return True
    return False

# Ana sayfa view
def index(request):
    return render(request, 'index.html')

# Admin giriş view
def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if verify_admin(username, password):
            # Başarılı giriş
            return redirect('admin_dashboard')
        else:
            # Başarısız giriş durumunda uyarı mesajı
            messages.error(request, 'Kullanıcı adı veya şifre yanlış.')
            return render(request, 'login_admin.html')
        
    return render(request, 'login_admin.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if verify_user(username, password):
            # Başarılı giriş
            return redirect('user_dashboard')
        else:
            # Hatalı girişte hata mesajı ekle
            messages.error(request, 'Geçersiz kullanıcı adı veya şifre.')
            return render(request, 'login_user.html')
    
    # GET isteğinde yalnızca formu göster, hata mesajı ekleme
    return render(request, 'login_user.html')

# Profil güncelleme view fonksiyonu
def update_profile(request):
    if request.method == 'POST':
        # Form verilerini al
        user_id = request.session.get('user_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        interests = request.POST.get('interests')
        
        # Veritabanı bağlantısı
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Kullanıcı bilgilerini güncelleme
            cursor.execute("""
                UPDATE users 
                SET first_name = %s, last_name = %s, email = %s, phone_number = %s, interests = %s 
                WHERE id = %s
            """, (first_name, last_name, email, phone_number, interests, user_id))
            conn.commit()
            messages.success(request, 'Profiliniz başarıyla güncellendi.')
        except mysql.connector.Error as err:
            messages.error(request, f'Hata oluştu: {err}')
        finally:
            cursor.close()
            conn.close()
        
        return redirect('user_dashboard')
    return redirect('user_dashboard')

# Admin kontrol paneli view
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

# Kullanıcı kontrol paneli view
def user_dashboard(request):
    return render(request, 'user_dashboard.html')

# Şifre sıfırlama view
def password_reset(request):
    if request.method == 'POST':
        # Şifre sıfırlama işlemleri yapılabilir
        messages.success(request, 'Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.')
        return redirect('password_reset_confirmation')
    return render(request, 'password_reset.html')

# Şifre sıfırlama onayı view
def password_reset_confirmation(request):
    return render(request, 'password_reset_confirmation.html')

# Yeni kullanıcı kayıt view
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        plain_password = request.POST.get('password')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Kullanıcıyı veritabanına ekleme
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (username, password, plain_password, email, first_name, last_name)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, hashed_password, plain_password, email, first_name, last_name))
            conn.commit()
            messages.success(request, 'Kayıt işleminiz başarıyla tamamlandı.')
            return redirect('index')
        except mysql.connector.Error as err:
            messages.error(request, f'Hata oluştu: {err}')
        finally:
            cursor.close()
            conn.close()
    return render(request, 'signup.html')
