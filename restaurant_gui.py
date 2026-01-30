"""
restaurant_gui.py
Графический интерфейс системы заказа еды на Tkinter - ПОЛНОСТЬЮ ОБНОВЛЕННЫЙ
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkinter.font import Font
from database import PostgreSQLDatabase
from models import OrderItem
import threading


class RestaurantGUI:
    """Класс графического интерфейса ресторана"""

    def __init__(self, root):
        self.root = root
        self.root.title("🍽️ Ресторан 'Вкусно и Точка'")
        self.root.geometry("1300x750")

        print("Инициализация GUI...")

        # Инициализация базы данных
        print("Подключение к базе данных...")
        self.db = PostgreSQLDatabase()

        # Текущие данные
        self.current_order_items = []
        self.cart_total = 0.0
        self.customer_info = {}
        self.all_menu_items = []
        self.menu_items_cache = []

        # Словарь статусов на русском
        self.status_dict = {
            'pending': 'Ожидает',
            'confirmed': 'Подтвержден',
            'preparing': 'Готовится',
            'delivering': 'Доставляется',
            'delivered': 'Доставлен',
            'cancelled': 'Отменен'
        }

        # Причины недоступности для выбора администратором
        self.unavailability_reasons = [
            "Закончились ингредиенты",
            "Не успеваем в срок",
            "Технические проблемы",
            "Сезонное блюдо",
            "Временно снято с производства",
            "Другая причина"
        ]

        # Стили
        self.setup_styles()

        # Создание интерфейса
        print("Создание интерфейса...")
        self.create_widgets()

        # Загрузка данных
        print("Загрузка данных меню...")
        self.load_menu_data()

        # Центрирование окна
        self.center_window()

        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        print("GUI инициализирован успешно!")

    def setup_styles(self):
        """Настраивает стили интерфейса"""
        self.title_font = Font(family="Helvetica", size=18, weight="bold")
        self.normal_font = Font(family="Helvetica", size=11)
        self.button_font = Font(family="Helvetica", size=11, weight="bold")

        # Цвета
        self.primary_color = "#2c3e50"
        self.secondary_color = "#3498db"
        self.accent_color = "#e74c3c"
        self.success_color = "#2ecc71"

    def center_window(self):
        """Центрирует окно на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """Создает все виджеты интерфейса"""
        # Главный контейнер
        main_container = ttk.Frame(self.root, padding="15")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Конфигурация строк и колонок
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)

        # Заголовок
        header_frame = ttk.Frame(main_container)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        title_label = ttk.Label(
            header_frame,
            text="🍽️ Ресторан 'Вкусно и Точка'",
            font=self.title_font,
            foreground=self.primary_color
        )
        title_label.pack(side=tk.LEFT)

        # Кнопки управления
        control_frame = ttk.Frame(header_frame)
        control_frame.pack(side=tk.RIGHT)

        ttk.Button(
            control_frame,
            text="🔄 Обновить меню",
            command=self.load_menu_data,
            width=20
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            control_frame,
            text="📊 Статистика",
            command=self.show_statistics,
            width=18
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            control_frame,
            text="🔐 Админ-панель",
            command=self.show_admin_panel,
            width=20
        ).pack(side=tk.LEFT, padx=3)

        # Основное содержание
        content_frame = ttk.Frame(main_container)
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)

        # Левая колонка - Меню
        self.create_menu_section(content_frame)

        # Правая колонка - Корзина и информация
        self.create_cart_section(content_frame)

        # Статус бар
        self.status_bar = ttk.Label(
            main_container,
            text="Готов к работе",
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=self.normal_font
        )
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))

    def create_menu_section(self, parent):
        """Создает секцию меню"""
        menu_frame = ttk.LabelFrame(parent, text="📋 Меню", padding="12")
        menu_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 15))
        menu_frame.columnconfigure(0, weight=1)
        menu_frame.rowconfigure(1, weight=1)

        # Фильтры меню
        filter_frame = ttk.Frame(menu_frame)
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 12))

        ttk.Label(filter_frame, text="Категория:", font=self.normal_font).pack(side=tk.LEFT, padx=(0, 5))

        self.category_var = tk.StringVar(value="Все")
        self.category_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.category_var,
            state="readonly",
            width=22,
            font=self.normal_font
        )
        self.category_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.category_combo.bind("<<ComboboxSelected>>", self.filter_menu_by_category)

        ttk.Label(filter_frame, text="Поиск:", font=self.normal_font).pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            filter_frame,
            textvariable=self.search_var,
            width=35,
            font=self.normal_font
        )
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.search_menu)

        # Кнопка сброса фильтров
        ttk.Button(
            filter_frame,
            text="Сбросить фильтры",
            command=self.reset_filters,
            width=18
        ).pack(side=tk.LEFT, padx=(10, 0))

        # Таблица меню
        columns = ("id", "name", "price", "category", "available", "calories")
        self.menu_tree = ttk.Treeview(
            menu_frame,
            columns=columns,
            show="headings",
            height=18,
            selectmode="browse"
        )

        # Заголовки колонок
        self.menu_tree.heading("id", text="ID")
        self.menu_tree.heading("name", text="Название")
        self.menu_tree.heading("price", text="Цена")
        self.menu_tree.heading("category", text="Категория")
        self.menu_tree.heading("available", text="Доступно")
        self.menu_tree.heading("calories", text="Ккал")

        # Ширина колонок
        self.menu_tree.column("id", width=60, anchor=tk.CENTER)
        self.menu_tree.column("name", width=250)
        self.menu_tree.column("price", width=100, anchor=tk.E)
        self.menu_tree.column("category", width=140)
        self.menu_tree.column("available", width=90, anchor=tk.CENTER)
        self.menu_tree.column("calories", width=70, anchor=tk.CENTER)

        self.menu_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Скроллбар для таблицы
        scrollbar = ttk.Scrollbar(
            menu_frame,
            orient=tk.VERTICAL,
            command=self.menu_tree.yview
        )
        self.menu_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))

        # Кнопки добавления в корзину
        add_frame = ttk.Frame(menu_frame)
        add_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(12, 0))

        ttk.Label(add_frame, text="Количество:", font=self.normal_font).pack(side=tk.LEFT, padx=(0, 5))

        self.quantity_var = tk.StringVar(value="1")
        self.quantity_spinbox = ttk.Spinbox(
            add_frame,
            from_=1,
            to=10,
            textvariable=self.quantity_var,
            width=7,
            font=self.normal_font
        )
        self.quantity_spinbox.pack(side=tk.LEFT, padx=(0, 15))

        self.add_to_cart_btn = ttk.Button(
            add_frame,
            text="🛒 Добавить в корзину",
            command=self.add_to_cart,
            state=tk.DISABLED,
            width=20
        )
        self.add_to_cart_btn.pack(side=tk.LEFT)

        # Бинд выбора в таблице
        self.menu_tree.bind("<<TreeviewSelect>>", self.on_menu_item_select)

        # Детали блюда
        self.details_text = scrolledtext.ScrolledText(
            menu_frame,
            height=6,
            width=60,
            wrap=tk.WORD,
            font=self.normal_font
        )
        self.details_text.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(12, 0))
        self.details_text.config(state=tk.DISABLED)

    def create_cart_section(self, parent):
        """Создает секцию корзины"""
        cart_frame = ttk.LabelFrame(parent, text="🛒 Корзина заказа", padding="12")
        cart_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        cart_frame.columnconfigure(0, weight=1)
        cart_frame.rowconfigure(1, weight=1)

        # Таблица корзины
        columns = ("name", "quantity", "price", "subtotal")
        self.cart_tree = ttk.Treeview(
            cart_frame,
            columns=columns,
            show="headings",
            height=12
        )

        # Заголовки колонок
        self.cart_tree.heading("name", text="Название")
        self.cart_tree.heading("quantity", text="Кол-во")
        self.cart_tree.heading("price", text="Цена")
        self.cart_tree.heading("subtotal", text="Сумма")

        # Ширина колонок
        self.cart_tree.column("name", width=180)
        self.cart_tree.column("quantity", width=70, anchor=tk.CENTER)
        self.cart_tree.column("price", width=90, anchor=tk.E)
        self.cart_tree.column("subtotal", width=90, anchor=tk.E)

        self.cart_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Скроллбар для корзины
        cart_scrollbar = ttk.Scrollbar(
            cart_frame,
            orient=tk.VERTICAL,
            command=self.cart_tree.yview
        )
        self.cart_tree.configure(yscrollcommand=cart_scrollbar.set)
        cart_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Кнопки управления корзиной
        cart_buttons_frame = ttk.Frame(cart_frame)
        cart_buttons_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(12, 0))

        ttk.Button(
            cart_buttons_frame,
            text="🗑️ Удалить выбранное",
            command=self.remove_from_cart,
            width=20
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            cart_buttons_frame,
            text="🗑️ Очистить корзину",
            command=self.clear_cart,
            width=18
        ).pack(side=tk.LEFT, padx=2)

        # Итоговая сумма
        total_frame = ttk.Frame(cart_frame)
        total_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(12, 0))

        ttk.Label(
            total_frame,
            text="Итого:",
            font=Font(family="Helvetica", size=12, weight="bold")
        ).pack(side=tk.LEFT)

        self.total_label = ttk.Label(
            total_frame,
            text="0.00 ₽",
            font=Font(family="Helvetica", size=12, weight="bold"),
            foreground=self.accent_color
        )
        self.total_label.pack(side=tk.RIGHT)

        # Разделитель
        ttk.Separator(cart_frame, orient=tk.HORIZONTAL).grid(
            row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=12
        )

        # Форма клиента
        customer_frame = ttk.LabelFrame(cart_frame, text="👤 Информация о клиенте", padding="12")
        customer_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 12))

        # Поля формы
        fields = [
            ("Имя *:", "name", True),
            ("Телефон *:", "phone", True),
            ("Email:", "email", False),
            ("Адрес доставки:", "address", False),
            ("Примечания:", "notes", False)
        ]

        self.customer_entries = {}

        for i, (label, field, required) in enumerate(fields):
            ttk.Label(customer_frame, text=label, font=self.normal_font).grid(
                row=i, column=0, sticky=tk.W, pady=3
            )

            if field == "notes":
                entry = scrolledtext.ScrolledText(customer_frame, height=3, width=35, font=self.normal_font)
                entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=3, padx=(10, 0))
                self.customer_entries[field] = entry
            else:
                entry = ttk.Entry(customer_frame, width=35, font=self.normal_font)
                entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=3, padx=(10, 0))
                self.customer_entries[field] = entry

        # Кнопка оформления заказа
        self.checkout_btn = ttk.Button(
            cart_frame,
            text="✅ Оформить заказ",
            command=self.process_order,
            state=tk.DISABLED,
            width=25
        )
        self.checkout_btn.grid(row=5, column=0, columnspan=2, pady=(12, 0))

        # Привязка изменений для активации кнопки
        for entry in self.customer_entries.values():
            if isinstance(entry, ttk.Entry):
                entry.bind("<KeyRelease>", self.validate_checkout_button)
            else:
                entry.bind("<KeyRelease>", self.validate_checkout_button)

        self.cart_tree.bind("<<TreeviewSelect>>", self.validate_checkout_button)

    def load_menu_data(self):
        """Загружает данные меню в таблицу - ПОКАЗЫВАЕМ ВСЕ БЛЮДА"""
        try:
            # Получаем ВСЕ блюда, включая недоступные
            self.all_menu_items = self.db.get_menu_items(available_only=False)
            self.menu_items_cache = self.all_menu_items.copy()

            # Очищаем таблицу
            for item in self.menu_tree.get_children():
                self.menu_tree.delete(item)

            # Заполняем таблицу из кэша
            for item in self.menu_items_cache:
                available_icon = "✓" if item.is_available else "✗"
                reason = f" ({item.unavailability_reason})" if not item.is_available and item.unavailability_reason else ""

                # Форматируем название для отображения
                display_name = f"{item.name}{reason}"

                self.menu_tree.insert("", tk.END, values=(
                    item.id,
                    display_name,  # ТОЛЬКО имя и причина
                    f"{item.price:.2f} ₽",
                    item.category_name,
                    "Да" if item.is_available else "Нет",
                    item.calories or "-"
                ))

            # Обновляем список категорий
            categories = self.db.get_all_categories()
            if categories:
                category_names = ["Все"] + [cat.name for cat in categories]
                self.category_combo["values"] = category_names
            else:
                self.category_combo["values"] = ["Все"]
                print("⚠ Категории не найдены")

            # Сбрасываем фильтры
            self.category_var.set("Все")
            self.search_var.set("")

            self.update_status(f"Меню загружено: {len(self.all_menu_items)} блюд")

        except Exception as e:
            self.update_status(f"Ошибка загрузки меню: {str(e)}", error=True)
            print(f"Подробности ошибки: {e}")

    def reset_filters(self):
        """Сбрасывает все фильтры"""
        self.category_var.set("Все")
        self.search_var.set("")
        self.filter_menu_by_category()

    def filter_menu_by_category(self, event=None):
        """Фильтрует меню по категории"""
        category = self.category_var.get()
        search_term = self.search_var.get().lower()

        # Фильтруем кэш
        if category == "Все":
            filtered_items = self.all_menu_items
        else:
            filtered_items = [item for item in self.all_menu_items
                            if item.category_name == category]

        # Применяем поиск если есть
        if search_term:
            filtered_items = [item for item in filtered_items
                            if search_term in item.name.lower() or
                            search_term in item.description.lower()]

        self.menu_items_cache = filtered_items

        # Обновляем таблицу
        self.update_menu_table()

    def search_menu(self, event=None):
        """Поиск в меню"""
        search_term = self.search_var.get().lower()
        category = self.category_var.get()

        # Фильтруем по категории
        if category == "Все":
            base_items = self.all_menu_items
        else:
            base_items = [item for item in self.all_menu_items
                         if item.category_name == category]

        # Фильтруем по поисковому запросу
        if search_term:
            filtered_items = [item for item in base_items
                            if search_term in item.name.lower() or
                            search_term in item.description.lower()]
        else:
            filtered_items = base_items

        self.menu_items_cache = filtered_items
        self.update_menu_table()

    def update_menu_table(self):
        """Обновляет таблицу меню из кэша"""
        # Очищаем таблицу
        for item in self.menu_tree.get_children():
            self.menu_tree.delete(item)

        # Заполняем таблицу из кэша
        for item in self.menu_items_cache:
            available_icon = "✓" if item.is_available else "✗"
            reason = f" ({item.unavailability_reason})" if not item.is_available and item.unavailability_reason else ""

            # Форматируем название для отображения
            display_name = f"{item.name}{reason}"

            self.menu_tree.insert("", tk.END, values=(
                item.id,
                display_name,  # ТОЛЬКО имя и причина
                f"{item.price:.2f} ₽",
                item.category_name,
                "Да" if item.is_available else "Нет",
                item.calories or "-"
            ))

        # Обновляем статус
        if self.menu_items_cache:
            available_count = sum(1 for item in self.menu_items_cache if item.is_available)
            self.update_status(f"Найдено {len(self.menu_items_cache)} блюд ({available_count} доступно)")
        else:
            self.update_status("По вашему запросу ничего не найдено")

    def on_menu_item_select(self, event):
        """Обработка выбора блюда в меню"""
        selection = self.menu_tree.selection()

        if selection:
            # Получаем значения выбранной строки
            values = self.menu_tree.item(selection[0], "values")
            if not values:
                self.add_to_cart_btn.config(state=tk.DISABLED)
                return

            try:
                # Первое значение - ID
                item_id = int(values[0])

                # Ищем в кэше
                menu_item = None
                for item in self.menu_items_cache:
                    if item.id == item_id:
                        menu_item = item
                        break

                if menu_item:
                    # Активируем кнопку добавления только если блюдо доступно
                    if menu_item.is_available:
                        self.add_to_cart_btn.config(state=tk.NORMAL)
                    else:
                        self.add_to_cart_btn.config(state=tk.DISABLED)

                    # Показываем детали
                    cooking_time = f"{menu_item.cooking_time} мин." if menu_item.cooking_time else "не указано"
                    calories = menu_item.calories or "не указано"

                    details = f"""
Название: {menu_item.name}
Описание: {menu_item.description}
Цена: {menu_item.price:.2f} ₽
Категория: {menu_item.category_name}
Статус: {'✅ Доступно' if menu_item.is_available else '❌ Недоступно'}
                    """

                    # Добавляем причину недоступности если есть
                    if not menu_item.is_available and menu_item.unavailability_reason:
                        details += f"\nПричина недоступности: {menu_item.unavailability_reason}"

                    details += f"""
Калории: {calories}
Время приготовления: {cooking_time}
                    """

                    self.details_text.config(state=tk.NORMAL)
                    self.details_text.delete(1.0, tk.END)
                    self.details_text.insert(1.0, details.strip())
                    self.details_text.config(state=tk.DISABLED)
                else:
                    self.add_to_cart_btn.config(state=tk.DISABLED)

            except (ValueError, IndexError) as e:
                print(f"Ошибка при обработке выбора: {e}")
                self.add_to_cart_btn.config(state=tk.DISABLED)
                self.details_text.config(state=tk.NORMAL)
                self.details_text.delete(1.0, tk.END)
                self.details_text.insert(1.0, "Ошибка при загрузке деталей блюда")
                self.details_text.config(state=tk.DISABLED)
        else:
            self.add_to_cart_btn.config(state=tk.DISABLED)

    def add_to_cart(self):
        """Добавляет выбранное блюдо в корзину - С ПРОВЕРКОЙ ДОСТУПНОСТИ"""
        try:
            selection = self.menu_tree.selection()
            if not selection:
                messagebox.showwarning("Внимание", "Выберите блюдо из меню")
                return

            # Получаем значения выбранной строки
            values = self.menu_tree.item(selection[0], "values")
            if not values:
                messagebox.showerror("Ошибка", "Не удалось получить данные блюда")
                return

            # Первое значение - ID
            item_id = int(values[0])

            # Находим блюдо в кэше для проверки доступности
            menu_item = None
            for item in self.menu_items_cache:
                if item.id == item_id:
                    menu_item = item
                    break

            if not menu_item:
                messagebox.showerror("Ошибка", "Блюдо не найдено")
                return

            # Проверяем доступность
            if not menu_item.is_available:
                reason = menu_item.unavailability_reason or "не указана"
                messagebox.showwarning(
                    "Блюдо недоступно",
                    f"Блюдо '{menu_item.name}' временно недоступно.\n\nПричина: {reason}"
                )
                return

            item_name = menu_item.name
            price = menu_item.price

            # Получаем количество
            try:
                quantity = int(self.quantity_spinbox.get())
                if quantity <= 0:
                    messagebox.showwarning("Внимание", "Количество должно быть больше 0")
                    return
            except ValueError:
                messagebox.showerror("Ошибка", "Пожалуйста, введите корректное количество")
                return

            # Добавляем в корзину
            subtotal = price * quantity

            self.cart_tree.insert("", tk.END, values=(
                item_name,
                quantity,
                f"{price:.2f} ₽",
                f"{subtotal:.2f} ₽"
            ))

            # Сохраняем в список для базы данных
            self.current_order_items.append(OrderItem(
                menu_item_id=menu_item.id,
                quantity=quantity,
                price_at_order=price,
                menu_item_name=item_name
            ))

            # Обновляем общую сумму
            self.cart_total += subtotal
            self.total_label.config(text=f"{self.cart_total:.2f} ₽")

            # Активируем кнопку оформления
            self.validate_checkout_button()

            self.update_status(f"Добавлено: {item_name} x{quantity}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
            print(f"Подробности ошибки в add_to_cart: {e}")

    def remove_from_cart(self):
        """Удаляет выбранный элемент из корзины"""
        selection = self.cart_tree.selection()

        if not selection:
            messagebox.showwarning("Внимание", "Выберите элемент для удаления")
            return

        # Получаем данные для удаления
        values = self.cart_tree.item(selection[0], "values")
        subtotal = float(values[3].replace(" ₽", ""))
        item_name = values[0]
        quantity = int(values[1])

        # Обновляем общую сумму
        self.cart_total -= subtotal
        self.total_label.config(text=f"{self.cart_total:.2f} ₽")

        # Удаляем из списка
        for i, item in enumerate(self.current_order_items):
            if item.menu_item_name == item_name and item.quantity == quantity:
                del self.current_order_items[i]
                break

        # Удаляем из таблицы
        self.cart_tree.delete(selection[0])

        self.update_status(f"Удалено: {item_name}")

        # Проверяем кнопку оформления
        self.validate_checkout_button()

    def clear_cart(self):
        """Очищает корзину полностью"""
        if not self.current_order_items:
            return

        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить корзину?"):
            # Очищаем таблицу
            for item in self.cart_tree.get_children():
                self.cart_tree.delete(item)

            # Сбрасываем данные
            self.current_order_items.clear()
            self.cart_total = 0.0
            self.total_label.config(text="0.00 ₽")

            # Деактивируем кнопку оформления
            self.checkout_btn.config(state=tk.DISABLED)

            self.update_status("Корзина очищена")

    def validate_checkout_button(self, event=None):
        """Проверяет, можно ли активировать кнопку оформления"""
        has_items = len(self.current_order_items) > 0
        has_name = self.customer_entries["name"].get().strip() != ""
        has_phone = self.customer_entries["phone"].get().strip() != ""

        if has_items and has_name and has_phone:
            self.checkout_btn.config(state=tk.NORMAL)
        else:
            self.checkout_btn.config(state=tk.DISABLED)

    def process_order(self):
        """Оформляет заказ"""
        try:
            # Проверяем обязательные поля
            name = self.customer_entries["name"].get().strip()
            phone = self.customer_entries["phone"].get().strip()
            email = self.customer_entries["email"].get().strip()
            address = self.customer_entries["address"].get().strip()

            notes = ""
            if isinstance(self.customer_entries["notes"], scrolledtext.ScrolledText):
                notes = self.customer_entries["notes"].get(1.0, tk.END).strip()
            else:
                notes = self.customer_entries["notes"].get().strip()

            if not name or not phone:
                messagebox.showerror("Ошибка", "Имя и телефон обязательны для заполнения")
                return

            # Создаем заказ в отдельном потоке
            def create_order_thread():
                try:
                    # Находим или создаем клиента
                    customer = self.db.find_or_create_customer(
                        name, phone, email, address
                    )

                    # Создаем заказ
                    order_id, order_number = self.db.create_order(
                        customer_id=customer.id,
                        items=self.current_order_items,
                        delivery_address=address,
                        notes=notes,
                        payment_method="cash"
                    )

                    # Обновляем интерфейс в основном потоке
                    self.root.after(0, self.order_success, order_number, customer, address)

                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Ошибка оформления", f"Произошла ошибка: {str(e)}"
                    ))
                    self.root.after(0, lambda: self.update_status(
                        f"Ошибка оформления: {str(e)}", error=True
                    ))

            # Запускаем поток
            threading.Thread(target=create_order_thread, daemon=True).start()

            # Показываем индикатор загрузки
            self.update_status("Оформление заказа...")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")

    def order_success(self, order_number, customer, address):
        """Обработка успешного оформления заказа"""
        # Показываем сообщение об успехе
        success_msg = f"""
✅ Заказ успешно оформлен!

Номер заказа: {order_number}
Имя: {customer.name}
Телефон: {customer.phone}
Сумма: {self.cart_total:.2f} ₽
        """

        if address:
            success_msg += f"\nАдрес доставки: {address}"

        success_msg += "\n\nСпасибо за заказ!"

        messagebox.showinfo("Заказ оформлен", success_msg)

        # Очищаем корзину и форму
        self.clear_cart_after_order()
        self.clear_customer_form()

        # Обновляем статус
        self.update_status(f"Заказ {order_number} успешно оформлен")

    def clear_cart_after_order(self):
        """Очищает корзину после успешного оформления заказа"""
        # Очищаем таблицу
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        # Сбрасываем данные
        self.current_order_items.clear()
        self.cart_total = 0.0
        self.total_label.config(text="0.00 ₽")

        # Деактивируем кнопку оформления
        self.checkout_btn.config(state=tk.DISABLED)

    def clear_customer_form(self):
        """Очищает форму клиента"""
        for field, widget in self.customer_entries.items():
            if isinstance(widget, ttk.Entry):
                widget.delete(0, tk.END)
            elif isinstance(widget, scrolledtext.ScrolledText):
                widget.delete(1.0, tk.END)

    def show_statistics(self):
        """Показывает статистику в отдельном окне"""
        try:
            stats = self.db.get_order_statistics()

            # Создаем окно статистики
            stats_window = tk.Toplevel(self.root)
            stats_window.title("📊 Статистика заказов")
            stats_window.geometry("600x500")
            stats_window.transient(self.root)
            stats_window.grab_set()

            # Центрируем окно
            stats_window.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (600 // 2)
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (500 // 2)
            stats_window.geometry(f"600x500+{x}+{y}")

            # Создаем содержимое
            content_frame = ttk.Frame(stats_window, padding="25")
            content_frame.pack(fill=tk.BOTH, expand=True)

            # Основная статистика
            ttk.Label(
                content_frame,
                text="Общая статистика",
                font=Font(family="Helvetica", size=14, weight="bold")
            ).pack(anchor=tk.W, pady=(0, 15))

            stats_text = f"""
Всего заказов: {stats['total_orders']}
Общая выручка: {stats['total_revenue']:.2f} ₽
Средний чек: {stats['avg_order_value']:.2f} ₽
Уникальных клиентов: {stats['unique_customers']}
            """

            ttk.Label(
                content_frame,
                text=stats_text.strip(),
                font=self.normal_font
            ).pack(anchor=tk.W, pady=(0, 25))

            # Популярные блюда
            if stats['popular_items']:
                ttk.Label(
                    content_frame,
                    text="Самые популярные блюда:",
                    font=Font(family="Helvetica", size=12, weight="bold")
                ).pack(anchor=tk.W, pady=(0, 10))

                for item_name, quantity in stats['popular_items'][:8]:
                    ttk.Label(
                        content_frame,
                        text=f"  • {item_name}: {quantity} шт.",
                        font=self.normal_font
                    ).pack(anchor=tk.W)

            # Кнопка закрытия
            ttk.Button(
                content_frame,
                text="Закрыть",
                command=stats_window.destroy,
                width=15
            ).pack(side=tk.BOTTOM, pady=(20, 0))

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить статистику: {str(e)}")

    def show_admin_panel(self):
        """Показывает административную панель"""
        # Создаем окно админ-панели
        admin_window = tk.Toplevel(self.root)
        admin_window.title("🔐 Административная панель")
        admin_window.geometry("1000x700")
        admin_window.transient(self.root)

        # Центрируем окно
        admin_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (1000 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (700 // 2)
        admin_window.geometry(f"1000x700+{x}+{y}")

        # Запрашиваем пароль
        password_frame = ttk.Frame(admin_window, padding="60")
        password_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            password_frame,
            text="Введите пароль администратора:",
            font=Font(family="Helvetica", size=12)
        ).pack(pady=(0, 15))

        password_var = tk.StringVar()
        password_entry = ttk.Entry(
            password_frame,
            textvariable=password_var,
            show="*",
            width=25,
            font=self.normal_font
        )
        password_entry.pack(pady=(0, 25))
        password_entry.focus()

        def check_password():
            if password_var.get() == "admin123":
                password_frame.destroy()
                self.create_admin_content(admin_window)
            else:
                messagebox.showerror("Ошибка", "Неверный пароль")
                admin_window.destroy()

        ttk.Button(
            password_frame,
            text="Войти",
            command=check_password,
            width=15
        ).pack()

        # Привязываем Enter к проверке пароля
        password_entry.bind("<Return>", lambda e: check_password())

    def create_admin_content(self, window):
        """Создает содержимое админ-панели"""
        # Notebook для вкладок
        notebook = ttk.Notebook(window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Вкладка "Заказы"
        orders_frame = ttk.Frame(notebook)
        notebook.add(orders_frame, text="📦 Управление заказами")

        # Панель управления заказами
        order_control_frame = ttk.Frame(orders_frame, padding="10")
        order_control_frame.pack(fill=tk.X)

        ttk.Label(order_control_frame, text="Управление статусом:", font=self.normal_font).pack(side=tk.LEFT, padx=(0, 10))

        # Статусы на русском
        russian_statuses = list(self.status_dict.values())
        self.status_var = tk.StringVar(value=russian_statuses[0])
        status_combo = ttk.Combobox(
            order_control_frame,
            textvariable=self.status_var,
            values=russian_statuses,
            state="readonly",
            width=20,
            font=self.normal_font
        )
        status_combo.pack(side=tk.LEFT, padx=(0, 15))

        self.selected_order_id = None
        self.selected_order_number = None

        # Контейнер для таблицы и деталей
        orders_container = ttk.Frame(orders_frame)
        orders_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Таблица заказов
        self.admin_orders_tree = ttk.Treeview(
            orders_container,
            columns=("number", "date", "customer", "amount", "status"),
            show="headings",
            height=22
        )

        # Заголовки
        self.admin_orders_tree.heading("number", text="Номер заказа")
        self.admin_orders_tree.heading("date", text="Дата и время")
        self.admin_orders_tree.heading("customer", text="Клиент")
        self.admin_orders_tree.heading("amount", text="Сумма")
        self.admin_orders_tree.heading("status", text="Статус")

        # Ширина колонок
        self.admin_orders_tree.column("number", width=170)
        self.admin_orders_tree.column("date", width=160)
        self.admin_orders_tree.column("customer", width=170)
        self.admin_orders_tree.column("amount", width=110)
        self.admin_orders_tree.column("status", width=130)

        self.admin_orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Скроллбар
        scrollbar = ttk.Scrollbar(orders_container, orient=tk.VERTICAL, command=self.admin_orders_tree.yview)
        self.admin_orders_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Панель деталей заказа
        admin_details_frame = ttk.LabelFrame(orders_container, text="Детали заказа", padding="10")
        admin_details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(15, 0))

        self.admin_order_details_text = scrolledtext.ScrolledText(
            admin_details_frame,
            height=30,
            width=45,
            wrap=tk.WORD,
            font=self.normal_font,
            state=tk.DISABLED
        )
        self.admin_order_details_text.pack(fill=tk.BOTH, expand=True)

        # Функция для загрузки заказов
        def load_orders():
            """Загружает заказы в таблицу"""
            try:
                # Очищаем таблицу
                for item in self.admin_orders_tree.get_children():
                    self.admin_orders_tree.delete(item)

                # Загружаем заказы
                orders = self.db.get_all_orders(limit=100)
                if orders:
                    for order in orders:
                        # Конвертируем статус на русский
                        status_russian = self.status_dict.get(order['status'], order['status'])
                        self.admin_orders_tree.insert("", tk.END, values=(
                            order['order_number'],
                            order['created_at'].strftime("%Y-%m-%d %H:%M"),
                            order['customer_name'],
                            f"{order['total_amount']:.2f} ₽",
                            status_russian
                        ))
                else:
                    # Если нет заказов, показываем сообщение
                    self.admin_orders_tree.insert("", tk.END, values=(
                        "Нет данных", "", "", "", ""
                    ))

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить заказы: {str(e)}")

        # Функция для отображения деталей заказа
        def show_order_details(order_data):
            """Показывает детали выбранного заказа"""
            # Конвертируем статус на русский
            status_russian = self.status_dict.get(order_data['status'], order_data['status'])

            details = f"""
ЗАКАЗ № {order_data['order_number']}
{'='*45}

Статус: {status_russian}
Дата: {order_data['created_at']}
Сумма: {order_data['total_amount']:.2f} ₽
Способ оплаты: {order_data['payment_method'] or 'не указан'}

КЛИЕНТ:
Имя: {order_data['customer_name']}
Телефон: {order_data['customer_phone']}
Email: {order_data['customer_email'] or 'не указан'}
Адрес: {order_data['delivery_address'] or 'не указан'}

ПОЗИЦИИ ЗАКАЗА:
{'='*45}
            """

            for item in order_data['items']:
                details += f"\n{item['item_name']} x{item['quantity']}"
                details += f" - {item['subtotal']:.2f} ₽"

            details += f"\n{'='*45}\nИТОГО: {order_data['total_amount']:.2f} ₽"

            if order_data['notes']:
                details += f"\n\nПРИМЕЧАНИЯ:\n{order_data['notes']}"

            self.admin_order_details_text.config(state=tk.NORMAL)
            self.admin_order_details_text.delete(1.0, tk.END)
            self.admin_order_details_text.insert(1.0, details.strip())
            self.admin_order_details_text.config(state=tk.DISABLED)

        # Функция для обновления статуса заказа
        def update_order_status():
            if not self.selected_order_id:
                messagebox.showwarning("Внимание", "Выберите заказ из таблицы")
                return

            # Конвертируем русский статус обратно в английский для базы
            new_status_russian = self.status_var.get()
            new_status_english = None
            for eng, rus in self.status_dict.items():
                if rus == new_status_russian:
                    new_status_english = eng
                    break

            if not new_status_english:
                messagebox.showerror("Ошибка", "Неверный статус")
                return

            if self.db.update_order_status(self.selected_order_id, new_status_english):
                messagebox.showinfo("Успех", f"Статус заказа {self.selected_order_number} обновлен на '{new_status_russian}'")
                load_orders()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить статус заказа")

        # Обработка выбора заказа
        def on_order_select(event):
            selection = self.admin_orders_tree.selection()
            if selection:
                values = self.admin_orders_tree.item(selection[0], "values")
                self.selected_order_number = values[0]

                # Получаем полную информацию о заказе
                order_data = self.db.get_order_by_number(self.selected_order_number)
                if order_data:
                    self.selected_order_id = order_data['order_id']

                    # Устанавливаем текущий статус
                    status_russian = self.status_dict.get(order_data['status'], order_data['status'])
                    self.status_var.set(status_russian)

                    # Показываем детали заказа
                    show_order_details(order_data)

        self.admin_orders_tree.bind("<<TreeviewSelect>>", on_order_select)

        # Кнопки управления
        ttk.Button(
            order_control_frame,
            text="Обновить статус",
            command=update_order_status,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            order_control_frame,
            text="🔄 Обновить список",
            command=load_orders,
            width=15
        ).pack(side=tk.LEFT)

        # Загружаем заказы
        load_orders()

        # Вкладка "Управление меню"
        menu_frame = ttk.Frame(notebook)
        notebook.add(menu_frame, text="📋 Управление меню")

        # Содержимое вкладки меню
        menu_content = ttk.Frame(menu_frame, padding="25")
        menu_content.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            menu_content,
            text="Управление меню",
            font=Font(family="Helvetica", size=14, weight="bold")
        ).pack(pady=(0, 25))

        # Кнопки управления
        btn_frame = ttk.Frame(menu_content)
        btn_frame.pack(pady=15)

        ttk.Button(
            btn_frame,
            text="➕ Добавить новое блюдо",
            command=self.show_add_dish_dialog,
            width=25
        ).pack(side=tk.LEFT, padx=8)

        ttk.Button(
            btn_frame,
            text="🔄 Обновить доступность блюда",
            command=self.show_availability_dialog_improved,
            width=28
        ).pack(side=tk.LEFT, padx=8)

        # Информационная панель
        info_frame = ttk.LabelFrame(menu_content, text="Информация", padding="15")
        info_frame.pack(fill=tk.X, pady=20)

        info_text = """
Для управления меню используйте кнопки выше:

1. "Добавить новое блюдо" - создание новых позиций в меню
2. "Обновить доступность блюда" - изменение статуса доступности

Все изменения сразу отображаются в основном меню.
Для удаления блюда обратитесь к администратору базы данных.
        """

        ttk.Label(
            info_frame,
            text=info_text.strip(),
            font=self.normal_font,
            justify=tk.LEFT
        ).pack(anchor=tk.W)

        # Вкладка "Статистика"
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="📊 Детальная статистика")

        # Показываем статистику
        stats = self.db.get_order_statistics()

        stats_text = f"""
Общая статистика:
------------------
Всего заказов: {stats['total_orders']}
Общая выручка: {stats['total_revenue']:.2f} ₽
Средний чек: {stats['avg_order_value']:.2f} ₽
Уникальных клиентов: {stats['unique_customers']}

Самые популярные блюда (топ-10):
-------------------------------"""

        for i, (item_name, quantity) in enumerate(stats['popular_items'][:10], 1):
            stats_text += f"\n{i}. {item_name}: {quantity} шт."

        stats_label = ttk.Label(
            stats_frame,
            text=stats_text,
            font=Font(family="Helvetica", size=11),
            justify=tk.LEFT
        )
        stats_label.pack(padx=30, pady=30, anchor=tk.W)

    def show_add_dish_dialog(self):
        """Показывает диалог добавления блюда"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить новое блюдо")
        dialog.geometry("450x550")
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрируем
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (450 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (550 // 2)
        dialog.geometry(f"450x550+{x}+{y}")

        # Форма
        form_frame = ttk.Frame(dialog, padding="25")
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Получаем список категорий для выбора
        categories = self.db.get_all_categories()
        category_names = [cat.name for cat in categories]
        category_ids = {cat.name: cat.id for cat in categories}

        fields = [
            ("Название блюда *:", "name", "entry"),
            ("Описание:", "description", "text"),
            ("Цена *:", "price", "entry"),
            ("Категория *:", "category", "combo"),
            ("Калории:", "calories", "entry"),
            ("Время приготовления (мин):", "cooking_time", "entry")
        ]

        entries = {}

        for i, (label, field, field_type) in enumerate(fields):
            ttk.Label(form_frame, text=label, font=self.normal_font).grid(
                row=i, column=0, sticky=tk.W, pady=8
            )

            if field_type == "entry":
                entry = ttk.Entry(form_frame, width=35, font=self.normal_font)
                entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=8, padx=(15, 0))
                entries[field] = entry
            elif field_type == "text":
                entry = scrolledtext.ScrolledText(form_frame, height=4, width=35, font=self.normal_font)
                entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=8, padx=(15, 0))
                entries[field] = entry
            elif field_type == "combo":
                entry = ttk.Combobox(form_frame, values=category_names, state="readonly", width=33, font=self.normal_font)
                entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=8, padx=(15, 0))
                if category_names:
                    entry.set(category_names[0])
                entries[field] = entry

        # Подсказка
        ttk.Label(
            form_frame,
            text="* - обязательные поля",
            font=Font(family="Helvetica", size=9),
            foreground="gray"
        ).grid(row=len(fields), column=0, columnspan=2, pady=(10, 0))

        # Кнопки
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=(25, 0))

        def save_dish():
            try:
                name = entries["name"].get().strip()
                if not name:
                    messagebox.showerror("Ошибка", "Название блюда обязательно")
                    return

                # Получаем описание
                if "description" in entries and isinstance(entries["description"], scrolledtext.ScrolledText):
                    description = entries["description"].get(1.0, tk.END).strip()
                else:
                    description = entries["description"].get().strip()

                # Получаем цену
                price_str = entries["price"].get().strip()
                if not price_str:
                    messagebox.showerror("Ошибка", "Цена обязательна")
                    return

                price = float(price_str)
                if price <= 0:
                    messagebox.showerror("Ошибка", "Цена должна быть больше 0")
                    return

                # Получаем категорию
                category_name = entries["category"].get()
                if not category_name:
                    messagebox.showerror("Ошибка", "Выберите категорию")
                    return

                category_id = category_ids.get(category_name)
                if not category_id:
                    messagebox.showerror("Ошибка", "Неверная категория")
                    return

                # Обработка необязательных полей
                calories_str = entries["calories"].get().strip()
                cooking_time_str = entries["cooking_time"].get().strip()

                calories = int(calories_str) if calories_str else None
                cooking_time = int(cooking_time_str) if cooking_time_str else None

                # Сохраняем в базу
                success = self.db.add_menu_item(
                    name=name,
                    description=description,
                    price=price,
                    category_id=category_id,
                    calories=calories,
                    cooking_time=cooking_time
                )

                if success:
                    messagebox.showinfo("Успех", f"Блюдо '{name}' успешно добавлено в меню!")
                    dialog.destroy()
                    self.load_menu_data()
                else:
                    messagebox.showerror("Ошибка", "Не удалось добавить блюдо. Проверьте данные.")

            except ValueError as e:
                messagebox.showerror("Ошибка", f"Некорректные данные: {str(e)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")

        ttk.Button(
            button_frame,
            text="💾 Сохранить",
            command=save_dish,
            width=15
        ).pack(side=tk.LEFT, padx=8)

        ttk.Button(
            button_frame,
            text="❌ Отмена",
            command=dialog.destroy,
            width=15
        ).pack(side=tk.LEFT, padx=8)

    def show_availability_dialog_improved(self):
        """Улучшенный диалог обновления доступности - с причиной"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Обновить доступность блюда")
        dialog.geometry("550x450")
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрируем
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (550 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (450 // 2)
        dialog.geometry(f"550x450+{x}+{y}")

        # Форма
        form_frame = ttk.Frame(dialog, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(
            form_frame,
            text="Выберите блюдо для изменения доступности:",
            font=Font(family="Helvetica", size=11, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))

        # Получаем список всех блюд
        all_items = self.db.get_menu_items(available_only=False)
        item_names = []
        item_ids = {}

        for item in all_items:
            status = "✓" if item.is_available else "✗"
            reason = f" ({item.unavailability_reason})" if not item.is_available and item.unavailability_reason else ""
            item_names.append(f"{item.id}. {status} {item.name}{reason}")
            item_ids[item.id] = item

        ttk.Label(form_frame, text="Блюдо:", font=self.normal_font).grid(
            row=1, column=0, sticky=tk.W, pady=8
        )

        selected_item_var = tk.StringVar()
        item_combo = ttk.Combobox(
            form_frame,
            textvariable=selected_item_var,
            values=item_names,
            state="readonly",
            width=45,
            font=self.normal_font
        )
        item_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=8, padx=(15, 0))

        ttk.Label(form_frame, text="Новая доступность:", font=self.normal_font).grid(
            row=2, column=0, sticky=tk.W, pady=8
        )

        self.availability_var = tk.StringVar(value="available")
        availability_frame = ttk.Frame(form_frame)
        availability_frame.grid(row=2, column=1, sticky=tk.W, pady=8, padx=(15, 0))

        def on_availability_change(*args):
            # Показываем/скрываем поле причины в зависимости от выбора
            if self.availability_var.get() == "unavailable":
                reason_label.grid()
                reason_combo.grid()
            else:
                reason_label.grid_remove()
                reason_combo.grid_remove()

        ttk.Radiobutton(
            availability_frame,
            text="✅ Доступно",
            variable=self.availability_var,
            value="available",
            command=on_availability_change
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Radiobutton(
            availability_frame,
            text="❌ Недоступно",
            variable=self.availability_var,
            value="unavailable",
            command=on_availability_change
        ).pack(side=tk.LEFT)

        # Поле для причины недоступности
        reason_label = ttk.Label(form_frame, text="Причина недоступности:", font=self.normal_font)
        reason_label.grid(row=3, column=0, sticky=tk.W, pady=8)
        reason_label.grid_remove()

        self.reason_var = tk.StringVar(value=self.unavailability_reasons[0])
        reason_combo = ttk.Combobox(
            form_frame,
            textvariable=self.reason_var,
            values=self.unavailability_reasons,
            state="readonly",
            width=43,
            font=self.normal_font
        )
        reason_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=8, padx=(15, 0))
        reason_combo.grid_remove()

        # Поле для своей причины
        custom_reason_label = ttk.Label(form_frame, text="Своя причина:", font=self.normal_font)
        custom_reason_label.grid(row=4, column=0, sticky=tk.W, pady=8)
        custom_reason_label.grid_remove()

        self.custom_reason_var = tk.StringVar()
        custom_reason_entry = ttk.Entry(
            form_frame,
            textvariable=self.custom_reason_var,
            width=45,
            font=self.normal_font
        )
        custom_reason_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=8, padx=(15, 0))
        custom_reason_entry.grid_remove()

        def on_reason_change(*args):
            # Показываем поле для своей причины если выбрано "Другая причина"
            if self.reason_var.get() == "Другая причина":
                custom_reason_label.grid()
                custom_reason_entry.grid()
            else:
                custom_reason_label.grid_remove()
                custom_reason_entry.grid_remove()

        reason_combo.bind("<<ComboboxSelected>>", on_reason_change)

        # Информация о выбранном блюде
        info_label = ttk.Label(
            form_frame,
            text="",
            font=Font(family="Helvetica", size=9),
            foreground="gray"
        )
        info_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(15, 0))

        def on_item_select(event):
            selection = item_combo.get()
            if selection:
                try:
                    # Извлекаем ID из строки
                    item_id = int(selection.split(".")[0])
                    item = item_ids.get(item_id)
                    if item:
                        # Устанавливаем текущий статус
                        if item.is_available:
                            self.availability_var.set("available")
                        else:
                            self.availability_var.set("unavailable")
                            if item.unavailability_reason:
                                # Ищем причину в списке или устанавливаем "Другая причина"
                                if item.unavailability_reason in self.unavailability_reasons:
                                    self.reason_var.set(item.unavailability_reason)
                                else:
                                    self.reason_var.set("Другая причина")
                                    self.custom_reason_var.set(item.unavailability_reason)

                        # Вызываем изменение для показа/скрытия полей
                        on_availability_change()
                        on_reason_change()

                        info_label.config(
                            text=f"Текущая цена: {item.price}₽ | Категория: {item.category_name}"
                        )
                except:
                    pass

        item_combo.bind("<<ComboboxSelected>>", on_item_select)

        # Кнопки
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(25, 0))

        def update_availability():
            selection = selected_item_var.get()
            if not selection:
                messagebox.showwarning("Внимание", "Выберите блюдо")
                return

            try:
                # Извлекаем ID из строки
                item_id = int(selection.split(".")[0])
                is_available = (self.availability_var.get() == "available")

                # Получаем причину если блюдо становится недоступным
                unavailability_reason = None
                if not is_available:
                    reason = self.reason_var.get()
                    if reason == "Другая причина":
                        custom_reason = self.custom_reason_var.get().strip()
                        if custom_reason:
                            unavailability_reason = custom_reason
                        else:
                            messagebox.showwarning("Внимание", "Укажите причину недоступности")
                            return
                    else:
                        unavailability_reason = reason

                # Обновляем в базе данных
                if self.db.update_menu_item_availability(item_id, is_available, unavailability_reason):
                    messagebox.showinfo("Успех", "Доступность блюда обновлена!")
                    dialog.destroy()
                    self.load_menu_data()
                else:
                    messagebox.showerror("Ошибка", "Не удалось обновить доступность")

            except ValueError:
                messagebox.showerror("Ошибка", "Ошибка при обработке данных")

        ttk.Button(
            button_frame,
            text="🔄 Обновить",
            command=update_availability,
            width=15
        ).pack(side=tk.LEFT, padx=8)

        ttk.Button(
            button_frame,
            text="❌ Отмена",
            command=dialog.destroy,
            width=15
        ).pack(side=tk.LEFT, padx=8)

    def update_status(self, message, error=False):
        """Обновляет статус бар"""
        if error:
            self.status_bar.config(text=f"Ошибка: {message}", foreground="red")
        else:
            self.status_bar.config(text=message, foreground="black")

    def on_closing(self):
        """Обработка закрытия окна"""
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.db.close()
            self.root.destroy()


def main():
    """Основная функция запуска GUI"""
    root = tk.Tk()

    # Устанавливаем тему
    try:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", font=("Helvetica", 10))
    except:
        pass

    app = RestaurantGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
