from food_order import Restaurant
import os


def main() -> None:
    """Основная функция программы"""
    print("\n" + "=" * 60)
    print("СИСТЕМА ЗАКАЗА ЕДЫ".center(60))
    print("=" * 60)

    # Создаем ресторан
    restaurant = Restaurant("Вкусно и Точка")

    # Основной цикл программы
    while True:
        print("\n" + "=" * 60)
        print("ГЛАВНОЕ МЕНЮ".center(60))
        print("=" * 60)
        print("1. Сделать заказ")
        print("2. Просмотреть меню")
        print("3. Статистика заказов")
        print("4. Показать папку с заказами")
        print("0. Выход")

        choice = input("\nВыберите действие: ")

        if choice == "1":
            continue_ordering = restaurant.process_order()
            if not continue_ordering:
                break

        elif choice == "2":
            restaurant.display_menu()

        elif choice == "3":
            restaurant.show_statistics()

        elif choice == "4":
            orders_dir = "orders"
            if os.path.exists(orders_dir):
                order_files = [f for f in os.listdir(orders_dir) if f.endswith('.json')]
                print(f"\nПапка '{orders_dir}/' содержит {len(order_files)} заказов:")
                for file in sorted(order_files)[:10]:  # Показываем первые 10
                    print(f"  - {file}")
                if len(order_files) > 10:
                    print(f"  ... и еще {len(order_files) - 10} файлов")
            else:
                print(f"\nПапка '{orders_dir}/' не существует.")

        elif choice == "0":
            print("\n" + "=" * 60)
            print("Спасибо за использование системы!".center(60))
            print("До свидания!".center(60))
            print("=" * 60)
            break

        else:
            print("\n✗ Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()
