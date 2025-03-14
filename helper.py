import socket
import threading
import hashlib
import random
import string
import logging
from sqlalchemy import create_engine, Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import add_user, check_user, check_username
# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

def md5(text):
    hashed = hashlib.md5(text.encode('utf-8')).hexdigest()
    logging.info(f"MD5('{text}') = {hashed}")
    return hashed

def gen_str(length=32):
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    logging.info(f"Generated nonce: {random_str}")
    return random_str

def get_password_hash(username):
    session = get_session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user:
            logging.info(f"User '{username}' found with stored hash: {user.password}")
        else:
            logging.warning(f"User '{username}' not found.")
        return user.password if user else None
    finally:
        session.close()

def authenticate_client(conn):
    username = conn.recv(1024).decode()
    logging.info(f"Received username: {username}")
    stored_hash = get_password_hash(username)
    if not stored_hash:
        conn.sendall(b'FAIL')
        logging.warning("Authentication failed: User not found.")
        return False
    nonce = gen_str()
    conn.sendall(nonce.encode())
    client_hash = conn.recv(1024).decode()
    logging.info(f"Received client hash: {client_hash}")
    server_hash = md5(nonce + stored_hash)
    logging.info(f"Computed server hash: {server_hash}")
    if client_hash == server_hash:
        conn.sendall(b'SUCCESS')
        logging.info("Client authentication successful.")
        return True
    else:
        conn.sendall(b'FAIL')
        logging.warning("Authentication failed: Hash mismatch.")
        return False

def handle_client(conn, addr):
    logging.info(f"Connection from {addr}")
    if authenticate_client(conn):
        logging.info("Client authenticated successfully.")
        threading.Thread(target=receive_messages, args=(conn, "Client"), daemon=True).start()
        while True:
            msg = input("Server: ")
            if msg.lower() == 'exit':
                break
            conn.sendall(msg.encode())
    conn.close()

def receive_messages(sock, name):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            logging.info(f"{name} sent: {data.decode()}")
            print(f"\n{name}: {data.decode()}")
        except:
            break

def start_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    logging.info(f"Listening on {host}:{port}")
    conn, addr = server.accept()
    handle_client(conn, addr)
    server.close()

def start_client(host, port, username, password):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    logging.info(f"Connecting to {host}:{port} as {username}")
    sock.sendall(username.encode())
    nonce = sock.recv(1024).decode()
    logging.info(f"Received nonce: {nonce}")
    if nonce == 'FAIL':
        logging.warning("Authentication failed: User not found.")
        return
    hashed_password = md5(password)
    final_hash = md5(nonce + hashed_password)
    logging.info(f"Computed final hash to send: {final_hash}")
    sock.sendall(final_hash.encode())
    response = sock.recv(1024).decode()
    if response == 'SUCCESS':
        logging.info("Authenticated successfully.")
        threading.Thread(target=receive_messages, args=(sock, "Server"), daemon=True).start()
        while True:
            msg = input("Client: ")
            if msg.lower() == 'exit':
                break
            sock.sendall(msg.encode())
    else:
        logging.warning("Authentication failed.")
    sock.close()

def main():
    host = "127.0.0.1"
    port = 5000
    mode = input("Enter 'server' or 'client': ").strip().lower()
    if mode == 'server':
        start_server(host, port)
    else:
        username = input("Username: ")
        if check_username(username):
            password = input("Password: ")
            start_client(host, port, username, password)

if __name__ == "__main__":
    main()
