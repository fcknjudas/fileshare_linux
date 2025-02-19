#!/bin/bash

# Ваши ключи
WALLET_ADDRESS="SOL:G5MFVuQvYabm9sknjwXi9HcHVLGYnEdiQcsQ3NASP1W3"
POOL_ADDRESS="rx.unmineable.com:443"
ALGORITHM="rx"

# Путь к xmrig (если не в PATH)
XMRIG_PATH="./xmrig"  # Предполагается, что xmrig находится в текущей директории.  Измените при необходимости.

# Функция для генерации случайного имени воркера
generate_random_worker_name() {
  head /dev/urandom | tr -dc A-Za-z0-9 | head -c 16 ; echo ''
}

# Получаем случайное имя воркера
WORKER_NAME=$(generate_random_worker_name)

# Формируем строку воркера для unMineable
UNMINEABLE_WORKER="$WALLET_ADDRESS.$WORKER_NAME"

# Формируем команду для запуска XMRig
XMRIG_COMMAND="$XMRIG_PATH -a $ALGORITHM -o stratum+ssl://$POOL_ADDRESS -p x -u $UNMINEABLE_WORKER"

# Запускаем XMRig в фоне и перенаправляем вывод в файл лога (опционально)
nohup $XMRIG_COMMAND > xmrig.log 2>&1 &

echo "Запущен XMRig с воркером: $WORKER_NAME"
echo "PID процесса: $!"  # Выводит PID запущенного процесса
echo "Лог майнера: xmrig.log"
