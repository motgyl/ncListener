# Production Deployment Quick Start

## Один-команда установка на сервер

```bash
sudo bash install.sh
```

Это автоматически:
- Создаст пользователя `memo`
- Установит все файлы в `/opt/serv_mess`
- Настроит systemd сервис
- Запустит сервер
- Включит автозапуск при загрузке

## После установки

### Проверить статус
```bash
systemctl status serv_mess
```

### Смотреть логи в реальном времени
```bash
tail -f /opt/serv_mess/logs/server.log
```

### Или использовать скрипт для логов
```bash
chmod +x /opt/serv_mess/logs.sh
/opt/serv_mess/logs.sh follow    # Следить за логами
/opt/serv_mess/logs.sh stats     # Статистика
/opt/serv_mess/logs.sh errors    # Только ошибки
```

### Подключиться к серверу (тестирование)
```bash
nc localhost 7002
login testuser
help
```

## Типичные операции

### Перезагрузить сервис после обновлений
```bash
sudo systemctl restart serv_mess
```

### Остановить сервис
```bash
sudo systemctl stop serv_mess
```

### Посмотреть ошибки
```bash
sudo grep ERROR /opt/serv_mess/logs/server.log | tail
```

### Посмотреть активность пользователей
```bash
sudo grep "logged in\|posted message" /opt/serv_mess/logs/server.log | tail -20
```

### Проверить, используется ли порт 7002
```bash
sudo netstat -tlnp | grep 7002
```

## Структура файлов после установки

```
/opt/serv_mess/
├── server.py              ← Основной сервер
├── client.py              ← Клиент для файлов
├── logs/
│   └── server.log        ← Логи (постоянно растут)
├── messages.json          ← Все сообщения
├── shared_files/         ← Загруженные файлы
└── README.md
```

## Мониторинг

### Простая проверка (раз в 5 сек)
```bash
watch -n 5 'systemctl status serv_mess | head -20'
```

### Посчитать активных пользователей
```bash
sudo netstat -tn | grep :7002 | wc -l
```

### Размер файла логов
```bash
du -h /opt/serv_mess/logs/server.log
```

## Решение проблем

### Сервис не запускается
```bash
sudo systemctl status serv_mess -l
sudo journalctl -u serv_mess -n 100
```

### Порт уже занят
```bash
sudo lsof -i :7002
sudo kill -9 <PID>
```

### Нет доступа к файлам
```bash
sudo chown -R memo:memo /opt/serv_mess
sudo chmod -R 755 /opt/serv_mess
```

## Ротация логов (опционально)

Чтобы логи не занимали место, создайте `/etc/logrotate.d/serv_mess`:

```bash
sudo cat > /etc/logrotate.d/serv_mess << 'EOF'
/opt/serv_mess/logs/server.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
}
EOF
```

После этого старые логи будут автоматически сжиматься и удаляться через 30 дней.

## Полная документация

Подробная инструкция см. в [DEPLOYMENT.md](DEPLOYMENT.md)
