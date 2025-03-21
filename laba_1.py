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
from sympy import randprime, primitive_root
from models import get_session, User, get_password_hash
from decod import gen_str, md5, gen_a_g_p,generate_prime,sha256
import arc4
from rsa_gen import generate_rsa_keys
# Настройка логирования



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')





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
            self.sock.bind(("127.0.0.2", 54321))
            # Подключаемся к серверу на порту 12345
            self.sock.connect(("127.0.0.2", 12345))
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
        tk.Button(self.server_root, text="Диффи-хелман", command=self.diffi_helman).pack(pady=5)
        tk.Button(self.server_root, text="ЭЦП", command=self.podpis_server).pack(pady=5)
        threading.Thread(target=self.run_server, daemon=True).start()
        self.server_root.mainloop()
    def podpis_server(self,file_name = "file.txt"):
        with open(file_name, "rb") as f:  # Открываем в бинарном режиме
            file_data = f.read()
        hash = sha256(file_data)
        print("hash file----------------", hash)
        bits = 512
        public_key, private_key = generate_rsa_keys(bits)
        d, N = private_key
        e, N = public_key
        print(f"e,N = {e},{N}")
        print(f"d,N = {d},{N}")
        podpis =  pow(hash, d, N)
        print("proverka---------------", pow(podpis,e,N))
        msg = f"podpis:{podpis}:{e}:{N}"
        
        self.send_server_message(msg)
    def diffi_helman(self):
        try:
            # Генерация параметров
            a, g, p = gen_a_g_p()    
            self.a = a 
            self.p = p 
            message = f"DIFFI_HELMAN:{a}:{g}:{p}"
            self.send_server_message(message)
        except:
            pass
    
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

    def send_server_message(self,msg = None):
        if hasattr(self, 'server_conn'):
            if not msg:
                msg = self.server_msg_entry.get()
            cipher = None
            try:
                cipher = self.cipher2
            except:
                pass
            data = msg
            if cipher:
                try:
                    data = cipher.encrypt(data.encode())
                    self.server_conn.sendall(data)
                    
                    self.server_log.configure(state='normal')
                    self.server_log.insert(tk.END, "Server enc: " + msg + "\n")
                    self.server_log.configure(state='disabled')
                    self.server_msg_entry.delete(0, tk.END)
                    print("Сервер отправил зашифровав", data)
                except:
                    print("Сервер не отправил зашифровав")
            else:
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
        server.bind(("127.0.0.2", 12345))
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
                print(data,"принято")
                cipher = None
                try:
                    cipher = self.cipher
                except:
                    pass
                if cipher:
                    try:
                        print("DECRYPT")
                        data = cipher.decrypt(data).decode()
                        print(data, "Расшифрано")
                        self.server_log.configure(state='normal')
                        self.server_log.insert(tk.END, f"Client Расшифровано : {data}\n")
                        
                        self.server_log.configure(state='disabled')
                        print("вставлено в чат")
                    except:
                        print("сервер не расшифрвоал")
                else:
                    if data.decode().startswith("DIFFI_HELMAN_RESPONSE"):
                            self.diffi_server(data.decode())
                    self.server_log.configure(state='normal')
                    self.server_log.insert(tk.END, f"Client: {data.decode()}\n")
                    
                    self.server_log.configure(state='disabled')
            except Exception as e:
                logging.error(f"Error receiving message: {e}")
                
    def diffi_server(self,data):   
        _, B = data.split(":")
        B = int(B)
        k = pow(B,self.a,self.p)
        self.secret = k
        print(self.secret, "SERVER")
        key_bytes = k.to_bytes((k.bit_length() + 7) // 8, byteorder='big')  # Преобразуем в байты
        self.cipher = arc4.ARC4(key_bytes)  # Передаем в ARC4
        self.cipher2 = arc4.ARC4(key_bytes)  # Передаем в ARC4
    def create_chat_screen(self, sock, role):
        self.clear_window()
        self.chat_log = scrolledtext.ScrolledText(self.root, state='disabled')
        self.chat_log.pack(padx=10, pady=10)
        self.msg_entry = tk.Entry(self.root)
        self.msg_entry.pack(padx=10, pady=5)
        tk.Button(self.root, text="Send", command=lambda: self.send_message(sock)).pack(pady=5)
        threading.Thread(target=self.receive_messages, args=(sock, role), daemon=True).start()

    def send_message(self, sock, msg = None):
        if not msg:
            msg = self.msg_entry.get()
        cipher = None
        try:
            cipher = self.cipher2
        except:
            pass
        data = msg
        if cipher:
            try:
                
                print(data , "data до шфирвоани")
                data = cipher.encrypt(data.encode())
                print(data , "data после шифрвония")
  
                sock.sendall(data)
                print("Зашифрованное сообщение отправлено", data)
                self.chat_log.configure(state='normal')
                self.chat_log.insert(tk.END, "You enc: " + msg + "\n")
                self.chat_log.configure(state='disabled')
                self.msg_entry.delete(0, tk.END)
                
            except:
                print("Зашифрованное не сообщение отправлено клиентом")
        else:
            sock.sendall(msg.encode())
            self.chat_log.configure(state='normal')
            self.chat_log.insert(tk.END, "You: " + msg + "\n")
            self.chat_log.configure(state='disabled')
            self.msg_entry.delete(0, tk.END)

    def receive_messages(self, sock, name):
        while True:
            try:
                data = sock.recv(1024)
                if data:
                    print("Принято клиентом",data)
                    cipher = None
                    try:
                        cipher = self.cipher
                    except:
                        pass
                    
                    if cipher:
                        try:
                            print("DECRYPT")
                            data = cipher.decrypt(data).decode()
                            print(data, "Расшифрано")
                            self.chat_log.configure(state='normal')
                            self.chat_log.insert(tk.END, f"Расшифровано {name}: {data}\n")
                            self.chat_log.configure(state='disabled')
                            if "podpis" in data:
                                file_name = "file.txt"
                                print(1)
                                _,podpis,e,N = data.split(":")
                                with open(file_name, "rb") as f:  # Открываем в бинарном режиме
                                    file_data = f.read()
                                hash_value = sha256(file_data)  # Вычисляем хэш файла
                                print("hash file", hash_value)
                                # Преобразуем строковые данные в числа
                                podpis = int(podpis)
                                e = int(e)
                                N = int(N)
                                print(2)
                                # Расшифровываем подпись (получаем оригинальный хэш)
                                decrypted_hash = pow(podpis, e, N)
                                print(3)
                                # Сравниваем с вычисленным хэшем
                                if decrypted_hash == hash_value:
                                    print("✅ Подпись верна!")
                                else:
                                    print("❌ Подпись неверна!")
                        except:
                            print("Клиент не расшифрвоал")
                    else:
                        self.chat_log.configure(state='normal')
                        self.chat_log.insert(tk.END, f"{name}: {data.decode()}\n")
                        self.chat_log.configure(state='disabled')
                        if data.decode().startswith("DIFFI_HELMAN"):
                            self.diffi_client(data.decode())
            except:
                logging.warning("ошибка при принятии сообщения клинетом")
    def diffi_client(self,data):
        
        # Обработка сообщения DIFFI_HELMAN
        _, a, g, p = data.split(":")
        a = int(a)
        g = int(g)
        p = int(p)
        # Вычисляем B = g^b mod p (где b — случайное число на сервере)
        b = random.randint(1, p-1)
        B = pow(g, b, p)
        # Вычисляем общий секретный ключ
        A = pow(g, a, p)
        secret_key = pow(A, b, p)
        self.secret = secret_key

        # Отправляем B клиенту
        self.send_message(self.sock, f"DIFFI_HELMAN_RESPONSE:{B}")
        self.cipher = arc4.ARC4(secret_key)
        self.cipher2 = arc4.ARC4(secret_key)  # Передаем в ARC4


      
if __name__ == "__main__":

    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
    