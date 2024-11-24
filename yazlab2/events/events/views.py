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

# Kullanıcı giriş doğrulama fonksiyonu (dinamik tablo için)
def verify_user(user_table, username, password):
    """Belirtilen tabloya göre kullanıcı doğrulama"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {user_table} WHERE username = %s AND plain_password = %s", (username, password))
        user = cursor.fetchone()
        return user  # Eğer kullanıcı varsa, bilgilerini döndür
    except Exception as e:
        print(f"Veritabanı hatası: {e}")
        return None
    finally:
        cursor.close()


def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Admini doğrula
        admin = verify_user("admin", username, password)  # Admins tablosunda kontrol
        if admin:
            # Admin bilgilerini session'a ekle
            request.session['admin_id'] = admin[0]  # Örnek: admin[0] = AdminID
            request.session['admin_username'] = admin[1]  # Admin kullanıcı adı
            return redirect('admin_dashboard')  # Admin paneline yönlendirme
        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı!")
            return redirect('login_admin')  # Tekrar giriş ekranına yönlendirme
    return render(request, 'login_admin.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Kullanıcıyı doğrula
        user = verify_user("users", username, password)  # Users tablosunda kontrol
        if user:
            # Kullanıcı bilgilerini session'a ekle
            request.session['user_id'] = user[0]  # Örnek: user[0] = UserID
            request.session['username'] = user[1]  # Kullanıcı adı
            return redirect('user_dashboard')  # Kullanıcı paneline yönlendirme
        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı!")
            return redirect('login_user')  # Tekrar giriş ekranına yönlendirme
    return render(request, 'login_user.html')


# Ana sayfa view
def index(request):
    return render(request, 'index.html')

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

def admin_dashboard(request):
    if 'admin_id' not in request.session:  # Admin oturum açmamışsa
        return redirect('login_admin')
    
    # Admin bilgilerini çek
    admin_id = request.session['admin_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin WHERE id = %s", (admin_id,))
    admin = cursor.fetchone()
    cursor.close()

    return render(request, 'admin_dashboard.html', {'admin': admin})


# Kullanıcı kontrol paneli view
def user_dashboard(request):
    if 'user_id' not in request.session:  # Kullanıcı oturum açmamışsa
        return redirect('login_user')
    
    # Kullanıcı bilgilerini çek
    user_id = request.session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    user = {
        'id': user[0],
        'username': user[1],
        'password': user[2],
        'plain_password': user[3],
        'email': user[4],
        'first_name': user[5],
        'last_name': user[6],
        'birth_date': user[7],
        'gender': user[8],
        'phone_number': user[9],
        'interests': user[10],
        'total_points': user[11],
    }

    return render(request, 'user_dashboard.html', {'user': user})



def get_user_info(username):
    # Kullanıcı bilgilerini veritabanından al
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name, email FROM users WHERE username = %s", (username,))
    user_info = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user_info:
        return {
            'first_name': user_info[0],
            'last_name': user_info[1],
            'email': user_info[2],
        }
    return None

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
