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
    cursor.execute("DROP TABLE IF EXISTS users, events, participants, messages, points")

    # Users tablosu
    cursor.execute("""
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(100),
            plain_password VARCHAR(100),  -- Düz metin şifreyi saklamak için sütun
            email VARCHAR(100) UNIQUE,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            birth_date DATE,
            gender ENUM('Erkek', 'Kadın'),
            phone_number VARCHAR(20),
            interests TEXT,
            total_points INT DEFAULT 0  -- Toplam puan sütunu                               
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

    cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
    db.commit()
    print("Tablolar başarıyla oluşturuldu.")

# Faker ile sahte kullanıcı ekleme
def add_fake_users(count):
    for _ in range(count):
        username = fake.user_name()
        plain_password = fake.password()  # Düz metin olarak saklanacak şifre
        hashed_password = hash_password(plain_password)  # Hashlenmiş şifre
        email = fake.email()
        first_name = fake.first_name()
        last_name = fake.last_name()
        birth_date = fake.date_of_birth(minimum_age=18, maximum_age=65)
        gender = fake.random_element(['Erkek', 'Kadın'])
        phone_number = fake.phone_number()[:10]
        interests = ", ".join(fake.words(nb=2, ext_word_list=['Spor', 'Müzik', 'Tarih', 'Sanat', 'Teknoloji', 'Siyaset', 'Magazin', 'Edebiyat', 'Eğitim']))

        cursor.execute("""
            INSERT INTO users (username, password, plain_password, email, first_name, last_name, birth_date, gender, phone_number, interests)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (username, hashed_password, plain_password, email, first_name, last_name, birth_date, gender, phone_number, interests))
    db.commit()
    print(f"{count} sahte kullanıcı eklendi.")

# Sahte etkinlik ekleme
def add_fake_events(count):
    for _ in range(count):
        name = fake.catch_phrase()
        description = fake.text(max_nb_chars=200)
        date = fake.date_this_year()
        time = fake.time()
        duration = fake.time()
        location = fake.city()
        category = fake.random_element(['Spor', 'Müzik', 'Tarih', 'Sanat', 'Teknoloji', 'Siyaset', 'Magazin', 'Edebiyat', 'Eğitim'])

        cursor.execute("""
            INSERT INTO events (name, description, date, time, duration, location, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, description, date, time, duration, location, category))
    db.commit()
    print(f"{count} sahte etkinlik eklendi.")

# Sahte katılımcı ekleme
def add_fake_participants(user_count, event_count):
    for _ in range(user_count):
        user_id = random.randint(1, user_count)
        event_id = random.randint(1, event_count)
        cursor.execute("INSERT INTO participants (user_id, event_id) VALUES (%s, %s)", (user_id, event_id))
    db.commit()
    print(f"{user_count} sahte katılımcı eklendi.")

# Sahte mesaj ekleme
def add_fake_messages(count, user_count, event_count):
    for _ in range(count):
        sender_id = random.randint(1, user_count)
        event_id = random.randint(1, event_count)
        message_text = fake.sentence()
        sent_time = fake.date_time_this_year()

        cursor.execute("""
            INSERT INTO messages (sender_id, event_id, message_text, sent_time)
            VALUES (%s, %s, %s, %s)
        """, (sender_id, event_id, message_text, sent_time))
    db.commit()
    print(f"{count} sahte mesaj eklendi.")

# Sahte puan ekleme (katılımcı kullanıcılar için)
def add_fake_points(count):
    # Katılımcı kullanıcıların ID'lerini alalım
    cursor.execute("SELECT DISTINCT user_id FROM participants")
    participant_ids = [row[0] for row in cursor.fetchall()]

    for _ in range(count):
        user_id = random.choice(participant_ids)  # Rastgele bir katılımcı seç
        points = random.randint(10, 100)          # Rastgele puan belirle
        earned_date = fake.date_this_year()       # Rastgele tarih oluştur

        # Points tablosuna puan kaydı ekle
        cursor.execute("""
            INSERT INTO points (user_id, points, earned_date)
            VALUES (%s, %s, %s)
        """, (user_id, points, earned_date))

        # Users tablosunda toplam puanı güncelle
        cursor.execute("""
            UPDATE users
            SET total_points = total_points + %s
            WHERE id = %s
        """, (points, user_id))

    db.commit()
    print(f"{count} katılımcı için sahte puan kaydı eklendi ve toplam puan güncellendi.")



# Main fonksiyonu
if __name__ == "__main__":
    create_tables()
    add_fake_users(10)          # 10 sahte kullanıcı ekler
    add_fake_events(5)          # 5 sahte etkinlik ekler
    add_fake_participants(10, 5) # Katılımcı ekler
    add_fake_messages(10, 10, 5) # Mesaj ekler
    add_fake_points(10)     # Puan ekler
    print("Tüm sahte veriler başarıyla eklendi.")

# Bağlantıyı kapat
cursor.close()
db.close()
