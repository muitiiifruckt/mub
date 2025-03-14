import socket
import threading
import multiprocessing
import hashlib
import random
import string
from tkinter import Tk, Entry, Button, Text, END, messagebox, simpledialog
from models import add_user, check_user, check_username

HOST = '127.0.0.1'
AUTH_PORT = 8888
port_1, port_2 = 12345, 54321
class User:
    def __init__(self, port_listen, port_send, name):
        self.name = name
        self.port_listen = port_listen
        self.port_send = port_send
        self.root = Tk()
        self.root.title(f"P2P Messenger - {self.name}")

        self.entry = Entry(self.root, width=50)
        self.entry.pack(pady=10)

        send_button = Button(self.root, text="Send", command=self.send_message)
        send_button.pack()

        self.chat_box = Text(self.root, width=60, height=20)
        self.chat_box.pack(pady=10)
    
    
    def listen_for_messages(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((HOST, self.port_listen))
            server_socket.listen()
            while True:
                client_socket, _ = server_socket.accept()
                try:
                    message = client_socket.recv(1024).decode('utf-8')
                    if message:
                        self.chat_box.insert(END, f"Сообщение: {message}\n")
                except Exception as e:
                    pass
                finally:
                    client_socket.close()

    def send_message(self):
        message = self.entry.get()
        if message:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                    client_socket.connect((HOST, self.port_send))
                    client_socket.send(message.encode('utf-8'))
                    self.chat_box.insert(END, f"{self.name}: {message}\n")
                self.entry.delete(0, END)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send message: {e}")
    def run(self):
        threading.Thread(target=self.listen_for_messages, daemon=True).start()
        self.root.mainloop()


def send_auth(message):
    if message:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((HOST, port_1))
                client_socket.send(message.encode('utf-8'))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {e}")
            
def login_window():
    root = Tk()
    root.title("Authentication")
    root.geometry("300x150")
    user_credentials = (None, None)

    def on_register():
        username = simpledialog.askstring("Register", "Enter username:")
        password = simpledialog.askstring("Register", "Enter password:", show="*")
        if username and password:
            if add_user(username, password):
                messagebox.showinfo("Registration", "Registration successful! Log in now.")
            else:
                messagebox.showerror("Error", "User already exists.")
        else:
            messagebox.showerror("Error", "Username and password cannot be empty.")

    def on_login():
        nonlocal user_credentials
        username = simpledialog.askstring("Login", "Enter username:")
        is_real_name = send_auth("AUTH USERNAME: " + username)
        if is_real_name:
            pass
        if check_username(username):
            password = simpledialog.askstring("Login", "Enter password:", show="*")
            if password and check_user(username, password):
                messagebox.showinfo("Login", "Login successful!")
                user_credentials = (username, password)
                root.quit()
            else:
                messagebox.showerror("Error", "Invalid username or password.")
        else:
            messagebox.showerror("Error", "User does not exist.")

    Button(root, text="Login", command=on_login).pack(pady=10)
    Button(root, text="Register", command=on_register).pack(pady=10)
    root.mainloop()
    root.destroy()
    return user_credentials

def start_user(port_listen, port_send, name):
    username, password = login_window()
    user = User(port_listen, port_send, username)
    user.run()
def start_admin(port_listen, port_send, name):
    user = User(port_listen, port_send, name)
    user.run()
def gen_str(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

if __name__ == "__main__":

    p1 = multiprocessing.Process(target=start_admin, args=(port_1, port_2, "Alice"))
    p2 = multiprocessing.Process(target=start_user, args=(port_2, port_1, "Bob"))
 
    p1.start()
    p2.start()
    p1.join()
    p2.join()
 