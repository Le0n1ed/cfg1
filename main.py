import tkinter as tk
import getpass
import socket
import os
import sys
import xml.etree.ElementTree as ET
import argparse
from pathlib import Path


class ShellEmulator:
    def __init__(self, vfs_path=None, startup_script=None, config_file=None):
        self.vfs_path = vfs_path or Path.home() / "vfs"
        self.startup_script = startup_script
        self.config_file = config_file
        self.current_dir = Path("/")

        # Создаем VFS директорию если не существует
        self.vfs_path.mkdir(exist_ok=True)

        # Загружаем конфигурацию
        self.load_config()

        # Отладочный вывод
        self.debug_print_config()

    def load_config(self):
        """Загрузка конфигурации из файла"""
        if self.config_file and Path(self.config_file).exists():
            try:
                tree = ET.parse(self.config_file)
                root = tree.getroot()

                vfs_elem = root.find('vfs_path')
                if vfs_elem is not None:
                    self.vfs_path = Path(vfs_elem.text)

                script_elem = root.find('startup_script')
                if script_elem is not None:
                    self.startup_script = script_elem.text

            except ET.ParseError as e:
                print(f"Ошибка парсинга конфигурационного файла: {e}")

    def debug_print_config(self):
        """Отладочный вывод конфигурации"""
        print("=== Конфигурация эмулятора ===")
        print(f"VFS путь: {self.vfs_path}")
        print(f"Стартовый скрипт: {self.startup_script}")
        print(f"Конфигурационный файл: {self.config_file}")
        print("===============================")

    def parse_input(self, input_string):
        """Парсер с поддержкой кавычек"""
        parts = []
        current_part = []
        in_quotes = False
        quote_char = None

        for char in input_string:
            if char in ['"', "'"]:
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                else:
                    current_part.append(char)
            elif char == ' ' and not in_quotes:
                if current_part:
                    parts.append(''.join(current_part))
                    current_part = []
            else:
                current_part.append(char)

        if current_part:
            parts.append(''.join(current_part))

        return (parts[0] if parts else "", parts[1:] if len(parts) > 1 else [])

    def get_prompt(self):
        """Формирование приглашения к вводу"""
        username = getpass.getuser()
        hostname = socket.gethostname()
        current_dir = str(self.current_dir)
        return f"{username}@{hostname}:{current_dir}$ "

    def resolve_vfs_path(self, path):
        """Преобразование виртуального пути в физический"""
        if path.startswith('/'):
            return self.vfs_path / path[1:]
        else:
            return self.vfs_path / self.current_dir.relative_to('/') / path

    # Реализация команд
    def cmd_ls(self, args):
        """Команда ls с поддержкой VFS"""
        try:
            target_path = self.current_dir
            if args:
                target_path = Path(args[0]) if args[0].startswith('/') else self.current_dir / args[0]

            physical_path = self.resolve_vfs_path(str(target_path))

            if not physical_path.exists():
                return f"ls: невозможно получить доступ к '{args[0]}': Нет такого файла или каталога"

            items = []
            for item in physical_path.iterdir():
                if item.is_dir():
                    items.append(f"{item.name}/")
                else:
                    items.append(item.name)

            return '\n'.join(sorted(items)) if items else ""

        except Exception as e:
            return f"ls: ошибка: {e}"

    def cmd_cd(self, args):
        """Команда cd с поддержкой VFS"""
        if not args:
            # cd без аргументов - переход в домашнюю директорию
            self.current_dir = Path("/")
            return ""

        try:
            new_path = Path(args[0])
            if new_path.is_absolute():
                target_path = new_path
            else:
                target_path = self.current_dir / new_path

            # Нормализуем путь
            target_path = target_path.resolve()

            physical_path = self.resolve_vfs_path(str(target_path))

            if not physical_path.exists():
                return f"cd: {args[0]}: Нет такого файла или каталога"
            if not physical_path.is_dir():
                return f"cd: {args[0]}: Не каталог"

            self.current_dir = target_path
            return ""

        except Exception as e:
            return f"cd: ошибка: {e}"

    def cmd_pwd(self, args):
        """Команда pwd"""
        return str(self.current_dir)

    def cmd_help(self, args):
        """Команда help"""
        help_text = """Доступные команды:
ls [директория] - список файлов и директорий
cd [директория]  - смена директории
pwd              - текущая директория
help             - эта справка
exit             - выход из эмулятора"""
        return help_text

    def cmd_exit(self, args):
        """Команда exit"""
        return "exit"

    def execute_script(self, script_path):
        """Выполнение стартового скрипта"""
        if not script_path or not Path(script_path).exists():
            return []

        commands = []
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Пропускаем пустые строки и комментарии
                    if line and not line.startswith('#'):
                        commands.append(line)
        except Exception as e:
            print(f"Ошибка чтения скрипта: {e}")

        return commands

    def execute_command(self, command_line):
        """Выполнение одной команды"""
        command, args = self.parse_input(command_line)

        if not command:
            return ""

        command_methods = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "pwd": self.cmd_pwd,
            "help": self.cmd_help,
            "exit": self.cmd_exit
        }

        if command in command_methods:
            result = command_methods[command](args)
            if result == "exit":
                return "exit"
            return result
        else:
            return f"{command}: команда не найдена"


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Эмулятор командной оболочки')
    parser.add_argument('--vfs-path', help='Путь к физическому расположению VFS')
    parser.add_argument('--startup-script', help='Путь к стартовому скрипту')
    parser.add_argument('--config-file', help='Путь к конфигурационному файлу')

    return parser.parse_args()


