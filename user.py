import socket
import threading
import multiprocessing
import hashlib
from tkinter import Tk, Entry, Button, Text, Label, END, messagebox, simpledialog
from models import add_user, check_user,check_username
import random
import string
HOST = '127.0.0.1'  # IP для прослушивания

class User:
    def __init__(self, port_listen, port_send, name):
        self.name = name
        self.port_listen = port_listen
        self.port_send = port_send
        self.root = Tk()
        self.root.title(f"P2P Мессенджер для {self.name}")

        # Поле для ввода сообщения
        self.entry = Entry(self.root, width=50)
        self.entry.pack(pady=10)

        # Кнопка отправки
        send_button = Button(self.root, text="Отправить", command=self.send_message)
        send_button.pack()

        # Окно чата
        self.chat_box = Text(self.root, width=60, height=20)
        self.chat_box.pack(pady=10)

    def listen_for_messages(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((HOST, self.port_listen))
            server_socket.listen()
            print(f"[{self.name}] Слушаем на {HOST}:{self.port_listen}")
            while True:
                client_socket, client_address = server_socket.accept()
                
                while True:
                    try:
                        message = client_socket.recv(1024).decode('utf-8')
                        
                        if not message:
                            break
                        print(f"Сообщение пришло к {self.name}: {message}")
                        self.chat_box.insert(END, f"Другой клиент: {message}\n")
                    except Exception as e:
                        print(f"[{self.name}] Ошибка: {e}")
                        break
                client_socket.close()

    def send_message(self):
        message = self.entry.get()
        if message:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                    client_socket.connect((HOST, self.port_send))
                    client_socket.send(message.encode('utf-8'))
                    self.chat_box.insert(END, f"{self.name}: {message}\n")
                    print(f"Сообщение отправлено от {self.name}: {message}")
                self.entry.delete(0, END)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось отправить сообщение: {e}")

    def run(self):
        threading.Thread(target=self.listen_for_messages, daemon=True).start()
        self.root.mainloop()
def login_window():
    def on_register():
        username = simpledialog.askstring("Регистрация", "Введите имя пользователя:")
        password = simpledialog.askstring("Регистрация", "Введите пароль:", show="*")
        
        if username and password:
            if add_user(username, password):
                messagebox.showinfo("Регистрация", "Успешная регистрация! Теперь войдите в систему.")
            else:
                messagebox.showerror("Ошибка", "Пользователь уже существует.")
        else:
            messagebox.showerror("Ошибка", "Имя пользователя и пароль не могут быть пустыми.")

    def on_login():
        nonlocal user_credentials  # Используем переменную вне функции
        username = simpledialog.askstring("Вход", "Введите имя пользователя:")
        if check_username(username):
            password = simpledialog.askstring("Вход", "Введите пароль:", show="*")
            
            if password:
                if check_user(username, password):
                    messagebox.showinfo("Вход", "Успешный вход!")
                    user_credentials = (username, password)  # Сохраняем логин и пароль
                    root.quit()  # Останавливаем mainloop()
                else:
                    messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль.")
            else:
                messagebox.showerror("Ошибка", "Пароль не может быть пустым.")
        else:
            messagebox.showerror("Ошибка", "Такого пользователя не существует")

    root = Tk()
    root.title("Авторизация")
    root.geometry("300x150")

    user_credentials = (None, None)  # Переменная для хранения результата

    btn_login = Button(root, text="Вход", command=on_login)
    btn_login.pack(pady=10)

    btn_register = Button(root, text="Регистрация", command=on_register)
    btn_register.pack(pady=10)

    root.mainloop()  # Запуск основного цикла Tkinter

    root.destroy()  # Закрываем окно после выхода из mainloop()
    return user_credentials  # Возвращаем логин и пароль
def start_user(port_listen, port_send, name):
    username, password = login_window()
    print("dsfsdfs")
    user = User(port_listen, port_send, username)
    user.run()
    
def gen_str(length=32):
    characters = string.ascii_letters + string.digits  # Буквы (верхний и нижний регистр) + цифры
    return ''.join(random.choices(characters, k=length))
def md5(str):
    return hashlib.md5(str.encode('utf-8')).hexdigest()
if __name__ == "__main__":
    port_1 = 12345
    port_2 = 54321

    # Создаем два процесса
    p1 = multiprocessing.Process(target=start_user, args=(port_1, port_2, "Alice"))
    p2 = multiprocessing.Process(target=start_user, args=(port_2, port_1, "Bob"))

    p1.start()
    p2.start()

    p1.join()
    p2.join()
