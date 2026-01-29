-- setup_database.sql
-- Скрипт для создания и настройки базы данных

-- 1. Создайте базу данных (выполните в psql или pgAdmin):
CREATE DATABASE restaurant_db;

-- 2. Подключитесь к базе restaurant_db и выполните:

-- Создание таблиц (это делает автоматически код Python)
-- Этот файл может быть полезен для ручной настройки или резервного копирования

-- Просмотр структуры базы данных:
SELECT
    table_name,
    column_name,
    data_type
FROM
    information_schema.columns
WHERE
    table_schema = 'public'
ORDER BY
    table_name,
    ordinal_position;