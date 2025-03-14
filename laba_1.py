import socket
import threading
import hashlib
import random
import string
import logging
import tkinter as tk
from tkinter import scrolledtext, messagebox
from sqlalchemy import create_engine, Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Authentication")
        self.create_login_screen()

    def create_login_screen(self):
        """Первичный экран — ввод только имени пользователя."""
        self.clear_window()
        tk.Label(self.root, text="Username:").pack(pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(pady=5)
        tk.Button(self.root, text="Next", command=self.check_username).pack(pady=5)
        tk.Button(self.root, text="Start Server", command=self.start_server).pack(pady=5)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def check_username(self):
        """Подключается к серверу, отправляет имя пользователя и получает nonce.
           Если имя найдено, появляется поле для ввода пароля."""
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Ошибка", "Введите имя пользователя!")
            return
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Привязываем клиентский сокет к порту 54321
            self.sock.bind(("127.0.0.1", 54321))
            # Подключаемся к серверу на порту 12345
            self.sock.connect(("127.0.0.1", 12345))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к серверу: {e}")
            return

        self.sock.sendall(username.encode())
        nonce = self.sock.recv(1024).decode()
        if nonce == 'FAIL':
            messagebox.showerror("Ошибка", "Пользователь не найден!")
            self.sock.close()
            return
        self.nonce = nonce
        self.show_password_entry(username)

    def show_password_entry(self, username):
        """Обновляет интерфейс: показывает имя пользователя и поле для ввода пароля."""
        self.clear_window()
        tk.Label(self.root, text=f"Username: {username}").pack(pady=5)
        tk.Label(self.root, text="Password:").pack(pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)
        tk.Button(self.root, text="Login", command=self.do_login).pack(pady=5)

    def do_login(self):
        """Отправляет серверу хэш от (nonce + MD5(пароля)) и ждет ответа."""
        password = self.password_entry.get()
        if not password:
            messagebox.showerror("Ошибка", "Введите пароль!")
            return
        hashed_password = md5(password)
        final_hash = md5(self.nonce + hashed_password)
        self.sock.sendall(final_hash.encode())
        response = self.sock.recv(1024).decode()
        if response == 'SUCCESS':
            self.create_chat_screen(self.sock, "Client")
        else:
            messagebox.showerror("Ошибка", "Аутентификация не удалась.")
            self.sock.close()

    def start_server(self):
        threading.Thread(target=self.run_server_gui, daemon=True).start()

    def run_server_gui(self):
        self.server_root = tk.Tk()
        self.server_root.title("Server Console")
        self.server_log = scrolledtext.ScrolledText(self.server_root, state='disabled')
        self.server_log.pack(padx=10, pady=10)
        self.server_msg_entry = tk.Entry(self.server_root)
        self.server_msg_entry.pack(padx=10, pady=5)
        tk.Button(self.server_root, text="Send", command=self.send_server_message).pack(pady=5)
        tk.Button(self.server_root, text="Регистрация", command=self.open_registration_window).pack(pady=5)
        threading.Thread(target=self.run_server, daemon=True).start()
        self.server_root.mainloop()

    def open_registration_window(self):
        reg_window = tk.Toplevel(self.server_root)
        reg_window.title("Регистрация нового пользователя")
        tk.Label(reg_window, text="Username:").pack(pady=5)
        username_entry = tk.Entry(reg_window)
        username_entry.pack(pady=5)
        tk.Label(reg_window, text="Password:").pack(pady=5)
        password_entry = tk.Entry(reg_window, show="*")
        password_entry.pack(pady=5)
        
        def on_register():
            username = username_entry.get()
            password = password_entry.get()
            if not username or not password:
                messagebox.showerror("Ошибка", "Пожалуйста, введите имя пользователя и пароль!")
                return
            self.register_user(username, password)
            reg_window.destroy()
        
        tk.Button(reg_window, text="Зарегистрировать", command=on_register).pack(pady=5)

    def register_user(self, username, password):
        session = get_session()
        try:
            if session.query(User).filter_by(username=username).first():
                messagebox.showerror("Ошибка", "Пользователь с таким именем уже существует!")
                return
            hashed_password = md5(password)
            new_user = User(username=username, password=hashed_password)
            session.add(new_user)
            session.commit()
            messagebox.showinfo("Успех", "Пользователь успешно зарегистрирован!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при регистрации: {str(e)}")
        finally:
            session.close()

    def send_server_message(self):
        if hasattr(self, 'server_conn'):
            msg = self.server_msg_entry.get()
            self.server_conn.sendall(msg.encode())
            self.server_log.configure(state='normal')
            self.server_log.insert(tk.END, "Server: " + msg + "\n")
            self.server_log.configure(state='disabled')
            self.server_msg_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "No client connected.")

    def run_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Сервер слушает на порту 12345
        server.bind(("127.0.0.1", 12345))
        server.listen(1)
        logging.info("Server listening on 127.0.0.1:12345")
        self.log_message("Server started on 127.0.0.1:12345")
        self.server_conn, addr = server.accept()
        self.log_message(f"Client connected: {addr}")
        self.handle_client(self.server_conn, addr)
        threading.Thread(target=self.receive_server_messages, daemon=True).start()

    def log_message(self, message):
        self.server_log.configure(state='normal')
        self.server_log.insert(tk.END, message + "\n")
        self.server_log.configure(state='disabled')

    def handle_client(self, conn, addr):
        username = conn.recv(1024).decode()
        stored_hash = get_password_hash(username)
        if not stored_hash:
            conn.sendall(b'FAIL')
            return
        nonce = gen_str()
        conn.sendall(nonce.encode())
        client_hash = conn.recv(1024).decode()
        server_hash = md5(nonce + stored_hash)
        if client_hash == server_hash:
            conn.sendall(b'SUCCESS')
            self.log_message("Authentication successful.")
        else:
            conn.sendall(b'FAIL')
            self.log_message("Authentication failed.")

    def receive_server_messages(self):
        while True:
            try:
                data = self.server_conn.recv(1024)
                if not data:
                    break
                self.server_log.configure(state='normal')
                self.server_log.insert(tk.END, f"Client: {data.decode()}\n")
                self.server_log.configure(state='disabled')
            except Exception as e:
                logging.error(f"Error receiving message: {e}")
                break

    def create_chat_screen(self, sock, role):
        self.clear_window()
        self.chat_log = scrolledtext.ScrolledText(self.root, state='disabled')
        self.chat_log.pack(padx=10, pady=10)
        self.msg_entry = tk.Entry(self.root)
        self.msg_entry.pack(padx=10, pady=5)
        tk.Button(self.root, text="Send", command=lambda: self.send_message(sock)).pack(pady=5)
        threading.Thread(target=self.receive_messages, args=(sock, role), daemon=True).start()

    def send_message(self, sock):
        msg = self.msg_entry.get()
        sock.sendall(msg.encode())
        self.chat_log.configure(state='normal')
        self.chat_log.insert(tk.END, "You: " + msg + "\n")
        self.chat_log.configure(state='disabled')
        self.msg_entry.delete(0, tk.END)

    def receive_messages(self, sock, name):
        while True:
            try:
                data = sock.recv(1024)
                if not data:
                    break
                self.chat_log.configure(state='normal')
                self.chat_log.insert(tk.END, f"{name}: {data.decode()}\n")
                self.chat_log.configure(state='disabled')
            except:
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
