import mysql.connector
from faker import Faker
import random
import bcrypt
from datetime import datetime, timedelta

# Veritabanına bağlanma
db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="200!Voxor",
    database="akillietkinlik"
)
cursor = db.cursor()

# Faker nesnesi
fake = Faker('tr_TR')

# Şifre hash'leme fonksiyonu
def hash_password(password):
    password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password, salt)

# Tabloları oluşturma
def create_tables():
    cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
    cursor.execute("DROP TABLE IF EXISTS users, events, participants, messages, points, admin")

    # Users tablosu
    cursor.execute("""
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(100),
            plain_password VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            birth_date DATE,
            gender ENUM('Erkek', 'Kadın'),
            phone_number VARCHAR(20),
            interests TEXT,
            profile_picture VARCHAR(255),
            il VARCHAR(50),
            total_points INT DEFAULT 20
        )
    """)

    # Events tablosu (is_ready alanı eklenmiş)
    cursor.execute("""
        CREATE TABLE events (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            description TEXT,
            date DATE,
            time TIME,
            duration TIME,
            category VARCHAR(50),
            image_url VARCHAR(255),
            il VARCHAR(50),
            olusturanid INT,
            is_ready BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (olusturanid) REFERENCES users(id)
        )
    """)

    # Participants tablosu
    cursor.execute("""
        CREATE TABLE participants (
            user_id INT,
            event_id INT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    """)

    # Messages tablosu
    cursor.execute("""
        CREATE TABLE messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_id INT,
            event_id INT,
            message_text TEXT,
            sent_time TIMESTAMP,
            is_read BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    """)

    # Points tablosu
    cursor.execute("""
        CREATE TABLE points (
            user_id INT,
            points INT,
            earned_date DATE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Admin tablosu
    cursor.execute("""
        CREATE TABLE admin (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(100),
            plain_password VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            first_name VARCHAR(50),
            last_name VARCHAR(50)
        )
    """)

    cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
    db.commit()
    print("Tablolar başarıyla oluşturuldu.")

# Kullanıcı sınıfı
class User:
    def __init__(self, username, plain_password, email, first_name, last_name, birth_date, gender, phone_number, interests, profile_picture, il):
        self.username = username
        self.password = hash_password(plain_password)
        self.plain_password = plain_password
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        self.gender = gender
        self.phone_number = phone_number
        self.interests = interests
        self.profile_picture = profile_picture
        self.il = il

    def save(self):
        cursor.execute("""
            INSERT INTO users (username, password, plain_password, email, first_name, last_name, birth_date, gender, phone_number, interests, profile_picture, il)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (self.username, self.password, self.plain_password, self.email, self.first_name, self.last_name, self.birth_date, self.gender, self.phone_number, self.interests, self.profile_picture, self.il))
        db.commit()

# Admin sınıfı
class Admin:
    def __init__(self, username, plain_password, email, first_name, last_name):
        self.username = username
        self.password = hash_password(plain_password)
        self.plain_password = plain_password
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

    def save(self):
        cursor.execute("""
            INSERT INTO admin (username, password, plain_password, email, first_name, last_name)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (self.username, self.password, self.plain_password, self.email, self.first_name, self.last_name))
        db.commit()

# Etkinlik sınıfı
class Event:
    def __init__(self, name, description, date, time, duration, category, image_url, il, olusturanid, is_ready=True):
        self.name = name
        self.description = description
        self.date = date
        self.time = time
        self.duration = duration
        self.category = category
        self.image_url = image_url
        self.il = il
        self.olusturanid = olusturanid
        self.is_ready = is_ready  # Admin onay durumu

    def save(self):
        cursor.execute(""" 
            INSERT INTO events (name, description, date, time, duration, category, image_url, il, olusturanid, is_ready)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (self.name, self.description, self.date, self.time, self.duration, self.category, self.image_url, self.il, self.olusturanid, self.is_ready))
        
        # Etkinliği oluşturan kullanıcıyı participants tablosuna ekle
        cursor.execute("INSERT INTO participants (user_id, event_id) VALUES (%s, LAST_INSERT_ID())", (self.olusturanid,))
        
        db.commit()

