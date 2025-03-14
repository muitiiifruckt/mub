import hashlib
from sqlalchemy import create_engine, Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Создаем базовый класс для моделей
Base = declarative_base()

# Определяем модель User
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(32), nullable=False)  # MD5-хэш всегда 32 символа

    __table_args__ = (UniqueConstraint('username', name='unique_username'),)

# Создаем соединение с базой данных (SQLite)
engine = create_engine('sqlite:///users.db', echo=False)
Base.metadata.create_all(engine)

# Создаем фабрику сессий
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

# Функция для хэширования пароля
def hash_password(password):
    return hashlib.md5(password.encode('utf-8')).hexdigest()

# Функция для добавления нового пользователя
def add_user(username, password):
    session = get_session()
    try:
        hashed_password = hash_password(password)
        new_user = User(username=username, password=hashed_password)
        session.add(new_user)
        session.commit()
        print(f"Пользователь {username} успешно добавлен.")
        return True
    except Exception as e:
        session.rollback()
        print(f"Ошибка при добавлении пользователя: {e}")
        return False
    finally:
        session.close()

def check_username(username):
    session = get_session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user:
            print(f"Пользователь {username} существует.")
            return True
        else:
            print("Пользователь несуществует")
            return False
    finally:
        session.close()
# Функция для проверки логина и пароля
def check_user(username, password):
    session = get_session()
    try:
        hashed_password = hash_password(password)
        user = session.query(User).filter_by(username=username, password=hashed_password).first()
        
        if user:
            print(f"Пользователь {username} авторизован.")
            return True
        else:
            print("Неверный логин или пароль.")
            return False
    finally:
        session.close()
def check_user_word_order(username, password):
    session = get_session()
    try:
        hashed_password = hash_password(password)
        user = session.query(User).filter_by(username=username, password=hashed_password).first()
        if user:
            print(f"Пользователь {username} авторизован.")
            return True
        else:
            print("Неверный логин или пароль.")
            return False
    finally:
        session.close()
def get_password_hash(username):
    session = get_session()
    try:

        user = session.query(User).filter_by(username=username).first()
        if user:
            return user.password
        else:
            print("Неверный логин или пароль.")
            return False
    finally:
        session.close()
# Код ниже теперь выполняется только при прямом запуске скрипта
if __name__ == "__main__":
    add_user('user1', 'password123')
    add_user('user2', 'qwerty')
    check_user('user1', 'password123')  # Успешная авторизация
    check_user('user1', 'wrongpassword')  # Неверный пароль
