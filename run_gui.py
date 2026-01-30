"""
run_gui.py
Простой скрипт для запуска GUI приложения
"""

import sys
import os

# Добавляем текущую директорию в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from restaurant_gui import main
    print("Запуск ресторана...")
    main()
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что установлены все зависимости:")
    print("pip install -r requirements.txt")
except Exception as e:
    print(f"Ошибка запуска: {e}")