# Katılımcı sınıfı
class Participant:
    def __init__(self, user_id, event_id):
        self.user_id = user_id
        self.event_id = event_id

    def save(self):
        cursor.execute("INSERT INTO participants (user_id, event_id) VALUES (%s, %s)", (self.user_id, self.event_id))
        db.commit()

# Mesaj sınıfı
class Message:
    def __init__(self, sender_id, event_id, message_text, sent_time, is_read=False):
        self.sender_id = sender_id
        self.event_id = event_id
        self.message_text = message_text
        self.sent_time = sent_time
        self.is_read = is_read  # Okundu bilgisi

    def save(self):
        cursor.execute("""
            INSERT INTO messages (sender_id, event_id, message_text, sent_time, is_read)
            VALUES (%s, %s, %s, %s, %s)
        """, (self.sender_id, self.event_id, self.message_text, self.sent_time, self.is_read))
        db.commit()

# Puan sınıfı
class Point:
    def __init__(self, user_id, points, earned_date):
        self.user_id = user_id
        self.points = points
        self.earned_date = earned_date

    def save(self):
        cursor.execute("""
            INSERT INTO points (user_id, points, earned_date)
            VALUES (%s, %s, %s)
        """, (self.user_id, self.points, self.earned_date))

        # Users tablosunda toplam puanı güncelle
        cursor.execute("""
            UPDATE users
            SET total_points = total_points + %s
            WHERE id = %s
        """, (self.points, self.user_id))
        db.commit()

# Profil resim dosya yolları
profile_pictures = [
    "/static/profil/profil0.jpg",
    "/static/profil/profil1.jpg",
    "/static/profil/profil2.jpg",
    "/static/profil/profil3.jpg",
    "/static/profil/profil4.jpg",
    "/static/profil/profil5.jpg",
    "/static/profil/profil6.jpg",
    "/static/profil/profil7.jpg",
    "/static/profil/profil8.jpg",
    "/static/profil/profil9.jpg",
    "/static/profil/profil10.jpg",
    "/static/profil/profil11.jpg",
    "/static/profil/profil12.jpg"
]

# Etkinlik resim linkleri
event_images = {
    "Tiyatro": "/static/event/tiyatro.jpg",
    "Sinema": "/static/event/sinema.jpg",
    "Opera": "/static/event/opera.jpg",
    "Konser": "/static/event/konser.jpg",
    "Kitap Tanıtımı": "/static/event/kitap.jpg",
    "Parti": "/static/event/parti.jpg",
    "Halısaha": "/static/event/halısaha.jpg",
    "Sergi": "/static/event/sergi.jpg",
    "Festival": "/static/event/festival.jpg"
}

# Etkinliklerin birden fazla ilgi alanıyla eşleşmesi
event_categories = {
    "Kitap Tanıtımı": ["Edebiyat", "Eğitim"],
    "Tiyatro": ["Sanat", "Edebiyat"],
    "Sinema": ["Sanat", "Edebiyat"],
    "Opera": ["Sanat", "Tarih"],
    "Konser": ["Müzik", "Sanat"],
    "Parti": ["Eğlence"],
    "Halısaha":["Eğlence", "Spor"],
    "Festival": ["Eğlence", "Kültür"],
    "Sergi": ["Sanat", "Kültür"]
}

cities = [
    "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", 
    "Adana", "Konya", "Gaziantep", "Kayseri", "Eskişehir",
    "Samsun", "Trabzon", "Denizli", "Şanlıurfa", "Mardin"
]


