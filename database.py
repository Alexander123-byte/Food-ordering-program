"""
database.py
Модуль для работы с PostgreSQL базой данных ресторана - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""

import psycopg2
from psycopg2.extensions import connection as PgConnection
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid

# Загружаем переменные окружения
load_dotenv()

class PostgreSQLDatabase:
    """Класс для работы с PostgreSQL"""

    def __init__(self):
        self.connection: Optional[PgConnection] = None
        self._connect()
        self._initialize_tables()
        self._seed_initial_data()

    def _connect(self) -> None:
        """Устанавливает соединение с PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                dbname=os.getenv("DB_NAME", "restaurant_db"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "rewty76"),
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432")
            )
            self.connection.autocommit = False
            print("✓ Подключение к PostgreSQL установлено")
        except Exception as e:
            print(f"✗ Ошибка подключения к PostgreSQL: {e}")
            raise

    def _initialize_tables(self) -> None:
        """Инициализирует таблицы если их нет"""
        try:
            with self.connection.cursor() as cursor:
                # Таблица категорий
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS categories (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица меню - ДОБАВЛЕНО ПОЛЕ ДЛЯ ПРИЧИНЫ
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS menu_items (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        description TEXT,
                        price DECIMAL(10, 2) NOT NULL,
                        category_id INTEGER REFERENCES categories(id),
                        is_available BOOLEAN DEFAULT TRUE,
                        unavailability_reason TEXT,
                        calories INTEGER,
                        cooking_time_minutes INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица клиентов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS customers (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        phone VARCHAR(20) UNIQUE,
                        email VARCHAR(200),
                        address TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица заказов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS orders (
                        id SERIAL PRIMARY KEY,
                        order_number VARCHAR(50) UNIQUE NOT NULL,
                        customer_id INTEGER REFERENCES customers(id),
                        total_amount DECIMAL(10, 2) NOT NULL,
                        status VARCHAR(50) DEFAULT 'pending',
                        payment_method VARCHAR(50),
                        delivery_address TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица позиций заказа
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS order_items (
                        id SERIAL PRIMARY KEY,
                        order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                        menu_item_id INTEGER REFERENCES menu_items(id),
                        quantity INTEGER NOT NULL CHECK (quantity > 0),
                        price_at_order DECIMAL(10, 2) NOT NULL,
                        subtotal DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * price_at_order) STORED,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                self.connection.commit()
                print("✓ Таблицы инициализированы")
        except Exception as e:
            self.connection.rollback()
            print(f"✗ Ошибка при инициализации таблиц: {e}")
            raise

    def _seed_initial_data(self) -> None:
        """Заполняет начальными данными если таблицы пустые"""
        try:
            with self.connection.cursor() as cursor:
                # Проверяем, есть ли категории
                cursor.execute("SELECT COUNT(*) FROM categories")
                count = cursor.fetchone()[0]

                if count == 0:
                    print("✓ Добавляем начальные данные...")

                    # Добавляем категории
                    categories = [
                        ("Пицца", "Итальянская пицца на тонком тесте"),
                        ("Суши и роллы", "Японская кухня"),
                        ("Напитки", "Холодные и горячие напитки"),
                        ("Десерты", "Сладкие угощения")
                    ]

                    for name, description in categories:
                        cursor.execute(
                            "INSERT INTO categories (name, description) VALUES (%s, %s)",
                            (name, description)
                        )

                    # Добавляем меню
                    menu_items = [
                        ("Маргарита", "Томатный соус, моцарелла, базилик", 450, 1, 800, 15),
                        ("Пепперони", "Томатный соус, пепперони, моцарелла", 550, 1, 950, 20),
                        ("Филадельфия", "Лосось, сливочный сыр, огурец", 320, 2, 420, 10),
                        ("Калифорния", "Краб-микс, авокадо, огурец, икра", 280, 2, 380, 10),
                        ("Кола", "Coca-Cola 0.5л", 120, 3, 210, 2),
                        ("Апельсиновый сок", "Свежевыжатый сок 0.3л", 150, 3, 120, 3),
                        ("Чизкейк", "Классический Нью-Йорк чизкейк", 200, 4, 350, 5),
                        ("Тирамису", "Итальянский десерт", 250, 4, 280, 5)
                    ]

                    for name, description, price, category_id, calories, cooking_time in menu_items:
                        cursor.execute(
                            """INSERT INTO menu_items 
                            (name, description, price, category_id, calories, cooking_time_minutes) 
                            VALUES (%s, %s, %s, %s, %s, %s)""",
                            (name, description, price, category_id, calories, cooking_time)
                        )

                    self.connection.commit()
                    print("✓ Начальные данные добавлены")
        except Exception as e:
            self.connection.rollback()
            print(f"⚠ Ошибка при добавлении начальных данных: {e}")

    def get_all_categories(self) -> List[Any]:
        """Получает все категории"""
        from models import Category

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT id, name, description FROM categories ORDER BY name")
                return [Category(id=row[0], name=row[1], description=row[2])
                        for row in cursor.fetchall()]
        except Exception as e:
            print(f"✗ Ошибка при получении категорий: {e}")
            return []

    def get_menu_items(self, category_id: Optional[int] = None,
                      available_only: bool = False) -> List[Any]:
        """Получает блюда из меню (по умолчанию ВСЕ блюда)"""
        from models import MenuItem

        try:
            query = """
                SELECT m.id, m.name, m.description, m.price, m.category_id, 
                       m.is_available, m.unavailability_reason, m.calories, m.cooking_time_minutes,
                       c.name as category_name
                FROM menu_items m
                JOIN categories c ON m.category_id = c.id
            """
            params = []

            if available_only:  # Только если явно запрошено
                query += " WHERE m.is_available = TRUE"

            if category_id:
                if available_only:
                    query += " AND m.category_id = %s"
                else:
                    if "WHERE" in query:
                        query += " AND m.category_id = %s"
                    else:
                        query += " WHERE m.category_id = %s"
                params.append(category_id)

            query += " ORDER BY c.name, m.name"

            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return [MenuItem(
                    id=row[0], name=row[1], description=row[2], price=float(row[3]),
                    category_id=row[4], category_name=row[8], is_available=row[5],
                    unavailability_reason=row[6], calories=row[7], cooking_time=row[8]
                ) for row in cursor.fetchall()]
        except Exception as e:
            print(f"✗ Ошибка при получении блюд: {e}")
            return []

    def get_menu_item_by_id(self, item_id: int) -> Optional[Any]:
        """Получает блюдо по ID"""
        from models import MenuItem

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT m.id, m.name, m.description, m.price, m.category_id,
                           m.is_available, m.unavailability_reason, m.calories, m.cooking_time_minutes,
                           c.name as category_name
                    FROM menu_items m
                    JOIN categories c ON m.category_id = c.id
                    WHERE m.id = %s
                """, (item_id,))
                row = cursor.fetchone()

                if row:
                    return MenuItem(
                        id=row[0], name=row[1], description=row[2], price=float(row[3]),
                        category_id=row[4], category_name=row[8], is_available=row[5],
                        unavailability_reason=row[6], calories=row[7], cooking_time=row[8]
                    )
                return None
        except Exception as e:
            print(f"✗ Ошибка при получении блюда по ID: {e}")
            return None

    def find_or_create_customer(self, name: str, phone: str,
                               email: str = "", address: str = "") -> Any:
        """Находит существующего клиента или создает нового"""
        from models import Customer

        try:
            with self.connection.cursor() as cursor:
                # Пытаемся найти по телефону
                cursor.execute(
                    "SELECT id, name, phone, email, address FROM customers WHERE phone = %s",
                    (phone,)
                )
                row = cursor.fetchone()

                if row:
                    return Customer(
                        id=row[0], name=row[1], phone=row[2], email=row[3], address=row[4]
                    )

                # Создаем нового клиента
                cursor.execute("""
                    INSERT INTO customers (name, phone, email, address)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, name, phone, email, address
                """, (name, phone, email, address))

                row = cursor.fetchone()
                self.connection.commit()

                return Customer(
                    id=row[0], name=row[1], phone=row[2], email=row[3], address=row[4]
                )
        except Exception as e:
            self.connection.rollback()
            print(f"✗ Ошибка при поиске/создании клиента: {e}")
            raise

    def create_order(self, customer_id: int, items: List[Any],
                    delivery_address: str = "", notes: str = "",
                    payment_method: str = "cash") -> Tuple[int, str]:
        """Создает новый заказ в базе данных"""
        try:
            with self.connection.cursor() as cursor:
                # Генерируем номер заказа
                order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

                # Рассчитываем общую сумму
                total_amount = sum(item.subtotal for item in items)

                # Создаем заказ
                cursor.execute("""
                    INSERT INTO orders 
                    (order_number, customer_id, total_amount, delivery_address, notes, payment_method)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (order_number, customer_id, total_amount, delivery_address, notes, payment_method))

                order_id = cursor.fetchone()[0]

                # Добавляем позиции заказа
                for item in items:
                    cursor.execute("""
                        INSERT INTO order_items 
                        (order_id, menu_item_id, quantity, price_at_order)
                        VALUES (%s, %s, %s, %s)
                    """, (order_id, item.menu_item_id, item.quantity, item.price_at_order))

                self.connection.commit()
                print(f"✓ Заказ создан: {order_number}")
                return order_id, order_number

        except Exception as e:
            self.connection.rollback()
            print(f"✗ Ошибка при создании заказа: {e}")
            raise

    def get_order_by_number(self, order_number: str) -> Optional[Dict[str, Any]]:
        """Получает детали заказа по номеру"""
        try:
            with self.connection.cursor() as cursor:
                # Получаем основную информацию о заказе
                cursor.execute("""
                    SELECT o.id, o.order_number, o.total_amount, o.status, o.created_at,
                           c.name as customer_name, c.phone, c.email,
                           o.delivery_address, o.notes, o.payment_method
                    FROM orders o
                    JOIN customers c ON o.customer_id = c.id
                    WHERE o.order_number = %s
                """, (order_number,))

                order_row = cursor.fetchone()
                if not order_row:
                    return None

                # Получаем позиции заказа
                cursor.execute("""
                    SELECT oi.menu_item_id, oi.quantity, oi.price_at_order, oi.subtotal,
                           m.name as item_name
                    FROM order_items oi
                    JOIN menu_items m ON oi.menu_item_id = m.id
                    WHERE oi.order_id = %s
                    ORDER BY oi.id
                """, (order_row[0],))

                items = []
                for row in cursor.fetchall():
                    items.append({
                        'item_id': row[0],
                        'item_name': row[4],
                        'quantity': row[1],
                        'price': float(row[2]),
                        'subtotal': float(row[3])
                    })

                return {
                    'order_id': order_row[0],
                    'order_number': order_row[1],
                    'total_amount': float(order_row[2]),
                    'status': order_row[3],
                    'created_at': order_row[4],
                    'customer_name': order_row[5],
                    'customer_phone': order_row[6],
                    'customer_email': order_row[7],
                    'delivery_address': order_row[8],
                    'notes': order_row[9],
                    'payment_method': order_row[10],
                    'items': items
                }
        except Exception as e:
            print(f"✗ Ошибка при получении заказа: {e}")
            return None

    def get_all_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает все заказы"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT o.order_number, o.created_at, o.total_amount, o.status,
                           c.name as customer_name
                    FROM orders o
                    JOIN customers c ON o.customer_id = c.id
                    ORDER BY o.created_at DESC
                    LIMIT %s
                """, (limit,))

                orders = []
                for row in cursor.fetchall():
                    orders.append({
                        'order_number': row[0],
                        'created_at': row[1],
                        'total_amount': float(row[2]),
                        'status': row[3],
                        'customer_name': row[4]
                    })

                return orders
        except Exception as e:
            print(f"✗ Ошибка при получении всех заказов: {e}")
            # Пытаемся восстановить соединение
            self._reconnect()
            return []

    def _reconnect(self):
        """Переподключается к базе данных в случае ошибки"""
        try:
            if self.connection:
                self.connection.close()
            self._connect()
            print("✓ Соединение с PostgreSQL восстановлено")
        except Exception as e:
            print(f"✗ Не удалось восстановить соединение: {e}")

    def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновляет статус заказа"""
        allowed_statuses = ['pending', 'confirmed', 'preparing', 'delivering', 'delivered', 'cancelled']

        if status not in allowed_statuses:
            print(f"✗ Неверный статус. Допустимые: {', '.join(allowed_statuses)}")
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE orders SET status = %s WHERE id = %s",
                    (status, order_id)
                )
                self.connection.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            print(f"✗ Ошибка при обновлении статуса: {e}")
            return False

    def add_menu_item(self, name: str, description: str, price: float,
                     category_id: int, calories: Optional[int] = None,
                     cooking_time: Optional[int] = None) -> bool:
        """Добавляет новое блюдо в меню"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO menu_items 
                    (name, description, price, category_id, calories, cooking_time_minutes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, description, price, category_id, calories, cooking_time))

                self.connection.commit()
                return True
        except Exception as e:
            self.connection.rollback()
            print(f"✗ Ошибка при добавлении блюда: {e}")
            return False

    def update_menu_item_availability(self, item_id: int, is_available: bool,
                                    unavailability_reason: Optional[str] = None) -> bool:
        """Обновляет доступность блюда с указанием причины"""
        try:
            with self.connection.cursor() as cursor:
                if is_available:
                    # Если блюдо становится доступным, очищаем причину
                    cursor.execute(
                        "UPDATE menu_items SET is_available = TRUE, unavailability_reason = NULL WHERE id = %s",
                        (item_id,)
                    )
                else:
                    # Если блюдо становится недоступным, сохраняем причину
                    cursor.execute(
                        "UPDATE menu_items SET is_available = FALSE, unavailability_reason = %s WHERE id = %s",
                        (unavailability_reason, item_id)
                    )

                self.connection.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            print(f"✗ Ошибка при обновлении блюда: {e}")
            return False

    def get_order_statistics(self, start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> Dict[str, Any]:
        """Получает статистику по заказам"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_orders,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as avg_order_value,
                    COUNT(DISTINCT customer_id) as unique_customers
                FROM orders
                WHERE status != 'cancelled'
            """
            params = []

            if start_date:
                query += " AND created_at >= %s"
                params.append(start_date)

            if end_date:
                query += " AND created_at <= %s"
                params.append(end_date)

            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()

                # Популярные блюда
                cursor.execute("""
                    SELECT m.name, SUM(oi.quantity) as total_quantity
                    FROM order_items oi
                    JOIN menu_items m ON oi.menu_item_id = m.id
                    JOIN orders o ON oi.order_id = o.id
                    WHERE o.status != 'cancelled'
                    GROUP BY m.name
                    ORDER BY total_quantity DESC
                    LIMIT 10
                """)
                popular_items = [(row[0], row[1]) for row in cursor.fetchall()]

                return {
                    'total_orders': row[0] or 0,
                    'total_revenue': float(row[1] or 0),
                    'avg_order_value': float(row[2] or 0),
                    'unique_customers': row[3] or 0,
                    'popular_items': popular_items
                }
        except Exception as e:
            print(f"✗ Ошибка при получении статистики: {e}")
            return {
                'total_orders': 0,
                'total_revenue': 0.0,
                'avg_order_value': 0.0,
                'unique_customers': 0,
                'popular_items': []
            }

    def close(self):
        """Закрывает соединение с базой данных"""
        if self.connection:
            try:
                self.connection.rollback()  # Откатываем любые незавершенные транзакции
                self.connection.close()
                print("✓ Соединение с PostgreSQL закрыто")
            except Exception as e:
                print(f"⚠ Ошибка при закрытии соединения: {e}")
