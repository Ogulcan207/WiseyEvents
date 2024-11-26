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
    # Kullanıcı oturumu yoksa giriş sayfasına yönlendir
    if 'user_id' not in request.session:
        return redirect('login_user')

    # Kullanıcı bilgilerini çek
    user_id = request.session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    # POST isteği ile güncelleme işlemi
    if request.method == 'POST':
        # Form verilerini al
        user_id = request.POST.get('user_id')  # Kullanıcı ID'sini formdan al
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        interests = request.POST.get('interests')
        il = request.POST.get('il')
        
        # Veritabanı bağlantısı
        try:
            cursor.execute("""
                UPDATE users 
                SET first_name = %s, last_name = %s, email = %s, phone_number = %s, interests = %s, il = %s 
                WHERE id = %s
            """, (first_name, last_name, email, phone_number, interests, il, user_id))
            conn.commit()
            messages.success(request, 'Profiliniz başarıyla güncellendi.')
            return redirect('user_dashboard')  # Güncelleme sonrası kullanıcı paneline yönlendir
        except mysql.connector.Error as err:
            messages.error(request, f'Hata oluştu: {err}')
        finally:
            cursor.close()
            conn.close()
        
    # GET isteği için profil sayfasını göster
    return render(request, 'profile.html', {'user': user})  # Kullanıcı bilgilerini gönder

def admin_dashboard(request):
    print("Session admin_id:", request.session.get('admin_id'))  # Admin ID kontrol
    if 'admin_id' not in request.session:
        print("Admin oturumu bulunamadı. Giriş ekranına yönlendirme.")
        return redirect('login_admin')
    
    # Admin bilgilerini çek
    admin_id = request.session['admin_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin WHERE id = %s", (admin_id,))
    admin = cursor.fetchone()
    cursor.close()

    return render(request, 'admin_dashboard.html', {'admin': admin})


def user_dashboard(request):
    if 'user_id' not in request.session:
        return redirect('login_user')
    
    user_id = request.session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Kullanıcı bilgilerini çek
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    # İlgi alanlarına göre etkinlikleri çek
    interests = user['interests'].split(",")
    format_strings = ','.join(['%s'] * len(interests))
    cursor.execute(f"SELECT * FROM events WHERE category IN ({format_strings})", tuple(interests))
    events = cursor.fetchall()

    # Kullanıcının katıldığı etkinlikleri çek
    cursor.execute("SELECT * FROM events WHERE id IN (SELECT event_id FROM participants WHERE user_id = %s)", (user_id,))
    joined_events = cursor.fetchall()

    # Kullanıcının oluşturduğu etkinlikleri çek
    cursor.execute("SELECT * FROM events WHERE olusturanid = %s", (user_id,))
    created_events = cursor.fetchall()

    cursor.close()

    return render(request, 'user_dashboard.html', {
        'user': user,
        'events': events,
        'joined_events': joined_events,
        'created_events': created_events  # Oluşturulan etkinlikler
    })




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

def edit_event(request, event_id):
    if 'user_id' not in request.session:
        return redirect('login_user')
    
    user_id = request.session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Etkinlik bilgilerini çek
    cursor.execute("SELECT * FROM events WHERE id = %s AND olusturanid = %s", (event_id, user_id))
    event = cursor.fetchone()
    
    if not event:
        messages.error(request, "Bu etkinliği düzenleme yetkiniz yok.")
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        # Form verilerini al ve güncelle
        name = request.POST.get('name')
        description = request.POST.get('description')
        date = request.POST.get('date')
        time = request.POST.get('time')
        duration = request.POST.get('duration')
        category = request.POST.get('category')
        
        try:
            cursor.execute("""
                UPDATE events 
                SET name = %s, description = %s, date = %s, time = %s, duration = %s, category = %s
                WHERE id = %s AND olusturanid = %s
            """, (name, description, date, time, duration, category, event_id, user_id))
            conn.commit()
            messages.success(request, 'Etkinlik başarıyla güncellendi.')
        except mysql.connector.Error as err:
            messages.error(request, f'Hata oluştu: {err}')
        finally:
            cursor.close()
            conn.close()
        
        return redirect('user_dashboard')
    
    cursor.close()
    return render(request, 'edit_event.html', {'event': event})
