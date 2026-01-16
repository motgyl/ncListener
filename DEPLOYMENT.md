# Server Deployment Guide

Инструкция по запуску сервера 24/7 на Linux сервере.

## Шаг 1: Подготовка

### 1.1 Создайте пользователя для сервера
```bash
sudo useradd -r -s /bin/false memo
```

### 1.2 Скопируйте файлы на сервер
```bash
sudo mkdir -p /opt/serv_mess
sudo cp -r /path/to/serv_mess/* /opt/serv_mess/
sudo chown -R memo:memo /opt/serv_mess
sudo chmod 755 /opt/serv_mess
```

### 1.3 Создайте директории для логов и файлов
```bash
sudo mkdir -p /opt/serv_mess/logs
sudo mkdir -p /opt/serv_mess/shared_files
sudo chown -R memo:memo /opt/serv_mess/logs
sudo chown -R memo:memo /opt/serv_mess/shared_files
```

## Шаг 2: Установка systemd сервиса

### 2.1 Копируем service файл
```bash
sudo cp serv_mess.service /etc/systemd/system/
```

### 2.2 Обновляем systemd
```bash
sudo systemctl daemon-reload
```

### 2.3 Запускаем сервис
```bash
sudo systemctl start serv_mess
```

### 2.4 Включаем автозапуск при загрузке
```bash
sudo systemctl enable serv_mess
```

## Шаг 3: Проверка работы

### Проверить статус
```bash
sudo systemctl status serv_mess
```

### Посмотреть логи в реальном времени
```bash
sudo tail -f /opt/serv_mess/logs/server.log
```

### Подключиться к серверу для тестирования
```bash
nc localhost 7002
```

## Полезные команды

### Перезагрузить сервис
```bash
sudo systemctl restart serv_mess
```

### Остановить сервис
```bash
sudo systemctl stop serv_mess
```

### Посмотреть последние 100 строк логов
```bash
sudo tail -100 /opt/serv_mess/logs/server.log
```

### Посмотреть логи за последний час
```bash
sudo tail -f /opt/serv_mess/logs/server.log | grep "$(date '+%H')"
```

### Посмотреть все ошибки в логах
```bash
sudo grep ERROR /opt/serv_mess/logs/server.log
```

### Посмотреть активность всех пользователей
```bash
sudo grep -E "logged in|logged out|posted" /opt/serv_mess/logs/server.log
```

### Посмотреть все загрузки файлов
```bash
sudo grep "uploaded" /opt/serv_mess/logs/server.log
```

## Системные требования

- Python 3.6+
- Linux система с systemd
- 1 GB RAM (минимум)
- Стабильное интернет соединение

## Структура файлов на сервере

```
/opt/serv_mess/
├── server.py              # Основной серверный скрипт
├── client.py              # Клиент для загрузки/скачивания файлов
├── messages.json          # Хранилище всех сообщений (персистентное)
├── logs/
│   └── server.log        # Логи сервера (постоянно растет)
└── shared_files/         # Директория с загруженными файлами
    ├── file1.pdf
    ├── file2.txt
    └── ...
```

## Управление логами

### Очистить логи
```bash
sudo sh -c 'echo "" > /opt/serv_mess/logs/server.log'
```

### Архивировать логи
```bash
sudo tar czf /opt/serv_mess/logs/server.log.$(date +%Y%m%d_%H%M%S).tar.gz /opt/serv_mess/logs/server.log
sudo sh -c 'echo "" > /opt/serv_mess/logs/server.log'
```

### Ротация логов (автоматическая)
Создайте файл `/etc/logrotate.d/serv_mess`:
```bash
sudo cat > /etc/logrotate.d/serv_mess << EOF
/opt/serv_mess/logs/server.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 memo memo
    postrotate
        systemctl reload serv_mess > /dev/null 2>&1 || true
    endscript
}
EOF
```

## Мониторинг

### Проверить, слушает ли порт 7002
```bash
sudo netstat -tlnp | grep 7002
```

или
```bash
sudo ss -tlnp | grep 7002
```

### Посмотреть количество активных подключений
```bash
sudo netstat -tn | grep 7002 | wc -l
```

### Мониторить в реальном времени
```bash
watch -n 5 'tail -20 /opt/serv_mess/logs/server.log'
```

## Решение проблем

### Если сервис не запускается
```bash
sudo systemctl status serv_mess -l
sudo journalctl -u serv_mess -n 50
```

### Если порт уже занят
```bash
sudo lsof -i :7002
# Или убить процесс
sudo kill -9 <PID>
```

### Если нет прав доступа к файлам
```bash
sudo chown -R memo:memo /opt/serv_mess
sudo chmod -R 755 /opt/serv_mess
```

## Обновление сервера

### Остановить сервис
```bash
sudo systemctl stop serv_mess
```

### Обновить файлы
```bash
sudo cp server.py /opt/serv_mess/
sudo cp client.py /opt/serv_mess/
```

### Запустить сервис
```bash
sudo systemctl start serv_mess
```

### Проверить статус
```bash
sudo systemctl status serv_mess
```
