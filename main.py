
import tkinter as tk
import getpass
import socket

def parse_input(input_string):
    parts = input_string.split()
    return (parts[0] if parts else "",
            parts[1:] if len(parts) > 1 else "")

# Реализация команд
def cmd_ls(args):
    return f"Команда 'ls' вызвана с аргументами: {args}"

def cmd_cd(args):
    return f"Команда 'cd' вызвана с аргументами: {args}"

def cmd_help():
    return f"help\ncd\nls"

def cmd_exit():
    print_to_console("Завершение работы...")
    root.after(1000, root.destroy)

# Создание GUI
root = tk.Tk()
username = getpass.getuser()
hostname = socket.gethostname()
root.title(f"Эмулятор - [{username}@{hostname}]")
root.geometry("700x400")

console_output = tk.Text(root, height=20, width=80)
console_output.pack(pady=10)

input_entry = tk.Entry(root, width=80)
input_entry.pack(pady=5)
input_entry.focus()

def print_to_console(text):
    console_output.insert(tk.END, text + "\n")
    console_output.see(tk.END)

def process_input(event=None):
    user_input = input_entry.get()
    if user_input.strip():
        print_to_console(f"$ {user_input}")

        command, args = parse_input(user_input)

        # Обработка команд
        if command == "ls":
            result = cmd_ls(args)
        elif command == "cd":
            result = cmd_cd(args)
        elif command == "help":
            result = cmd_help()
        elif command == "exit":
            cmd_exit()
            input_entry.delete(0, tk.END)
            return
        else:
            result = f"Неизвестная команда: {command}"

        print_to_console(result)
        print_to_console("")
    input_entry.delete(0, tk.END)
input_entry.bind('<Return>', process_input)

print_to_console(f"Введите команду и нажмите Enter...")
print_to_console("")

root.mainloop()
