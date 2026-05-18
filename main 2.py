import os
import sys
import subprocess

# Автоматическая проверка и установка библиотек перед запуском
required_libraries = ["requests", "customtkinter"]
for lib in required_libraries:
    try:
        __import__(lib)
    except ImportError:
        print(f"Установка библиотеки {lib}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

# Основные импорты программы
import json
import datetime
import requests
import customtkinter as ctk
from tkinter import ttk, messagebox

# Настройки оформления
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class CurrencyConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Конфигурация файлов истории
        self.HISTORY_FILE = "history.json"
        
        # Список популярных валют
        self.currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY", "KZT", "BYN"]

        # РЕЗЕРВНАЯ БАЗА КУРСОВ (если интернет полностью отключен или заблокирован)
        # Курсы указаны относительно 1 USD (Доллара США)
        self.fallback_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "RUB": 92.5,
            "GBP": 0.79,
            "JPY": 155.0,
            "CNY": 7.23,
            "KZT": 445.0,
            "BYN": 3.25
        }

        # Настройка окна
        self.title("Currency Converter")
        self.geometry("700x450")
        self.resizable(False, False)

        self.create_widgets()
        self.load_history()

    def create_widgets(self):
        # Левая панель: Ввод и конвертация
        self.left_frame = ctk.CTkFrame(self, width=280, corner_radius=10)
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.lbl_title = ctk.CTkLabel(self.left_frame, text="Конвертер валют", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_title.pack(pady=15)

        # Выбор "Из"
        self.lbl_from = ctk.CTkLabel(self.left_frame, text="Из валюты:")
        self.lbl_from.pack(anchor="w", padx=20)
        self.combo_from = ctk.CTkComboBox(self.left_frame, values=self.currencies, width=200)
        self.combo_from.pack(pady=5)
        self.combo_from.set("USD")

        # Выбор "В"
        self.lbl_to = ctk.CTkLabel(self.left_frame, text="В валюту:")
        self.lbl_to.pack(anchor="w", padx=20)
        self.combo_to = ctk.CTkComboBox(self.left_frame, values=self.currencies, width=200)
        self.combo_to.pack(pady=5)
        self.combo_to.set("RUB")

        # Поле ввода суммы
        self.lbl_amount = ctk.CTkLabel(self.left_frame, text="Сумма:")
        self.lbl_amount.pack(anchor="w", padx=20)
        self.entry_amount = ctk.CTkEntry(self.left_frame, width=200, placeholder_text="Введите число")
        self.entry_amount.pack(pady=5)

        # Кнопка конвертации
        self.btn_convert = ctk.CTkButton(self.left_frame, text="Конвертировать", command=self.convert_currency, width=200)
        self.btn_convert.pack(pady=20)

        # Поле вывода результата
        self.lbl_result = ctk.CTkLabel(self.left_frame, text="Результат: -", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_result.pack(pady=10)

        # Правая панель: Таблица истории
        self.right_frame = ctk.CTkFrame(self, corner_radius=10)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.lbl_history = ctk.CTkLabel(self.right_frame, text="История конвертаций", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_history.pack(pady=10)

        # Настройка стандартной таблицы Tkinter (Treeview)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white", rowheight=25)
        style.map("Treeview", background=[("selected", "#1f538d")])

        self.tree = ttk.Treeview(self.right_frame, columns=("Дата", "Исходное", "Целевое"), show="headings")
        self.tree.heading("Дата", text="Дата и время")
        self.tree.heading("Исходное", text="Исходное")
        self.tree.heading("Целевое", text="Результат")
        
        self.tree.column("Дата", width=130, anchor="center")
        self.tree.column("Исходное", width=110, anchor="center")
        self.tree.column("Целевое", width=110, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

    def convert_currency(self):
        # 1. Валидация ввода
        amount_str = self.entry_amount.get().strip().replace(",", ".")
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Сумма должна быть положительным числом!")
            return

        from_curr = self.combo_from.get()
        to_curr = self.combo_to.get()

        if from_curr == to_curr:
            self.lbl_result.configure(text=f"Результат: {amount:.2f} {to_curr}")
            return

        # 2. Попытка запроса к API
        url = f"https://er-api.com{from_curr}"
        using_fallback = False
        
        try:
            # Ставим таймаут покороче (3 секунды), чтобы программа не зависала при плохой сети
            response = requests.get(url, timeout=3)
            data = response.json()
            
            if response.status_code == 200 and data.get("result") != "error":
                rates = data.get("rates", {})
                rate = rates.get(to_curr)
            else:
                using_fallback = True
        except (requests.exceptions.RequestException, Exception):
            # Если сети нет — включаем резервный режим
            using_fallback = True

        # Логика резервного расчета без интернета
        if using_fallback:
            # Кросс-курс через доллар (USD)
            rate_from_usd = self.fallback_rates.get(from_curr, 1.0)
            rate_to_usd = self.fallback_rates.get(to_curr, 1.0)
            rate = rate_to_usd / rate_from_usd

        # Вычисление
        result = amount * rate
        
        # Обновление интерфейса
        result_text = f"{result:.2f} {to_curr}"
        if using_fallback:
            self.lbl_result.configure(text=f"Результат (оффлайн): {result_text}")
        else:
            self.lbl_result.configure(text=f"Результат: {result_text}")

        # 3. Сохранение в историю
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        history_item = {
            "date": now,
            "from": f"{amount:.2f} {from_curr}",
            "to": result_text
        }
        self.save_to_history(history_item)

    def load_history(self):
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    for item in reversed(history):
                        self.tree.insert("", "end", values=(item["date"], item["from"], item["to"]))
            except json.JSONDecodeError:
                pass

    def save_to_history(self, item):
        history = []
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                pass

        history.append(item)
        if len(history) > 50:
            history.pop(0)

        with open(self.HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)

        self.tree.insert("", 0, values=(item["date"], item["from"], item["to"]))

if __name__ == "__main__":
    app = CurrencyConverterApp()
    app.mainloop()
