import mysql.connector
from django.shortcuts import render, redirect
from django.contrib import messages
import bcrypt, random, string, difflib
from datetime import datetime, timedelta, time as dt_time
from .generate import event_images, profile_pictures, hash_password


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
        profile_picture = request.POST.get('profile_picture')  # Profil resmini al

        # Veritabanı bağlantısı
        try:
            cursor.execute(""" 
                UPDATE users 
                SET first_name = %s, last_name = %s, email = %s, phone_number = %s, interests = %s, il = %s, profile_picture = %s 
                WHERE id = %s
            """, (first_name, last_name, email, phone_number, interests, il, profile_picture, user_id))
            conn.commit()
            messages.success(request, 'Profiliniz başarıyla güncellendi.')
            return redirect('user_dashboard')  # Güncelleme sonrası kullanıcı paneline yönlendir
        except mysql.connector.Error as err:
            messages.error(request, f'Hata oluştu: {err}')
        finally:
            cursor.close()
            conn.close()
        
    # GET isteği için profil sayfasını göster
    return render(request, 'profile.html', {'user': user, 'profile_pictures': profile_pictures})  # Kullanıcı bilgilerini gönder

def admin_dashboard(request):
    if 'admin_id' not in request.session:
        return redirect('login_admin')
    
    admin_id = request.session['admin_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # Sütun isimlerini sözlük formatında al
    try:
        # Admin bilgilerini çek
        cursor.execute("SELECT * FROM admin WHERE id = %s", (admin_id,))
        admin = cursor.fetchone()

        # Onay bekleyen etkinlikleri çek
        cursor.execute("SELECT * FROM events WHERE is_ready = FALSE")
        pending_events = cursor.fetchall()

        # Tüm etkinlikleri listele (isteğe bağlı)
        cursor.execute("SELECT * FROM events WHERE is_ready = TRUE")
        approved_events = cursor.fetchall()

        # Tüm kullanıcıları çek (isteğe bağlı)
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

    except mysql.connector.Error as err:
        messages.error(request, f"Veritabanı hatası: {err}")
        pending_events, approved_events, users = [], [], []
    finally:
        cursor.close()
        conn.close()

    return render(request, 'admin_dashboard.html', {
        'admin': admin,
        'pending_events': pending_events,
        'approved_events': approved_events,
        'users': users,
        'profile_pictures': profile_pictures,  # Profil resimlerini gönder
    })



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

    # Kullanıcının katıldığı etkinliklerdeki okunmamış mesaj sayısını al (kendi mesajları hariç)
    cursor.execute("""
        SELECT COUNT(*) AS unread_count
        FROM messages
        WHERE event_id IN (SELECT event_id FROM participants WHERE user_id = %s) AND is_read = FALSE AND sender_id != %s
    """, (user_id, user_id))
    unread_count = cursor.fetchone()['unread_count']

    # Kullanıcıya ait önceki bildirim sayısını saklayın (örneğin, session'da)
    if 'previous_unread_count' not in request.session:
        request.session['previous_unread_count'] = unread_count
    else:
        # Artış miktarını hesaplayın
        new_messages_count = unread_count - request.session['previous_unread_count']
        request.session['previous_unread_count'] = unread_count  # Güncelle

    cursor.close()

    return render(request, 'user_dashboard.html', {
        'user': user,
        'events': events,
        'joined_events': joined_events,
        'created_events': created_events,  # Oluşturulan etkinlikler
        'messages_data': messages_data,  # Oluşturulan etkinliklere ait mesajlar
        'profile_pictures': profile_pictures,  # Profil resimlerini gönder
        'unread_count': unread_count,
        'new_messages_count': new_messages_count if 'new_messages_count' in locals() else 0,
    })



def maps(request, event_id):
    user_id = request.session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT il FROM users WHERE id = %s", (user_id,))
    user_city = cursor.fetchone()

    cursor.execute("SELECT il FROM events WHERE id = %s", (event_id,))
    event_city = cursor.fetchone()

    return render(request, 'maps.html', {
        'event_id': event_id,
        'event_city': event_city,
        'user_city': user_city
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

    # Etkinliğe ait mesajları, kullanıcı adlarını ve profil fotoğraflarını çek
    cursor.execute("""
        SELECT messages.*, users.username, users.profile_picture 
        FROM messages 
        JOIN users ON messages.sender_id = users.id 
        WHERE event_id = %s 
        ORDER BY sent_time ASC
    """, (event_id,))
    messages_data = cursor.fetchall()

    # Mesajları okundu olarak işaretle (kullanıcının kendi mesajları hariç)
    cursor.execute("""
        UPDATE messages
        SET is_read = TRUE
        WHERE event_id = %s AND sender_id != %s AND is_read = FALSE
    """, (event_id, user_id))
    conn.commit()

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
        email = request.POST.get('email')
        last_password = request.POST.get('last_password')

        # Kullanıcının e-posta adresini kontrol et
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            # Benzerlik oranını kontrol et
            similarity = difflib.SequenceMatcher(None, user[3], last_password).ratio()  # user[3] = plain_password
            if similarity >= 0.3:  # benzerlik
                # Yeni rastgele şifre oluştur
                new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))  # 8 karakterli yeni şifre
                hashed_password = hash_password(new_password)  # Yeni şifreyi hash'le

                # Kullanıcının şifresini güncelle
                cursor.execute("UPDATE users SET password = %s, plain_password = %s WHERE id = %s", (hashed_password, new_password, user[0]))
                conn.commit()

                # Yeni şifreyi ekranda göster
                return render(request, 'password_reset_confirmation.html', {'new_password': new_password})
            else:
                messages.error(request, 'Hatırladığınız şifre yeterince benzer değil.')
        else:
            messages.error(request, 'E-posta adresi bulunamadı.')
    
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
        birth_date = request.POST.get('birth_date')  # Doğum tarihi
        gender = request.POST.get('gender')  # Cinsiyet
        phone_number = request.POST.get('phone_number')  # Telefon numarası
        interests = request.POST.get('interests')  # İlgi alanları
        profile_picture = request.POST.get('profile_picture')  # Kullanıcının seçtiği profil resmi
        il = request.POST.get('il')  # İl

        hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Kullanıcıyı veritabanına ekleme
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (username, password, plain_password, email, first_name, last_name, birth_date, gender, phone_number, interests, profile_picture, il, total_points)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (username, hashed_password, plain_password, email, first_name, last_name, birth_date, gender, phone_number, interests, profile_picture, il, 20))  # 20 puan ekleniyor
            conn.commit()
            messages.success(request, 'Kayıt işleminiz başarıyla tamamlandı ve 20 puan kazandınız.')
            return redirect('index')
        except mysql.connector.Error as err:
            messages.error(request, f'Hata oluştu: {err}')
        finally:
            cursor.close()
            conn.close()
    return render(request, 'signup.html', {'profile_pictures': profile_pictures})  # Profil resimlerini gönderin

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
        is_ready = request.POST.get('is_ready')

        # Yeni etkinliğin başlangıç zamanını hesapla
        start_datetime = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), dt_time.fromisoformat(time))
        duration_hours, duration_minutes = map(int, duration.split(':'))
        end_datetime = start_datetime + timedelta(hours=duration_hours, minutes=duration_minutes)

        # Zaman çakışması kontrolü (sadece kullanıcının kendi etkinlikleri)
        cursor.execute("SELECT * FROM events WHERE olusturanid = %s AND id != %s", (user_id, event_id))  # Kullanıcının etkinlikleri
        existing_events = cursor.fetchall()

        # Eğer mevcut etkinlikleri bir sözlük formatında almak istiyorsanız
        columns = [column[0] for column in cursor.description]  # Sütun isimlerini al
        existing_events = [dict(zip(columns, row)) for row in existing_events]  # Her satırı bir sözlük haline getir

        conflict = False
        for existing_event in existing_events:
            existing_start = datetime.combine(existing_event['date'], (datetime.min + existing_event['time']).time())
            if isinstance(existing_event['duration'], timedelta):
                total_seconds = int(existing_event['duration'].total_seconds())
                existing_duration_hours, remainder = divmod(total_seconds, 3600)
                existing_duration_minutes, _ = divmod(remainder, 60)
            else:
                existing_duration_hours, existing_duration_minutes = map(int, existing_event['duration'].split(':'))

            existing_end = existing_start + timedelta(hours=existing_duration_hours, minutes=existing_duration_minutes)

            # Çakışma kontrolü
            if (start_datetime < existing_end and end_datetime > existing_start):
                conflict = True
                break

        if conflict:
            messages.error(request, "Bu etkinlik, mevcut etkinliklerinizle çakışıyor. Lütfen farklı bir zaman seçin.")
            return redirect('edit_event', event_id=event_id)

        # Etkinliği güncelle
        try:
            cursor.execute(""" 
                UPDATE events 
                SET name = %s, description = %s, date = %s, time = %s, duration = %s, category = %s, il = %s, is_ready = %s FALSE
                WHERE id = %s AND olusturanid = %s
            """, (name, description, date, time, duration, category, il, is_ready, event_id, user_id))
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

        # Yeni etkinliğin başlangıç zamanını hesapla
        start_datetime = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), dt_time.fromisoformat(time))
        duration_hours, duration_minutes = map(int, duration.split(':'))
        end_datetime = start_datetime + timedelta(hours=duration_hours, minutes=duration_minutes)

        # Zaman çakışması kontrolü (sadece kullanıcının kendi etkinlikleri)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE olusturanid = %s", (request.session['user_id'],))  # Kullanıcının etkinlikleri
        existing_events = cursor.fetchall()

        # Eğer mevcut etkinlikleri bir sözlük formatında almak istiyorsanız
        columns = [column[0] for column in cursor.description]  # Sütun isimlerini al
        existing_events = [dict(zip(columns, row)) for row in existing_events]  # Her satırı bir sözlük haline getir

        conflict = False
        for event in existing_events:
            existing_start = datetime.combine(event['date'], (datetime.min + event['time']).time())
            if isinstance(event['duration'], timedelta):
                total_seconds = int(event['duration'].total_seconds())
                existing_duration_hours, remainder = divmod(total_seconds, 3600)
                existing_duration_minutes, _ = divmod(remainder, 60)
            else:
                existing_duration_hours, existing_duration_minutes = map(int, event['duration'].split(':'))

            existing_end = existing_start + timedelta(hours=existing_duration_hours, minutes=existing_duration_minutes)

            # Çakışma kontrolü
            if (start_datetime < existing_end and end_datetime > existing_start):
                conflict = True
                break

        if conflict:
            messages.error(request, "Bu etkinlik, mevcut etkinliklerinizle çakışıyor. Lütfen farklı bir zaman seçin.")
            return redirect('create_event')

        # Veritabanına etkinliği ekle
        try:
            cursor.execute(""" 
                INSERT INTO events (name, description, date, time, duration, category, image_url, il, olusturanid, is_ready) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, description, date, time, duration, category, event_images.get(category, ""), il, request.session['user_id'], False))  # is_ready = FALSE
            conn.commit()

            # Kullanıcıya 15 puan ekle
            cursor.execute("UPDATE users SET total_points = total_points + 15 WHERE id = %s", (request.session['user_id'],))
            conn.commit()

            messages.success(request, 'Etkinlik başarıyla oluşturuldu ve onay bekliyor.')
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

def delete_event_admin(request, event_id):
    if 'admin_id' not in request.session:
        return redirect('login_admin')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Etkinliği sil
    try:
        cursor.execute("DELETE FROM participants WHERE event_id = %s", (event_id,))
        cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
        conn.commit()
        messages.success(request, 'Etkinlik başarıyla silindi.')
    except mysql.connector.Error as err:
        messages.error(request, f'Hata oluştu: {err}')
    finally:
        cursor.close()
        conn.close()
    
    return redirect('admin_dashboard')  # Admin paneline yönlendir

def edit_event_admin(request, event_id):
    if 'admin_id' not in request.session:
        return redirect('login_admin')  # If admin is not logged in, redirect to admin login

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Etkinlik bilgilerini çek
    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))  # Pass event_id as a tuple
    event = cursor.fetchone()
    
    # If the request method is POST, update the event details
    if request.method == 'POST':
        
        name = request.POST.get('name')
        description = request.POST.get('description')
        date = request.POST.get('date')
        time = request.POST.get('time')
        duration = request.POST.get('duration')
        category = request.POST.get('category')
        il = request.POST.get('il')
        is_ready = request.POST.get('is_ready') == 'True'  # Convert 'True'/'False' to boolean
        
        try:
            cursor.execute("""
                UPDATE events
                SET name = %s, description = %s, date = %s, time = %s, duration = %s, 
                    category = %s, il = %s, is_ready = %s
                WHERE id = %s
            """, (name, description, date, time, duration, category, il, is_ready, event_id))
            conn.commit()
            messages.success(request, 'Etkinlik başarıyla güncellendi.')
        except mysql.connector.Error as err:
            messages.error(request, f'Hata oluştu: {err}')
            return redirect('admin_dashboard')
        finally:
            cursor.close()
            conn.close()
        
        return redirect('admin_dashboard')
    
    # Render the edit event form with existing data
    return render(request, 'edit_event_admin.html', {'event': event})


def delete_user(request, user_id):
    if 'admin_id' not in request.session:
        return redirect('login_admin')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Kullanıcıyı sil
    try:
        cursor.execute("DELETE FROM participants WHERE user_id = %s", (user_id,))  
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        messages.success(request, 'Kullanıcı başarıyla silindi.')
    except mysql.connector.Error as err:
        messages.error(request, f'Hata oluştu: {err}')
    finally:
        cursor.close()
        conn.close()
    
    return redirect('admin_dashboard')  # Admin paneline yönlendir


def edit_user(request, user_id):
    if 'admin_id' not in request.session:
        return redirect('login_admin')

    # Kullanıcı bilgilerini çek
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    # POST isteği ile güncelleme işlemi
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        interests = request.POST.get('interests')
        il = request.POST.get('city')
        profile_picture = request.POST.get('profile_picture')  # Seçilen profil resmini al

        # Veritabanı güncelleme işlemi
        try:
            cursor.execute("""
                UPDATE users 
                SET first_name = %s, last_name = %s, email = %s, phone_number = %s, interests = %s, il = %s, profile_picture = %s
                WHERE id = %s
            """, (first_name, last_name, email, phone_number, interests, il, profile_picture, user_id))
            conn.commit()
            messages.success(request, 'Kullanıcı bilgileri başarıyla güncellendi.')
            return redirect('admin_dashboard')
        except mysql.connector.Error as err:
            messages.error(request, f'Hata oluştu: {err}')
        finally:
            cursor.close()
            conn.close()

    # GET isteği ile kullanıcı bilgilerini formda gösterme
    return render(request, 'edit_user.html', {'user': user, 'profile_pictures': profile_pictures})


def approve_event(request, event_id):
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE events SET is_ready = TRUE WHERE id = %s", (event_id,))
            conn.commit()
            messages.success(request, "Etkinlik onaylandı.")
        except mysql.connector.Error as err:
            messages.error(request, f"Veritabanı hatası: {err}")
        finally:
            cursor.close()
            conn.close()
    return redirect('admin_dashboard')

def disapprove_event(request, event_id):
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE events SET is_ready = FALSE WHERE id = %s", (event_id,))
            conn.commit()
            messages.success(request, "Etkinlik onayı kaldırıldı.")
        except mysql.connector.Error as err:
            messages.error(request, f"Veritabanı hatası: {err}")
        finally:
            cursor.close()
            conn.close()
    return redirect('admin_dashboard')



def all_events(request):
    if 'user_id' not in request.session:
        return redirect('login_user')

    user_id = request.session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Kullanıcının ilgi alanlarını al
    cursor.execute("SELECT interests FROM users WHERE id = %s", (user_id,))
    user_interests = cursor.fetchone()['interests'].split(',')  # İlgi alanlarını parçala

    # Kullanıcının katıldığı etkinlikleri al
    cursor.execute("SELECT event_id FROM participants WHERE user_id = %s", (user_id,))
    user_joined_events = [row['event_id'] for row in cursor.fetchall()]

    # Kullanıcının oluşturduğu etkinlikleri al
    cursor.execute("SELECT id FROM events WHERE olusturanid = %s", (user_id,))
    user_created_events = [row['id'] for row in cursor.fetchall()]

    # Kullanıcının coğrafi konumunu al (örneğin, şehir)
    cursor.execute("SELECT il FROM users WHERE id = %s", (user_id,))
    user_location = cursor.fetchone()['il']

    # Tüm etkinlikleri al
    cursor.execute("SELECT * FROM events WHERE is_ready = TRUE")
    events = cursor.fetchall()

    # Katılımcı sayısını güncelle
    for event in events:
        cursor.execute("SELECT COUNT(*) as participant_count FROM participants WHERE event_id = %s", (event['id'],))
        participant_count = cursor.fetchone()['participant_count']
        event['participant_count'] = participant_count

        # Kategorileri parçala
        event['categories'] = event['category'].split(',')  # Kategorileri parçala

        # Kullanıcının katıldığı etkinlikleri etkinlik listesine ekle
        event['is_joined'] = event['id'] in user_joined_events
        event['is_created'] = event['id'] in user_created_events

    cursor.close()

    # Filtreleme işlemi
    filtered_events = []
    selected_category = request.GET.get('category')  # Seçilen kategori
    selected_interest = request.GET.get('interest')  # Seçilen ilgi alanı
    selected_location = request.GET.get('location')  # Seçilen şehir

    for event in events:
        category_match = (selected_category is None or selected_category == "" or selected_category in event['categories'])
        interest_match = (selected_interest is None or selected_interest == "" or selected_interest in user_interests)
        location_match = (selected_location is None or selected_location == "" or event['il'] == selected_location)

        if category_match and interest_match and location_match:
            filtered_events.append(event)

    # Tüm kategorileri ayrı ayrı listele
    all_categories = set()
    for event in events:
        all_categories.update(event['categories'])

    return render(request, 'all_events.html', {
        'events': filtered_events,  # Filtrelenmiş etkinlikleri gönder
        'user_joined_events': user_joined_events,
        'user_created_events': user_created_events,
        'categories': sorted(all_categories),  # Kategorileri ayrı ayrı gönder
        'user_interests': user_interests,  # Kullanıcının ilgi alanlarını gönder
        'user_location': user_location,  # Kullanıcının konumunu gönder
    })

def join_event(request, event_id):
    if 'user_id' not in request.session:
        return redirect('login_user')

    user_id = request.session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Katılmak istenen etkinliğin bilgilerini al
    cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    event_to_join = cursor.fetchone()

    if not event_to_join:
        messages.error(request, "Böyle bir etkinlik bulunamadı.")
        return redirect('all_events')

    # Kullanıcının katıldığı etkinlikleri al
    cursor.execute("SELECT event_id FROM participants WHERE user_id = %s", (user_id,))
    user_joined_events = [row['event_id'] for row in cursor.fetchall()]

    # Kullanıcının katıldığı etkinliklerin bilgilerini al
    cursor.execute("SELECT * FROM events WHERE id IN (%s)" % ','.join(['%s'] * len(user_joined_events)), user_joined_events)
    joined_events = cursor.fetchall()

    # Zaman çakışması kontrolü
    conflict = False
    for joined_event in joined_events:
        existing_start = datetime.combine(joined_event['date'], (datetime.min + joined_event['time']).time())
        existing_duration_hours, existing_duration_minutes = map(int, joined_event['duration'].split(':'))
        existing_end = existing_start + timedelta(hours=existing_duration_hours, minutes=existing_duration_minutes)

        # Katılmak istenen etkinliğin başlangıç zamanını ve süresini hesapla
        event_start = datetime.combine(event_to_join['date'], (datetime.min + event_to_join['time']).time())
        event_duration_hours, event_duration_minutes = map(int, event_to_join['duration'].split(':'))
        event_end = event_start + timedelta(hours=event_duration_hours, minutes=event_duration_minutes)

        # Çakışma kontrolü
        if (event_start < existing_end and event_end > existing_start):
            conflict = True
            break

    if conflict:
        messages.error(request, "Bu etkinliğe katılamazsınız, çünkü mevcut etkinliklerinizle çakışıyor.")
        return redirect('all_events')

    # Kullanıcının etkinliğe katılmasını sağla
    try:
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
