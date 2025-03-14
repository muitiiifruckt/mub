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
        self.clear_window()
        tk.Label(self.root, text="Username:").pack()
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack()
        tk.Label(self.root, text="Password:").pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()
        tk.Button(self.root, text="Login", command=self.start_client).pack()
        tk.Button(self.root, text="Start Server", command=self.start_server).pack()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def start_server(self):
        threading.Thread(target=self.run_server_gui, daemon=True).start()

    def run_server_gui(self):
        self.server_root = tk.Tk()
        self.server_root.title("Server Console")
        self.server_log = scrolledtext.ScrolledText(self.server_root, state='disabled')
        self.server_log.pack()
        self.server_msg_entry = tk.Entry(self.server_root)
        self.server_msg_entry.pack()
        tk.Button(self.server_root, text="Send", command=self.send_server_message).pack()
        threading.Thread(target=self.run_server, daemon=True).start()
        self.server_root.mainloop()

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
        server.bind(("127.0.0.1", 5000))
        server.listen(1)
        logging.info("Server listening on 127.0.0.1:5000")
        self.log_message("Server started on 127.0.0.1:5000")
        self.server_conn, addr = server.accept()
        self.log_message(f"Client connected: {addr}")
        self.handle_client(self.server_conn, addr)

        # Запускаем поток для приема сообщений от клиента
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

    def start_client(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 5000))
        sock.sendall(username.encode())
        nonce = sock.recv(1024).decode()
        if nonce == 'FAIL':
            messagebox.showerror("Error", "Authentication failed: User not found.")
            return
        hashed_password = md5(password)
        final_hash = md5(nonce + hashed_password)
        sock.sendall(final_hash.encode())
        response = sock.recv(1024).decode()
        if response == 'SUCCESS':
            self.create_chat_screen(sock, "Client")
        else:
            messagebox.showerror("Error", "Authentication failed.")

    def create_chat_screen(self, sock, role):
        self.clear_window()
        self.chat_log = scrolledtext.ScrolledText(self.root, state='disabled')
        self.chat_log.pack()
        self.msg_entry = tk.Entry(self.root)
        self.msg_entry.pack()
        tk.Button(self.root, text="Send", command=lambda: self.send_message(sock)).pack()
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