class ShellGUI:
    def __init__(self, shell):
        self.shell = shell
        self.root = tk.Tk()
        self.setup_gui()

    def setup_gui(self):
        """Настройка графического интерфейса"""
        username = getpass.getuser()
        hostname = socket.gethostname()
        self.root.title(f"Эмулятор оболочки - [{username}@{hostname}]")
        self.root.geometry("700x400")

        # Текстовое поле для вывода
        self.console_output = tk.Text(self.root, height=20, width=80, bg='black', fg='white',
                                      font=('Courier New', 10))
        self.console_output.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Фрейм для ввода команды
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        # Приглашение к вводу
        self.prompt_label = tk.Label(input_frame, text=self.shell.get_prompt(),
                                     bg='black', fg='green', font=('Courier New', 10))
        self.prompt_label.pack(side=tk.LEFT)

        # Поле ввода
        self.input_entry = tk.Entry(input_frame, width=60, bg='black', fg='white',
                                    font=('Courier New', 10), insertbackground='white')
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.focus()

        # Привязка событий
        self.input_entry.bind('<Return>', self.process_input)
        self.input_entry.bind('<Key>', self.update_prompt)

        # Вывод начального сообщения
        self.print_to_console("Эмулятор командной оболочки ОС")
        self.print_to_console("Введите 'help' для списка команд")
        self.print_to_console("")

        # Выполнение стартового скрипта
        if self.shell.startup_script:
            self.execute_startup_script()

    def update_prompt(self, event=None):
        """Обновление приглашения к вводу"""
        self.prompt_label.config(text=self.shell.get_prompt())

    def print_to_console(self, text):
        """Вывод текста в консоль"""
        self.console_output.insert(tk.END, text + "\n")
        self.console_output.see(tk.END)

    def execute_startup_script(self):
        """Выполнение стартового скрипта"""
        commands = self.shell.execute_script(self.shell.startup_script)
        for command in commands:
            self.print_to_console(f"{self.shell.get_prompt()}{command}")
            result = self.shell.execute_command(command)
            if result:
                self.print_to_console(result)
            if result == "exit":
                self.root.after(1000, self.root.destroy)
                return
            self.print_to_console("")
            self.update_prompt()

    def process_input(self, event=None):
        """Обработка ввода пользователя"""
        user_input = self.input_entry.get().strip()
        if user_input:
            self.print_to_console(f"{self.shell.get_prompt()}{user_input}")

            result = self.shell.execute_command(user_input)

            if result:
                self.print_to_console(result)

            if result == "exit":
                self.root.after(1000, self.root.destroy)
                return

            self.print_to_console("")

        self.input_entry.delete(0, tk.END)
        self.update_prompt()

    def run(self):
        """Запуск приложения"""
        self.root.mainloop()


def create_sample_config():
    """Создание примеров конфигурационных файлов и скриптов"""

    # Создаем пример конфигурационного файла
    config_content = """<?xml version="1.0" encoding="UTF-8"?>
<config>
    <vfs_path>/home/{}/vfs</vfs_path>
    <startup_script>/home/{}/startup.sh</startup_script>
</config>""".format(getpass.getuser(), getpass.getuser())

    with open('config.xml', 'w') as f:
        f.write(config_content)

    # Создаем пример стартового скрипта
    script_content = """#!/bin/bash
# Стартовый скрипт для эмулятора
echo "Запуск эмулятора..."

pwd
ls
cd /home
pwd
ls
help
"""

    with open('startup.sh', 'w') as f:
        f.write(script_content)

    # Создаем тестовые скрипты для реальной ОС
    test_script1 = """#!/bin/bash
# Тест 1: Запуск с параметрами командной строки
python shell_emulator.py --vfs-path ./test_vfs --startup-script ./test_script.sh
"""

    test_script2 = """#!/bin/bash
# Тест 2: Запуск с конфигурационным файлом
python shell_emulator.py --config-file config.xml
"""

    test_script3 = """#!/bin/bash
# Тест 3: Запуск со всеми параметрами
python shell_emulator.py --vfs-path ./custom_vfs --startup-script ./custom_script.sh --config-file config.xml
"""

    with open('test_with_args.sh', 'w') as f:
        f.write(test_script1)

    with open('test_with_config.sh', 'w') as f:
        f.write(test_script2)

    with open('test_all_params.sh', 'w') as f:
        f.write(test_script3)

    print("Созданы примеры конфигурационных файлов и скриптов:")
    print("- config.xml (конфигурационный файл)")
    print("- startup.sh (стартовый скрипт)")
    print("- test_with_args.sh (тест с параметрами командной строки)")
    print("- test_with_config.sh (тест с конфигурационным файлом)")
    print("- test_all_params.sh (тест со всеми параметрами)")


def main():
    """Основная функция"""
    args = parse_arguments()

    # Создаем экземпляр эмулятора
    shell = ShellEmulator(
        vfs_path=args.vfs_path,
        startup_script=args.startup_script,
        config_file=args.config_file
    )

    # Запускаем GUI
    gui = ShellGUI(shell)
    gui.run()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--create-samples":
        create_sample_config()
    else:
        main()