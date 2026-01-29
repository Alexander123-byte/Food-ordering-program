"""
restaurant_system.py
Главный файл системы заказа еды с PostgreSQL
"""

from database import PostgreSQLDatabase
from models import MenuItem, OrderItem, Customer, Category
from datetime import datetime
import uuid


class RestaurantSystem:
    """Основной класс системы ресторана"""

    def __init__(self):
        self.db = PostgreSQLDatabase()
        self.current_order_items = []

    def display_menu_by_categories(self):
        """Показывает меню сгруппированное по категориям"""
        categories = self.db.get_all_categories()

        print(f"\n{'=' * 60}")
        print("МЕНЮ РЕСТОРАНА".center(60))
        print('=' * 60)

        for category in categories:
            items = self.db.get_menu_items(category_id=category.id, available_only=True)

            if items:
                print(f"\n{category.name.upper()} ({category.description}):")
                print("-" * 40)
                for item in items:
                    print(item.display())

    def add_to_order(self):
        """Добавляет блюдо в текущий заказ"""
        self.display_menu_by_categories()

        try:
            item_id = int(input("\nВведите ID блюда: "))
            quantity = int(input("Введите количество: "))

            if quantity <= 0:
                print("✗ Количество должно быть положительным")
                return

            menu_item = self.db.get_menu_item_by_id(item_id)
            if not menu_item:
                print("✗ Блюдо не найдено")
                return

            if not menu_item.is_available:
                print("✗ Это блюдо временно недоступно")
                return

            # Добавляем в текущий заказ
            self.current_order_items.append(OrderItem(
                menu_item_id=menu_item.id,
                quantity=quantity,
                price_at_order=menu_item.price,
                menu_item_name=menu_item.name
            ))

            print(f"✓ Добавлено: {menu_item.name} x{quantity}")

        except ValueError:
            print("✗ Пожалуйста, введите корректные числа")

    def show_current_order(self):
        """Показывает текущий заказ"""
        if not self.current_order_items:
            print("\nВаш заказ пуст")
            return

        print("\n" + "=" * 50)
        print("ТЕКУЩИЙ ЗАКАЗ")
        print("=" * 50)

        total = 0
        for i, item in enumerate(self.current_order_items, 1):
            subtotal = item.subtotal
            total += subtotal
            print(f"{i}. {item.menu_item_name} x{item.quantity} - {subtotal}₽")

        print("-" * 50)
        print(f"ИТОГО: {total}₽")
        print("=" * 50)

    def process_order(self):
        """Обрабатывает оформление заказа"""
        if not self.current_order_items:
            print("✗ Ваш заказ пуст")
            return

        self.show_current_order()

        print("\n" + "=" * 50)
        print("ОФОРМЛЕНИЕ ЗАКАЗА")
        print("=" * 50)

        # Собираем информацию о клиенте
        name = input("Ваше имя: ").strip()
        phone = input("Телефон: ").strip()
        email = input("Email (необязательно): ").strip()
        address = input("Адрес доставки: ").strip()
        notes = input("Примечания к заказу: ").strip()

        if not name or not phone:
            print("✗ Имя и телефон обязательны")
            return

        try:
            # Находим или создаем клиента
            customer = self.db.find_or_create_customer(name, phone, email, address)

            # Создаем заказ в базе данных
            order_id, order_number = self.db.create_order(
                customer_id=customer.id,
                items=self.current_order_items,
                delivery_address=address,
                notes=notes,
                payment_method="cash"
            )

            print("\n" + "=" * 60)
            print("ЗАКАЗ УСПЕШНО ОФОРМЛЕН!".center(60))
            print("=" * 60)
            print(f"Номер заказа: {order_number}")
            print(f"Имя: {customer.name}")
            print(f"Телефон: {customer.phone}")
            if address:
                print(f"Адрес доставки: {address}")
            print(f"Сумма: {sum(item.subtotal for item in self.current_order_items)}₽")
            print("=" * 60)

            # Очищаем текущий заказ
            self.current_order_items = []

        except Exception as e:
            print(f"✗ Ошибка при оформлении заказа: {e}")

    def show_statistics(self):
        """Показывает статистику"""
        stats = self.db.get_order_statistics()

        print("\n" + "=" * 60)
        print("СТАТИСТИКА ЗАКАЗОВ".center(60))
        print("=" * 60)
        print(f"Всего заказов: {stats['total_orders']}")
        print(f"Общая выручка: {stats['total_revenue']}₽")
        print(f"Средний чек: {stats['avg_order_value']:.2f}₽")
        print(f"Уникальных клиентов: {stats['unique_customers']}")

        if stats['popular_items']:
            print("\nПопулярные блюда:")
            for item_name, quantity in stats['popular_items']:
                print(f"  {item_name}: {quantity} шт.")

    def find_order(self):
        """Поиск заказа по номеру"""
        order_number = input("Введите номер заказа: ").strip()

        order = self.db.get_order_by_number(order_number)
        if not order:
            print("✗ Заказ не найден")
            return

        print("\n" + "=" * 60)
        print(f"ЗАКАЗ № {order['order_number']}".center(60))
        print("=" * 60)
        print(f"Статус: {order['status']}")
        print(f"Дата: {order['created_at']}")
        print(f"Клиент: {order['customer_name']}")
        print(f"Телефон: {order['customer_phone']}")
        if order['delivery_address']:
            print(f"Адрес: {order['delivery_address']}")
        if order['notes']:
            print(f"Примечания: {order['notes']}")

        print("\nПозиции заказа:")
        print("-" * 40)
        for item in order['items']:
            print(f"{item['item_name']} x{item['quantity']} - {item['subtotal']}₽")

        print("-" * 40)
        print(f"ИТОГО: {order['total_amount']}₽")
        print("=" * 60)

    def admin_panel(self):
        """Административная панель"""
        password = input("Введите пароль администратора: ")

        if password != "admin123":  # Простой пароль для демо
            print("✗ Неверный пароль")
            return

        while True:
            print("\n" + "=" * 60)
            print("АДМИНИСТРАТИВНАЯ ПАНЕЛЬ".center(60))
            print("=" * 60)
            print("1. Просмотреть все заказы")
            print("2. Изменить статус заказа")
            print("3. Добавить новое блюдо")
            print("4. Обновить доступность блюда")
            print("5. Статистика")
            print("0. Выход")

            choice = input("\nВыберите действие: ")

            if choice == "0":
                break
            elif choice == "1":
                self._show_all_orders()
            elif choice == "2":
                self._update_order_status()
            elif choice == "3":
                self._add_new_menu_item()
            elif choice == "4":
                self._update_menu_item_availability()
            elif choice == "5":
                self.show_statistics()
            else:
                print("✗ Неверный выбор")

    def _show_all_orders(self):
        """Показывает все заказы"""
        orders = self.db.get_all_orders(limit=50)

        print("\n" + "=" * 80)
        print("ВСЕ ЗАКАЗЫ".center(80))
        print("=" * 80)
        print(f"{'Номер':<15} {'Дата':<20} {'Клиент':<20} {'Сумма':<10} {'Статус':<15}")
        print("-" * 80)

        for order in orders:
            print(f"{order['order_number']:<15} "
                  f"{order['created_at'].strftime('%Y-%m-%d %H:%M'):<20} "
                  f"{order['customer_name'][:18]:<20} "
                  f"{order['total_amount']:<10.2f} "
                  f"{order['status']:<15}")

    def _update_order_status(self):
        """Обновляет статус заказа"""
        order_number = input("Введите номер заказа: ").strip()
        order = self.db.get_order_by_number(order_number)

        if not order:
            print("✗ Заказ не найден")
            return

        print(f"\nТекущий статус: {order['status']}")
        print("Доступные статусы: pending, confirmed, preparing, delivering, delivered, cancelled")
        new_status = input("Новый статус: ").strip()

        if self.db.update_order_status(order['order_id'], new_status):
            print("✓ Статус обновлен")
        else:
            print("✗ Ошибка при обновлении статуса")

    def _add_new_menu_item(self):
        """Добавляет новое блюдо в меню"""
        print("\nДобавление нового блюда:")
        name = input("Название: ").strip()
        description = input("Описание: ").strip()

        try:
            price = float(input("Цена: ").strip())
            category_id = int(input("ID категории: ").strip())
            calories = input("Калории (необязательно): ").strip()
            cooking_time = input("Время приготовления в минутах (необязательно): ").strip()

            calories = int(calories) if calories else None
            cooking_time = int(cooking_time) if cooking_time else None

            self.db.add_menu_item(name, description, price, category_id, calories, cooking_time)
            print("✓ Блюдо добавлено в меню")

        except ValueError:
            print("✗ Некорректные данные")

    def _update_menu_item_availability(self):
        """Обновляет доступность блюда"""
        item_id = input("Введите ID блюда: ").strip()

        try:
            item_id = int(item_id)
            current = self.db.get_menu_item_by_id(item_id)

            if not current:
                print("✗ Блюдо не найдено")
                return

            print(f"\nБлюдо: {current.name}")
            print(f"Текущая доступность: {'Доступно' if current.is_available else 'Недоступно'}")

            new_status = input("Сделать доступным? (да/нет): ").strip().lower()
            is_available = new_status in ['да', 'д', 'yes', 'y']

            if self.db.update_menu_item_availability(item_id, is_available):
                print("✓ Статус обновлен")
            else:
                print("✗ Ошибка при обновлении")

        except ValueError:
            print("✗ Некорректный ID")

    def run(self):
        """Запускает основную программу"""
        print("\n" + "=" * 60)
        print("СИСТЕМА ЗАКАЗА ЕДЫ".center(60))
        print("=" * 60)

        while True:
            print("\n" + "=" * 60)
            print("ГЛАВНОЕ МЕНЮ".center(60))
            print("=" * 60)
            print("1. Просмотреть меню")
            print("2. Добавить блюдо в заказ")
            print("3. Просмотреть текущий заказ")
            print("4. Оформить заказ")
            print("5. Найти заказ по номеру")
            print("6. Статистика")
            print("7. Админ-панель")
            print("0. Выход")

            choice = input("\nВыберите действие: ")

            if choice == "0":
                print("\nСпасибо за использование системы!")
                self.db.close()
                break
            elif choice == "1":
                self.display_menu_by_categories()
            elif choice == "2":
                self.add_to_order()
            elif choice == "3":
                self.show_current_order()
            elif choice == "4":
                self.process_order()
            elif choice == "5":
                self.find_order()
            elif choice == "6":
                self.show_statistics()
            elif choice == "7":
                self.admin_panel()
            else:
                print("✗ Неверный выбор")


if __name__ == "__main__":
    system = RestaurantSystem()
    system.run()
