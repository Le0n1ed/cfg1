import tkinter as tk
import getpass
import socket
import shlex


def parse_input(input_string):
    try:
        parts = shlex.split(input_string)
        return (parts[0] if parts else "", parts[1:] if len(parts) > 1 else [])
    except ValueError as e:
        return ("", [f"Ошибка парсинга: {str(e)}"])


# Реализация команд-заглушек
def cmd_ls(args):
    return f"ls: {args}"


def cmd_cd(args):
    return f"cd: {args}"


def cmd_help():
    return "Доступные команды: ls, cd, help, exit"


def cmd_exit():
    print_to_console("Завершение работы...")
    root.after(1000, root.destroy)


# Создание GUI
root = tk.Tk()
username = getpass.getuser()
hostname = socket.gethostname()
prompt = f"{username}@{hostname}:~$"
root.title(f"Эмулятор терминала - {prompt}")
root.geometry("700x400")

console_output = tk.Text(root, height=20, width=80, bg="black", fg="white", font=("Courier", 10))
console_output.pack(pady=10, padx=10)

input_frame = tk.Frame(root)
input_frame.pack(pady=5, padx=10, fill=tk.X)

prompt_label = tk.Label(input_frame, text=prompt, bg="black", fg="green", font=("Courier", 10))
prompt_label.pack(side=tk.LEFT)

input_entry = tk.Entry(input_frame, width=60, bg="black", fg="white", font=("Courier", 10), insertbackground="white")
input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
input_entry.focus()


def print_to_console(text):
    console_output.insert(tk.END, text + "\n")
    console_output.see(tk.END)


def process_input(event=None):
    user_input = input_entry.get().strip()
    if not user_input:
        print_to_console(prompt)
        input_entry.delete(0, tk.END)
        return

    print_to_console(prompt + " " + user_input)

    command, args = parse_input(user_input)

    # Обработка ошибок парсинга
    if args and isinstance(args[0], str) and args[0].startswith("Ошибка парсинга"):
        print_to_console(args[0])
    # Обработка команд
    elif command == "ls":
        result = cmd_ls(args)
    elif command == "cd":
        result = cmd_cd(args)
    elif command == "help":
        result = cmd_help()
    elif command == "exit":
        cmd_exit()
        return
    elif command == "":
        result = ""
    else:
        result = f"Неизвестная команда: {command}"

    if result:
        print_to_console(result)

    print_to_console("")
    input_entry.delete(0, tk.END)


input_entry.bind('<Return>', process_input)

# Начальное сообщение
print_to_console("Эмулятор терминала")
print_to_console("Введите 'help' для списка команд")
print_to_console("")

root.mainloop()