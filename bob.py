import socket
import threading
from tkinter import Tk, Entry, Button, Text, END, messagebox

# Настройки клиента
HOST = '127.0.0.1'  # IP для прослушивания
PORT = 54321        # Порт для прослушивания
PEER_HOST = '127.0.0.1'  # IP другого клиента
PEER_PORT = 12345      # Порт другого клиента

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

# Создание GUI
root = Tk()
root.title("P2P Мессенджер")

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

# Запуск GUI
root.mainloop()