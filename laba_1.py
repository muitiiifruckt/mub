import socket
import threading
import hashlib
from tkinter import Tk, Entry, Button, Text, END, messagebox, Label
from tkinter import Tk, Toplevel, Label, Button
# Настройки клиента
HOST = '127.0.0.1'  # IP для прослушивания
PORT = 12345        # Порт для прослушивания
PEER_HOST = '127.0.0.1'  # IP другого клиента
PEER_PORT = 54321        # Порт другого клиента
SIZE = "500x400"
# Файл для хранения пользователей
USERS_FILE = "users.txt"

# Функция для хэширования пароля
def hash_password(password):
    return hashlib.md5(password.encode('utf-8')).hexdigest()

# Функция для регистрации нового пользователя
def register(username, password):
    with open(USERS_FILE, "a") as file:
        file.write(f"{username}:{hash_password(password)}\n")
    messagebox.showinfo("Успех", "Регистрация прошла успешно!")

# Функция для аутентификации пользователя
def authenticate(username, password):
    with open(USERS_FILE, "r") as file:
        for line in file:
            stored_username, stored_hash = line.strip().split(":")
            if stored_username == username and stored_hash == hash_password(password):
                return True
    return False

# Функция для прослушивания входящих сообщений
def listen_for_messages():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Слушаем на {HOST}:{PORT}")
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Подключен клиент: {client_address}")
            while True:
                try:
                    message = client_socket.recv(1024).decode('utf-8')
                    if not message:
                        break
                    chat_box.insert(END, f"Другой клиент: {message}\n")
                except Exception as e:
                    print(f"Ошибка: {e}")
                    break
            client_socket.close()

# Функция для отправки сообщений
def send_message():
    message = entry.get()
    if message:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((PEER_HOST, PEER_PORT))
                client_socket.send(message.encode('utf-8'))
            entry.delete(0, END)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отправить сообщение: {e}")

# Функция для отображения окна регистрации
def show_register_window():
    register_window = Tk()
    register_window.title("Регистрация")
    register_window.geometry(SIZE)

    Label(register_window, text="Логин:").pack()
    register_username_entry = Entry(register_window)
    register_username_entry.pack()

    Label(register_window, text="Пароль:").pack()
    register_password_entry = Entry(register_window, show="*")
    register_password_entry.pack()

    def perform_register():
        username = register_username_entry.get()
        password = register_password_entry.get()
        if username and password:
            register(username, password)
            register_window.destroy()
        else:
            messagebox.showerror("Ошибка", "Логин и пароль не могут быть пустыми!")

    Button(register_window, text="Зарегистрироваться", command=perform_register).pack()
    register_window.mainloop()

# Функция для отображения окна аутентификации
def show_auth_window():
    auth_window = Tk()
    auth_window.title("Аутентификация")
    auth_window.geometry(SIZE)

    Label(auth_window, text="Логин:").pack()
    auth_username_entry = Entry(auth_window)
    auth_username_entry.pack()

    Label(auth_window, text="Пароль:").pack()
    auth_password_entry = Entry(auth_window, show="*")
    auth_password_entry.pack()

    def perform_auth():
        username = auth_username_entry.get()
        password = auth_password_entry.get()
        if username and password:
            if authenticate(username, password):
                auth_window.destroy()
                root.deiconify()  # Показываем основное окно чата
            else:
                messagebox.showerror("Ошибка", "Неверный логин или пароль!")
        else:
            messagebox.showerror("Ошибка", "Логин и пароль не могут быть пустыми!")

    Button(auth_window, text="Войти", command=perform_auth).pack()
    auth_window.mainloop()
root = Tk()
root.title("P2P Мессенджер")
root.withdraw()  # Скрываем основное окно до аутентификации

# Поле для ввода сообщения
entry = Entry(root, width=50)
entry.pack(pady=10)

# Кнопка отправки
send_button = Button(root, text="Отправить", command=send_message)
send_button.pack()

# Окно чата
chat_box = Text(root, width=60, height=20)
chat_box.pack(pady=10)

# Запуск потока для прослушивания сообщений
threading.Thread(target=listen_for_messages, daemon=True).start()

# Отображение окна регистрации или аутентификации
def startup():
    choice = choice = messagebox.askquestion("Выбор", "У вас есть аккаунт?")
    if choice == "yes":
        show_auth_window()
    else:
        show_register_window()
        show_auth_window()

# Запуск начального окна
startup()

# Запуск GUI
root.mainloop()
