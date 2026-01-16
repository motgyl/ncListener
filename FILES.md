# Project Files Overview

## Основные файлы приложения

### server.py
Основной серверный скрипт. Запускает TCP сервер на порту 7002.

**Особенности:**
- Многопоточная архитектура (каждый клиент в отдельном потоке)
- Полное логирование в файл и консоль
- Поддержка загрузки/скачивания файлов (base64)
- Персистентное хранилище сообщений (JSON)
- Директория для общих файлов

**Запуск:**
```bash
python3 server.py
```

### client.py
Клиент для удобной загрузки/скачивания файлов.

**Использование:**
```bash
python3 client.py upload localhost:7002 file.txt
python3 client.py download localhost:7002 file.txt
```

## Скрипты установки и управления

### install.sh
Автоматический скрипт установки (требует sudo).

**Что делает:**
- Создает пользователя `memo`
- Копирует файлы в `/opt/serv_mess`
- Устанавливает systemd сервис
- Запускает сервер

**Запуск:**
```bash
sudo bash install.sh
```

### manage.sh
Утилита управления сервисом.

**Команды:**
```bash
./manage.sh start      # Запустить
./manage.sh stop       # Остановить
./manage.sh restart    # Перезагрузить
./manage.sh status     # Статус
./manage.sh logs       # Логи
./manage.sh logs -f    # Следить за логами
./manage.sh info       # Информация
```

### logs.sh
Специализированный просмотр логов.

**Команды:**
```bash
./logs.sh follow      # Следить за логами
./logs.sh errors      # Только ошибки
./logs.sh users       # Активность пользователей
./logs.sh files       # Передачи файлов
./logs.sh stats       # Статистика
```

## Systemd сервис

### serv_mess.service
Конфигурация systemd сервиса. 

**Устанавливается в:** `/etc/systemd/system/serv_mess.service`

**Особенности:**
- Автозапуск при загрузке системы
- Автоматический перезапуск при падении
- Логирование в файл
- Изоляция и ограничения для безопасности

## Документация

### README.md
Основная документация проекта.

**Содержит:**
- Описание проекта
- Установка и запуск
- Список команд
- Примеры использования
- Информация о передаче файлов

### SETUP.md (этот файл)
Краткий обзор всех компонентов и быстрый старт.

### DEPLOYMENT.md
Подробная инструкция по развертыванию на Linux сервере.

**Включает:**
- Пошаговая установка
- Systemd сервис
- Управление логами
- Мониторинг
- Решение проблем

### QUICKSTART.md
Быстрый гайд для продакшена.

**Включает:**
- Одна-команда установка
- Типичные операции
- Мониторинг
- Ротация логов

## Файлы данных (создаются при работе)

### messages.json
JSON файл со всеми сообщениями.

**Формат:**
```json
[
  {
    "from": "alice",
    "text": "Hello everyone!",
    "time": "2026-01-16 14:23:45"
  },
  ...
]
```

### logs/server.log
Все логи сервера (автоматически создается).

**Примеры записей:**
```
[2026-01-16 14:23:45] [INFO] Server started on 0.0.0.0:7002
[2026-01-16 14:24:00] [INFO] User 'alice' logged in from 192.168.1.100
[2026-01-16 14:25:15] [INFO] User 'alice' posted message
```

### shared_files/
Директория с файлами, загруженными пользователями.

## Использование

### Локальная разработка/тестирование
```bash
python3 server.py
# В другом терминале:
nc localhost 7002
```

### Продакшн на Linux сервере
```bash
# Установка (один раз)
sudo bash install.sh

# Управление
./manage.sh status      # Проверить статус
./manage.sh logs -f     # Смотреть логи
./manage.sh restart     # Перезагрузить
```

## Структура на сервере после установки

```
/opt/serv_mess/
├── server.py
├── client.py
├── manage.sh
├── logs.sh
├── serv_mess.service
├── README.md
├── DEPLOYMENT.md
├── QUICKSTART.md
├── logs/
│   └── server.log              (растет со временем)
├── messages.json               (все сообщения)
└── shared_files/               (загруженные файлы)

/etc/systemd/system/
└── serv_mess.service           (скопировано install.sh)
```

## Команды systemd

```bash
# Проверить статус
sudo systemctl status serv_mess

# Запустить
sudo systemctl start serv_mess

# Остановить
sudo systemctl stop serv_mess

# Перезагрузить
sudo systemctl restart serv_mess

# Включить автозапуск
sudo systemctl enable serv_mess

# Отключить автозапуск
sudo systemctl disable serv_mess

# Просмотр логов journalctl
sudo journalctl -u serv_mess -n 100

# Следить за логами journalctl
sudo journalctl -u serv_mess -f
```

## Полезные команды

```bash
# Просмотр логов сервера
tail -f /opt/serv_mess/logs/server.log

# Просмотр ошибок
grep ERROR /opt/serv_mess/logs/server.log

# Просмотр активности пользователей
grep "logged in\|posted" /opt/serv_mess/logs/server.log

# Размер логов
du -h /opt/serv_mess/logs/server.log

# Количество сообщений
wc -l /opt/serv_mess/messages.json

# Активные подключения
sudo netstat -tn | grep :7002

# Процесс сервера
ps aux | grep server.py
```

## Устранение неполадок

### Сервис не запускается
```bash
sudo systemctl status serv_mess -l
sudo journalctl -u serv_mess -n 50
```

### Порт занят
```bash
sudo lsof -i :7002
sudo kill -9 <PID>
```

### Нет прав доступа
```bash
sudo chown -R memo:memo /opt/serv_mess
sudo chmod -R 755 /opt/serv_mess
```

### Размер логов слишком большой
```bash
# Очистить логи
sudo sh -c 'echo "" > /opt/serv_mess/logs/server.log'

# Или архивировать
sudo tar czf /opt/serv_mess/logs/server.log.backup.tar.gz \
  /opt/serv_mess/logs/server.log
```

## Версия и зависимости

- **Python:** 3.6+
- **ОС:** Linux (для systemd)
- **Зависимости:** Стандартная библиотека Python (socket, threading, json, logging и т.д.)

## Автор и лицензия

Проект создан для личного использования.
Вольны использовать и модифицировать как угодно.
