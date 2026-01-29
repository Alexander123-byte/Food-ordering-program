import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any


class FoodItem:
    """Класс для представления блюда в меню"""

    def __init__(self, id: int, name: str, description: str, price: float, category: str):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.category = category

    def display(self) -> str:
        return f"{self.id}. {self.name} - {self.price}₽\n   {self.description}"


class Order:
    """Класс для представления заказа"""

    def __init__(self):
        self.items: List[FoodItem] = []
        self.order_time = datetime.now()
        self.total = 0
        self.order_id = self._generate_order_id()

    def _generate_order_id(self) -> str:
        """Генерирует уникальный ID заказа"""
        return f"ORD_{self.order_time.strftime('%Y%m%d_%H%M%S')}"

    def add_item(self, food_item: FoodItem, quantity: int = 1) -> None:
        for _ in range(quantity):
            self.items.append(food_item)
            self.total += food_item.price

    def remove_item(self, food_item: FoodItem) -> bool:
        if food_item in self.items:
            self.items.remove(food_item)
            self.total -= food_item.price
            return True
        return False

    def display_order(self) -> None:
        print("\n" + "=" * 50)
        print("ВАШ ЗАКАЗ:")
        print("=" * 50)

        # Группируем одинаковые позиции
        item_counts: Dict[str, Dict[str, Any]] = {}
        for item in self.items:
            if item.name in item_counts:
                item_counts[item.name]['count'] += 1
            else:
                item_counts[item.name] = {'item': item, 'count': 1}

        for name, data in item_counts.items():
            item = data['item']
            count = data['count']
            print(f"{name} x{count} - {item.price * count}₽")

        print("-" * 50)
        print(f"ИТОГО: {self.total}₽")
        print("=" * 50)

    def save_to_file(self) -> str:
        """Сохраняет заказ в файл в папке orders"""
        # Создаем папку orders, если она не существует
        orders_dir = "orders"
        if not os.path.exists(orders_dir):
            os.makedirs(orders_dir)

        order_data = {
            'order_id': self.order_id,
            'order_time': self.order_time.strftime("%Y-%m-%d %H:%M:%S"),
            'items': [{'name': item.name, 'price': item.price, 'category': item.category}
                      for item in self.items],
            'total': self.total,
            'item_count': len(self.items)
        }

        filename = os.path.join(orders_dir, f"{self.order_id}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(order_data, f, ensure_ascii=False, indent=2)

        return filename


class Restaurant:
    """Основной класс ресторана"""

    def __init__(self, name: str):
        self.name: str = name
        self.menu: List[FoodItem] = []
        self.current_order: Optional[Order] = None
        self.orders_dir = "orders"
        self._initialize_menu()
        self._ensure_orders_directory()

    def _ensure_orders_directory(self) -> None:
        """Создает папку для заказов, если ее нет"""
        if not os.path.exists(self.orders_dir):
            os.makedirs(self.orders_dir)
            print(f"Создана папка для заказов: {self.orders_dir}/")

    def _initialize_menu(self) -> None:
        """Инициализирует меню"""
        self.menu = self.load_menu()

    def load_menu(self) -> List[FoodItem]:
        """Загружает меню из файла или создает стандартное"""
        menu_file = "menu.json"

        if os.path.exists(menu_file):
            try:
                with open(menu_file, 'r', encoding='utf-8') as f:
                    menu_data = json.load(f)
                print(f"Меню загружено из файла: {menu_file}")
            except json.JSONDecodeError:
                print(f"Ошибка чтения {menu_file}. Использую стандартное меню.")
                menu_data = self._get_default_menu()
        else:
            print(f"Файл {menu_file} не найден. Использую стандартное меню.")
            menu_data = self._get_default_menu()
            # Сохраняем стандартное меню в файл
            self._save_default_menu(menu_data, menu_file)

        # Преобразуем данные в объекты FoodItem
        menu_items = []
        for category, items in menu_data.items():
            for item_data in items:
                menu_items.append(FoodItem(
                    id=item_data['id'],
                    name=item_data['name'],
                    description=item_data['description'],
                    price=item_data['price'],
                    category=category
                ))

        return menu_items

    def _get_default_menu(self) -> Dict[str, List[Dict[str, Any]]]:
        """Возвращает стандартное меню"""
        return {
            "Пицца": [
                {"id": 1, "name": "Маргарита", "description": "Томатный соус, моцарелла, базилик", "price": 450},
                {"id": 2, "name": "Пепперони", "description": "Томатный соус, пепперони, моцарелла", "price": 550},
                {"id": 3, "name": "Гавайская", "description": "Томатный соус, курица, ананас, сыр", "price": 500}
            ],
            "Суши": [
                {"id": 4, "name": "Филадельфия", "description": "Лосось, сливочный сыр, огурец", "price": 320},
                {"id": 5, "name": "Калифорния", "description": "Краб-микс, авокадо, огурец, икра", "price": 280}
            ],
            "Напитки": [
                {"id": 6, "name": "Кола", "description": "Coca-Cola 0.5л", "price": 120},
                {"id": 7, "name": "Сок", "description": "Апельсиновый сок 0.3л", "price": 90},
                {"id": 8, "name": "Вода", "description": "Бутылка воды 0.5л", "price": 60}
            ],
            "Десерты": [
                {"id": 9, "name": "Чизкейк", "description": "Классический Нью-Йорк чизкейк", "price": 200},
                {"id": 10, "name": "Тирамису", "description": "Итальянский десерт", "price": 250}
            ]
        }

    def _save_default_menu(self, menu_data: Dict[str, Any], filename: str) -> None:
        """Сохраняет стандартное меню в файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(menu_data, f, ensure_ascii=False, indent=2)
        print(f"Стандартное меню сохранено в файл: {filename}")

    def display_menu(self) -> None:
        """Показывает меню по категориям"""
        print(f"\n{'=' * 60}")
        print(f"МЕНЮ РЕСТОРАНА '{self.name}'".center(60))
        print('=' * 60)

        # Группируем по категориям
        categories: Dict[str, List[FoodItem]] = {}
        for item in self.menu:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)

        # Выводим по категориям
        for category, items in categories.items():
            print(f"\n{category.upper()}:")
            print("-" * 40)
            for item in items:
                print(item.display())

    def find_item_by_id(self, item_id: int) -> Optional[FoodItem]:
        """Находит блюдо по ID"""
        for item in self.menu:
            if item.id == item_id:
                return item
        return None

    def start_new_order(self) -> None:
        """Начинает новый заказ"""
        self.current_order = Order()
        print("\n" + "=" * 60)
        print("НОВЫЙ ЗАКАЗ".center(60))
        print("=" * 60)

    def show_statistics(self) -> None:
        """Показывает статистику заказов"""
        if not os.path.exists(self.orders_dir):
            print(f"\nПапка {self.orders_dir} не существует. Заказов еще нет.")
            return

        order_files = [f for f in os.listdir(self.orders_dir) if f.endswith('.json')]

        if not order_files:
            print("\nЗаказов еще нет.")
            return

        print("\n" + "=" * 60)
        print("СТАТИСТИКА ЗАКАЗОВ".center(60))
        print("=" * 60)
        print(f"Всего заказов: {len(order_files)}")

        # Анализ заказов
        total_revenue = 0
        items_sold = {}

        for order_file in order_files:
            filepath = os.path.join(self.orders_dir, order_file)
            with open(filepath, 'r', encoding='utf-8') as f:
                order_data = json.load(f)
                total_revenue += order_data['total']

                for item in order_data['items']:
                    item_name = item['name']
                    if item_name in items_sold:
                        items_sold[item_name] += 1
                    else:
                        items_sold[item_name] = 1

        print(f"Общая выручка: {total_revenue}₽")

        if items_sold:
            print("\nПопулярные блюда:")
            sorted_items = sorted(items_sold.items(), key=lambda x: x[1], reverse=True)
            for item_name, count in sorted_items[:5]:  # Топ-5
                print(f"  {item_name}: {count} шт.")

    def process_order(self) -> bool:
        """Обрабатывает процесс заказа"""
        self.start_new_order()

        while True:
            print("\n" + "=" * 60)
            print("МЕНЮ ЗАКАЗА".center(60))
            print("=" * 60)
            print("1. Добавить блюдо в заказ")
            print("2. Удалить блюдо из заказа")
            print("3. Просмотреть заказ")
            print("4. Оформить заказ")
            print("5. Отменить заказ")
            print("6. Показать меню")
            print("7. Статистика заказов")
            print("0. Выход в главное меню")

            choice = input("\nВыберите действие: ")

            if choice == "1":
                self.display_menu()
                try:
                    item_id = int(input("\nВведите ID блюда для добавления: "))
                    quantity = int(input("Введите количество: "))

                    if quantity <= 0:
                        print("\n✗ Количество должно быть положительным числом")
                        continue

                    item = self.find_item_by_id(item_id)
                    if item:
                        self.current_order.add_item(item, quantity)
                        print(f"\n✓ Добавлено: {item.name} x{quantity}")
                    else:
                        print("\n✗ Блюдо с таким ID не найдено")
                except ValueError:
                    print("\n✗ Пожалуйста, введите число")

            elif choice == "2":
                if not self.current_order.items:
                    print("\n✗ Ваш заказ пуст")
                    continue

                self.current_order.display_order()
                print("\nКак удалить:")
                print("1. Удалить последнее добавленное блюдо")
                print("2. Удалить конкретное блюдо по номеру")

                remove_choice = input("Выберите способ: ")

                if remove_choice == "1":
                    if self.current_order.items:
                        last_item = self.current_order.items[-1]
                        self.current_order.remove_item(last_item)
                        print(f"\n✓ Удалено последнее блюдо: {last_item.name}")
                elif remove_choice == "2":
                    try:
                        item_num = int(input("Введите номер блюда из списка: "))
                        if 0 < item_num <= len(self.current_order.items):
                            item_to_remove = self.current_order.items[item_num - 1]
                            if self.current_order.remove_item(item_to_remove):
                                print(f"\n✓ Удалено: {item_to_remove.name}")
                            else:
                                print("\n✗ Блюдо не найдено в заказе")
                        else:
                            print("\n✗ Неверный номер блюда")
                    except ValueError:
                        print("\n✗ Пожалуйста, введите число")
                else:
                    print("\n✗ Неверный выбор")

            elif choice == "3":
                if not self.current_order.items:
                    print("\n✗ Ваш заказ пуст")
                else:
                    self.current_order.display_order()

            elif choice == "4":
                if not self.current_order.items:
                    print("\n✗ Ваш заказ пуст! Добавьте блюда.")
                    continue

                self.current_order.display_order()
                print("\n" + "-" * 50)
                print("ОФОРМЛЕНИЕ ЗАКАЗА".center(50))
                print("-" * 50)

                # Запрашиваем данные для доставки
                name = input("Ваше имя: ").strip()
                address = input("Адрес доставки (если нужна): ").strip()
                phone = input("Телефон для связи: ").strip()

                confirm = input("\nПодтвердить заказ? (да/нет): ")

                if confirm.lower() in ['да', 'д', 'yes', 'y']:
                    print("\n" + "=" * 60)
                    print("ЗАКАЗ ОФОРМЛЕН!".center(60))
                    print("=" * 60)
                    print(f"Номер заказа: {self.current_order.order_id}")
                    print(f"Время заказа: {self.current_order.order_time.strftime('%H:%M:%S')}")
                    print(f"Имя клиента: {name}")
                    if address:
                        print(f"Адрес доставки: {address}")
                    print(f"Телефон: {phone}")
                    print(f"Сумма к оплате: {self.current_order.total}₽")

                    # Сохраняем заказ с дополнительными данными
                    filename = self.current_order.save_to_file()
                    print(f"\n✓ Заказ сохранен в файл: {filename}")

                    # Очищаем текущий заказ
                    self.current_order = None
                    break
                else:
                    print("\nЗаказ не оформлен")

            elif choice == "5":
                confirm = input("\nВы уверены, что хотите отменить заказ? (да/нет): ")
                if confirm.lower() in ['да', 'д', 'yes', 'y']:
                    print("\n✗ Заказ отменен")
                    self.current_order = None
                    break

            elif choice == "6":
                self.display_menu()

            elif choice == "7":
                self.show_statistics()

            elif choice == "0":
                print("\nВозвращаемся в главное меню...")
                return True

            else:
                print("\n✗ Неверный выбор. Попробуйте снова.")

        return True
