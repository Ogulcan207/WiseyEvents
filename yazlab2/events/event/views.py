import mysql.connector
from django.shortcuts import render, redirect
from django.contrib import messages
import bcrypt
from datetime import datetime
from .generate import event_images


# Veritabanı bağlantısını kurma fonksiyonu
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="159753Ubeyd",
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

    # Kullanıcının oluşturduğu etkinliklere ait mesajları çek
    messages_data = []
    for event in created_events:
        cursor.execute("SELECT * FROM messages WHERE event_id = %s ORDER BY sent_time ASC", (event['id'],))
        messages = cursor.fetchall()
        messages_data.append({
            'event': event,
            'messages': messages,
            'image_url': event['image_url']  # Etkinlik resmini ekle
        })

    cursor.close()

    return render(request, 'user_dashboard.html', {
        'user': user,
        'events': events,
        'joined_events': joined_events,
        'created_events': created_events,  # Oluşturulan etkinlikler
        'messages_data': messages_data  # Oluşturulan etkinliklere ait mesajlar
    })


def event_messages(request, event_id):
    if 'user_id' not in request.session:
        return redirect('login_user')

    user_id = request.session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Etkinlik bilgilerini çek
    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()

    if not event:
        messages.error(request, "Böyle bir etkinlik bulunamadı.")
        return redirect('user_dashboard')

    # Etkinliğe ait mesajları çek
    cursor.execute("SELECT * FROM messages WHERE event_id = %s ORDER BY sent_time ASC", (event_id,))
    messages_data = cursor.fetchall()

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            try:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    INSERT INTO messages (sender_id, event_id, message_text, sent_time)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, event_id, content, current_time))
                conn.commit()
                messages.success(request, 'Mesaj başarıyla gönderildi.')
            except mysql.connector.Error as err:
                messages.error(request, f'Hata oluştu: {err}')
        return redirect('event_messages', event_id=event_id)

    cursor.close()
    conn.close()

    return render(request, 'event_messages.html', {
        'event': event,
        'messages': messages_data,
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
        il = request.POST.get('il')
        
        try:
            cursor.execute(""" 
                UPDATE events 
                SET name = %s, description = %s, date = %s, time = %s, duration = %s, category = %s, il = %s
                WHERE id = %s AND olusturanid = %s
            """, (name, description, date, time, duration, category, il, event_id, user_id))
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

def create_event(request):
    if 'user_id' not in request.session:
        return redirect('login_user')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        date = request.POST.get('date')
        time = request.POST.get('time')
        duration = request.POST.get('duration')
        category = request.POST.get('category')
        il = request.POST.get('il')
        
        # Veritabanı bağlantısını kur
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(""" 
                INSERT INTO events (name, description, date, time, duration, category, image_url, il, olusturanid) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, description, date, time, duration, category, event_images.get(category, ""), il, request.session['user_id']))
            conn.commit()

            # Kullanıcıya 15 puan ekle
            cursor.execute("UPDATE users SET points = points + 15 WHERE id = %s", (request.session['user_id'],))
            conn.commit()

            messages.success(request, 'Etkinlik başarıyla oluşturuldu ve 15 puan kazandınız.')
            return redirect('user_dashboard')
        except mysql.connector.Error as err:
            messages.error(request, f'Hata oluştu: {err}')
        finally:
            cursor.close()
            conn.close()
        return redirect('user_dashboard')
    return render(request, 'create_event.html', {'event_images': event_images})

def delete_event(request, event_id):
    if 'user_id' not in request.session:
        return redirect('login_user')
    
    user_id = request.session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Etkinliği sil
    try:
        cursor.execute("DELETE FROM events WHERE id = %s AND olusturanid = %s", (event_id, user_id))
        conn.commit()
        messages.success(request, 'Etkinlik başarıyla silindi.')
    except mysql.connector.Error as err:
        messages.error(request, f'Hata oluştu: {err}')
    finally:
        cursor.close()
        conn.close()
    
    return redirect('user_dashboard')  # Kullanıcı paneline yönlendir

def all_events(request):
    if 'user_id' not in request.session:
        return redirect('login_user')

    user_id = request.session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Kullanıcının ilgi alanlarını al
    cursor.execute("SELECT interests FROM users WHERE id = %s", (user_id,))
    user_interests = cursor.fetchone()['interests'].split(',')

    # Kullanıcının katıldığı etkinlikleri al
    cursor.execute("SELECT event_id FROM participants WHERE user_id = %s", (user_id,))
    user_joined_events = [row['event_id'] for row in cursor.fetchall()]

    # Kullanıcının coğrafi konumunu al (örneğin, şehir)
    cursor.execute("SELECT il FROM users WHERE id = %s", (user_id,))
    user_location = cursor.fetchone()['il']

    # Tüm etkinlikleri al
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()

    # Etkinlikleri filtrele ve sıralama yap
    recommended_events = filter_and_sort_events(events, user_interests, user_joined_events, user_location)

    cursor.close()

    return render(request, 'all_events.html', {
        'events': recommended_events,
        'user_joined_events': user_joined_events,
        'categories': list(set(event['category'] for event in events))  # Kategorileri benzersiz hale getir
    })

def join_event(request, event_id):
    if 'user_id' not in request.session:
        return redirect('login_user')

    user_id = request.session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Kullanıcının etkinliğe katılmasını sağla
        cursor.execute("INSERT INTO participants (user_id, event_id) VALUES (%s, %s)", (user_id, event_id))
        conn.commit()

        # Kullanıcıya 10 puan ekle
        cursor.execute("UPDATE users SET points = points + 10 WHERE id = %s", (user_id,))
        conn.commit()

        messages.success(request, 'Etkinliğe katıldınız ve 10 puan kazandınız.')
    except mysql.connector.Error as err:
        messages.error(request, f'Hata oluştu: {err}')
    finally:
        cursor.close()
        conn.close()

    return redirect('all_events')  # Katıldıktan sonra tüm etkinlikler sayfasına yönlendir

def filter_and_sort_events(events, user_interests, user_joined_events, user_location):
    recommended_events = []

    # İlgi alanına göre öneri
    for event in events:
        if any(interest in event['category'] for interest in user_interests):
            recommended_events.append((event, 3))  # İlgi alanı uyumu için yüksek puan

    # Katılım geçmişine göre öneri
    for event in events:
        if event['id'] in user_joined_events:
            recommended_events.append((event, 2))  # Katılım geçmişi için orta puan

    # Coğrafi konuma göre öneri
    for event in events:
        if event['il'] == user_location:
            recommended_events.append((event, 1))  # Coğrafi konum için düşük puan

    # Önerileri puanlarına göre sırala
    recommended_events.sort(key=lambda x: x[1], reverse=True)

    # Sadece etkinlikleri döndür
    return [event for event, _ in recommended_events]