# Faker ile sahte veri ekleme
def add_fake_data():
    existing_emails = set()  # Mevcut e-posta adreslerini saklamak için bir küme
    existing_events = []  # Mevcut etkinliklerin tarih ve saatlerini saklamak için bir liste

    # Sahte kullanıcılar
    for _ in range(50):
        email = fake.email()
        while email in existing_emails:  # E-posta adresinin benzersiz olmasını sağla
            email = fake.email()
        existing_emails.add(email)  # E-posta adresini küme ekle

        user = User(
            username=fake.user_name(),
            plain_password=fake.password(),
            email=email,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            birth_date=fake.date_of_birth(minimum_age=18, maximum_age=65),
            gender=fake.random_element(['Erkek', 'Kadın']),
            phone_number=fake.phone_number()[:10],
            interests=", ".join(fake.words(nb=2, ext_word_list=['Spor', 'Eğlence', 'Müzik', 'Tarih', 'Sanat', 'Teknoloji', 'Siyaset', 'Magazin', 'Edebiyat', 'Eğitim'])),
            profile_picture=random.choice(profile_pictures),  # Profil resmini rastgele seç
            il=random.choice(cities)
        )
        user.save()

    # Sahte admin
    admin = Admin(
        username="admin",
        plain_password="admin123",
        email="admin@example.com",
        first_name="Admin",
        last_name="User"
    )
    admin.save()

    # Create fake events using event_images
    events = []  # Etkinlikleri saklamak için bir liste oluştur
    for event_name, image_url in event_images.items():
        for _ in range(3):  # Her etkinlik için 3 farklı etkinlik oluştur
            olusturanid = random.randint(1, 50)  # Rastgele kullanıcı ID'si
            duration = random.choice(["2:00:00", "3:00:00", "1:30:00", "1:00:00", "2:30:00", "0:30:00"])  # Rastgele süre seçimi
            
            # Yeni etkinliğin tarih ve saatini oluştur
            event_date = fake.date_this_year()
            event_time_str = fake.time()  # Zamanı string olarak al
            event_time = datetime.strptime(event_time_str, "%H:%M:%S").time()  # String'i datetime.time nesnesine dönüştür

            start_datetime = datetime.combine(event_date, event_time)
            end_datetime = start_datetime + timedelta(hours=int(duration.split(':')[0]), minutes=int(duration.split(':')[1]))

            # Zaman çakışması kontrolü
            conflict = False
            for existing_event in existing_events:
                if (start_datetime < existing_event['end'] and end_datetime > existing_event['start']):
                    conflict = True
                    break

            if conflict:
                continue  # Çakışma varsa bu etkinliği atla

            # Etkinliği oluştur
            event = Event(
                name=event_name,
                description=fake.text(max_nb_chars=200),
                date=event_date,
                time=event_time_str,  # Zamanı string olarak sakla
                duration=duration,  # Süreyi burada kullan
                category=", ".join(event_categories.get(event_name, [])),  # Kategorileri al
                image_url=image_url,  # event_images dizisinden resim URL'si
                il=random.choice(cities),  # Rastgele şehir
                olusturanid=olusturanid  # Rastgele kullanıcı ID'si
            )
            events.append(event)  # Oluşturulan etkinliği listeye ekle
            existing_events.append({'start': start_datetime, 'end': end_datetime})  # Mevcut etkinlikleri güncelle

            # Kullanıcıya 15 puan ekle
            cursor.execute("UPDATE users SET total_points = total_points + 15 WHERE id = %s", (olusturanid,))
            db.commit()

    random.shuffle(events)  # Etkinlikleri rastgele sırala
    for event in events:  # Rastgele sıralanmış etkinlikleri kaydet
        event.save()

    print("Tüm sahte veriler başarıyla eklendi.")

# Sahte katılımcılar ve puan ekleme
def add_fake_participants():
    event_count = cursor.execute("SELECT COUNT(*) FROM events")  # Etkinlik sayısını al
    total_events = cursor.fetchone()[0]  # İlk satırı al

    for user_id in range(1, 51):  # 50 kullanıcı olduğunu varsayıyoruz
        participated_events = set()  # Kullanıcının katıldığı etkinlikleri saklamak için bir küme
        # Her kullanıcı için rastgele 1-3 etkinliğe katılım oluştur
        for _ in range(random.randint(1, 3)):
            event_id = random.randint(1, total_events)  # Dinamik etkinlik sayısını kullan
            if event_id not in participated_events:  # Eğer kullanıcı bu etkinliğe katılmadıysa
                cursor.execute("INSERT INTO participants (user_id, event_id) VALUES (%s, %s)", (user_id, event_id))
                participated_events.add(event_id)  # Etkinliği küme ekle
                
                # Kullanıcının toplam puanını artır
                cursor.execute("""
                    UPDATE users
                    SET total_points = total_points + 10
                    WHERE id = %s
                """, (user_id,))
    db.commit()
    print("Sahte katılımcılar başarıyla eklendi.")

# Main fonksiyonu
if __name__ == "__main__":
    create_tables()
    add_fake_data()
    add_fake_participants()
    
# Bağlantıyı kapat
cursor.close()
db.close()
