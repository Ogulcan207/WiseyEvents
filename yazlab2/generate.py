import mysql.connector
from faker import Faker
import random
import bcrypt

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
            total_points INT DEFAULT 0
        )
    """)

    # Events tablosu
    cursor.execute("""
        CREATE TABLE events (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            description TEXT,
            date DATE,
            time TIME,
            duration TIME,
            location VARCHAR(100),
            category VARCHAR(50)
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
    def __init__(self, username, plain_password, email, first_name, last_name, birth_date, gender, phone_number, interests):
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

    def save(self):
        cursor.execute("""
            INSERT INTO users (username, password, plain_password, email, first_name, last_name, birth_date, gender, phone_number, interests)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (self.username, self.password, self.plain_password, self.email, self.first_name, self.last_name, self.birth_date, self.gender, self.phone_number, self.interests))
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
    def __init__(self, name, description, date, time, duration, location, category):
        self.name = name
        self.description = description
        self.date = date
        self.time = time
        self.duration = duration
        self.location = location
        self.category = category

    def save(self):
        cursor.execute("""
            INSERT INTO events (name, description, date, time, duration, location, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (self.name, self.description, self.date, self.time, self.duration, self.location, self.category))
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
    def __init__(self, sender_id, event_id, message_text, sent_time):
        self.sender_id = sender_id
        self.event_id = event_id
        self.message_text = message_text
        self.sent_time = sent_time

    def save(self):
        cursor.execute("""
            INSERT INTO messages (sender_id, event_id, message_text, sent_time)
            VALUES (%s, %s, %s, %s)
        """, (self.sender_id, self.event_id, self.message_text, self.sent_time))
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

# Faker ile sahte veri ekleme
def add_fake_data():
    # Sahte kullanıcılar
    for _ in range(10):
        user = User(
            username=fake.user_name(),
            plain_password=fake.password(),
            email=fake.email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            birth_date=fake.date_of_birth(minimum_age=18, maximum_age=65),
            gender=fake.random_element(['Erkek', 'Kadın']),
            phone_number=fake.phone_number()[:10],
            interests=", ".join(fake.words(nb=2, ext_word_list=['Spor', 'Müzik', 'Tarih', 'Sanat', 'Teknoloji', 'Siyaset', 'Magazin', 'Edebiyat', 'Eğitim']))
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

    # Sahte etkinlikler
    for _ in range(5):
        event = Event(
            name=fake.catch_phrase(),
            description=fake.text(max_nb_chars=200),
            date=fake.date_this_year(),
            time=fake.time(),
            duration=fake.time(),
            location=fake.city(),
            category=fake.random_element(['Spor', 'Müzik', 'Tarih', 'Sanat', 'Teknoloji', 'Siyaset', 'Magazin', 'Edebiyat', 'Eğitim'])
        )
        event.save()

    # Sahte katılımcılar ve puanlar
    for i in range(1, 6):
        participant = Participant(user_id=i, event_id=random.randint(1, 5))
        participant.save()
        point = Point(user_id=i, points=random.randint(10, 100), earned_date=fake.date_this_year())
        point.save()

    # Sahte mesajlar
    for _ in range(10):
        message = Message(
            sender_id=random.randint(1, 10),
            event_id=random.randint(1, 5),
            message_text=fake.sentence(),
            sent_time=fake.date_time_this_year()
        )
        message.save()

    print("Tüm sahte veriler başarıyla eklendi.")

# Main fonksiyonu
if __name__ == "__main__":
    create_tables()
    add_fake_data()

# Bağlantıyı kapat
cursor.close()
db.close()
import mysql.connector
from faker import Faker
import random
import bcrypt

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
            total_points INT DEFAULT 0
        )
    """)

    # Events tablosu
    cursor.execute("""
        CREATE TABLE events (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            description TEXT,
            date DATE,
            time TIME,
            duration TIME,
            location VARCHAR(100),
            category VARCHAR(50)
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
    def __init__(self, username, plain_password, email, first_name, last_name, birth_date, gender, phone_number, interests):
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

    def save(self):
        cursor.execute("""
            INSERT INTO users (username, password, plain_password, email, first_name, last_name, birth_date, gender, phone_number, interests)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (self.username, self.password, self.plain_password, self.email, self.first_name, self.last_name, self.birth_date, self.gender, self.phone_number, self.interests))
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
    def __init__(self, name, description, date, time, duration, location, category):
        self.name = name
        self.description = description
        self.date = date
        self.time = time
        self.duration = duration
        self.location = location
        self.category = category

    def save(self):
        cursor.execute("""
            INSERT INTO events (name, description, date, time, duration, location, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (self.name, self.description, self.date, self.time, self.duration, self.location, self.category))
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
    def __init__(self, sender_id, event_id, message_text, sent_time):
        self.sender_id = sender_id
        self.event_id = event_id
        self.message_text = message_text
        self.sent_time = sent_time

    def save(self):
        cursor.execute("""
            INSERT INTO messages (sender_id, event_id, message_text, sent_time)
            VALUES (%s, %s, %s, %s)
        """, (self.sender_id, self.event_id, self.message_text, self.sent_time))
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

# Faker ile sahte veri ekleme
def add_fake_data():
    # Sahte kullanıcılar
    for _ in range(10):
        user = User(
            username=fake.user_name(),
            plain_password=fake.password(),
            email=fake.email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            birth_date=fake.date_of_birth(minimum_age=18, maximum_age=65),
            gender=fake.random_element(['Erkek', 'Kadın']),
            phone_number=fake.phone_number()[:10],
            interests=", ".join(fake.words(nb=2, ext_word_list=['Spor', 'Müzik', 'Tarih', 'Sanat', 'Teknoloji', 'Siyaset', 'Magazin', 'Edebiyat', 'Eğitim']))
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

    # Sahte etkinlikler
    for _ in range(5):
        event = Event(
            name=fake.catch_phrase(),
            description=fake.text(max_nb_chars=200),
            date=fake.date_this_year(),
            time=fake.time(),
            duration=fake.time(),
            location=fake.city(),
            category=fake.random_element(['Spor', 'Müzik', 'Tarih', 'Sanat', 'Teknoloji', 'Siyaset', 'Magazin', 'Edebiyat', 'Eğitim'])
        )
        event.save()

    # Sahte katılımcılar ve puanlar
    for i in range(1, 6):
        participant = Participant(user_id=i, event_id=random.randint(1, 5))
        participant.save()
        point = Point(user_id=i, points=random.randint(10, 100), earned_date=fake.date_this_year())
        point.save()

    # Sahte mesajlar
    for _ in range(10):
        message = Message(
            sender_id=random.randint(1, 10),
            event_id=random.randint(1, 5),
            message_text=fake.sentence(),
            sent_time=fake.date_time_this_year()
        )
        message.save()

    print("Tüm sahte veriler başarıyla eklendi.")

# Main fonksiyonu
if __name__ == "__main__":
    create_tables()
    add_fake_data()

# Bağlantıyı kapat
cursor.close()
db.close()
