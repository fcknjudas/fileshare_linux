#!/bin/bash
# === XMRig RandomX Miner — FULL POWER TURBO EDITION for Aeza Terminator ===
# by fcknjudas — 4 ядра, huge pages, max priority, Telegram отчёты, 14:50 таймер

# ============ НАСТРОЙКИ ============
WALLET="krxYN6R87Q"               # Замени на свой кошелёк Kryptex
WORKER="${1:-worker}"             # Имя воркера (передавай как аргумент: bash script.sh vps01)
POOL="stratum+tcp://xmr.kryptex.network:7777"

# ⚙️ Telegram уведомления (ОБЯЗАТЕЛЬНО замени на свои!)
TELEGRAM_BOT_TOKEN="8483385138:AAHc_VXgGiPDoSCdfIUAg3wVTIB-1nWi3rw"    # Создай бота через @BotFather
TELEGRAM_CHAT_ID="1088254191"        # Узнай через @userinfobot

# ===================================

echo "💥 [$(date)] ЗАПУСК XMRig TURBO — 4 ЯДРА, MAX POWER, TELEGRAM ОТЧЁТЫ"
echo "⏱️  Автостоп через 14 минут 50 секунд — выжмем всё до удаления VPS."

# === Этап 1: Установка зависимостей (если нужно) ===
apt-get update > /dev/null 2>&1
apt-get install -y psmisc curl > /dev/null 2>&1

# === Этап 2: Применяем randomx_boost.sh (huge pages) ===
echo "⚡ Применяем randomx_boost.sh для 1GB huge pages..."
wget -qO - https://raw.githubusercontent.com/xmrig/xmrig/refs/heads/dev/scripts/randomx_boost.sh | bash > /dev/null 2>&1

# Проверим, включились ли huge pages
HUGE_PAGES=$(cat /proc/meminfo | grep -i "HugePages_Total" | awk '{print $2}')
echo "🔧 Huge Pages Total: $HUGE_PAGES"

# === Этап 3: Скачиваем XMRig — напрямую, без задержек ===
echo "📥 Скачиваем XMRig v6.22.2..."
wget -q https://github.com/xmrig/xmrig/releases/download/v6.22.2/xmrig-6.22.2-linux-static-x64.tar.gz -O - | tar -xzf - --strip-components=1

# === Этап 4: Оптимизация системы под майнинг ===
echo "⚙️  Оптимизация системы..."

# Отключаем ASLR
echo 0 | tee /proc/sys/kernel/randomize_va_space > /dev/null 2>&1

# Включаем режим максимальной производительности CPU
for CPU in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null; do
    echo performance > $CPU
done

# Увеличиваем лимиты (если root)
if [ "$EUID" -eq 0 ]; then
    ulimit -n 65536
    echo "🔓 ulimit увеличен до 65536"
fi

# === Этап 5: Запуск XMRig на 4 ядрах с максимальным приоритетом ===
echo "🚀 Запускаем XMRig на 4 ядрах..."

# Запускаем в фоне с логированием
./xmrig \
    -a rx \
    -o "$POOL" \
    -u "$WALLET.$WORKER" \
    -p x \
    --threads 4 \
    --cpu-priority 5 \
    --randomx-mode auto \
    --randomx-1gb-pages \
    --no-color \
    --log-file=xmrig.log \
    > /dev/null 2>&1 &

XMIG_PID=$!

# Повышаем приоритет процесса (если root)
if [ "$EUID" -eq 0 ]; then
    renice -n -20 -p $XMIG_PID 2>/dev/null && echo "⏫ Приоритет процесса повышен до -20"
fi

echo "✅ XMRig запущен (PID: $XMIG_PID). Лог: xmrig.log"

# === Этап 6: Таймер на 890 секунд (14:50) — успеваем отправить последние шары ===
(
    sleep 890
    echo "🛑 [$(date)] ТАЙМЕР ИСТЕК — ЗАВЕРШАЕМ МАЙНЕР..."
    
    # Останавливаем майнер
    kill $XMIG_PID 2>/dev/null && echo "✅ XMRig остановлен."
    
    # Ждём 5 сек, чтобы записался лог
    sleep 5
    
    # Формируем отчёт
    echo "📈 ФОРМИРУЕМ ОТЧЁТ..."
    
    # Получаем последние строки лога
    LAST_LOG=$(tail -n 15 xmrig.log 2>/dev/null | grep -E "speed|accepted|H/s" | tail -3)
    
    # Если лог пуст — пишем заглушку
    if [ -z "$LAST_LOG" ]; then
        LAST_LOG="⚠️ Лог пуст — возможно, майнер не успел подключиться."
    fi
    
    # Формируем сообщение
    MESSAGE="✅ *Aeza VPS Session Completed* 🚀
📅 *Дата:* $(date)
💻 *Воркер:* $WALLET.$WORKER
⚡ *Пул:* xmr.kryptex.network:7777
📊 *Последние данные:*
$LAST_LOG
💰 *Оценка прибыли:* ~\$0.003–0.004"

    # Отправляем в Telegram
    echo "📲 Отправляем отчёт в Telegram..."
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d chat_id="$TELEGRAM_CHAT_ID" \
        -d text="$MESSAGE" \
        -d parse_mode="Markdown" > /dev/null
    
    echo "📤 Отчёт отправлен в Telegram."
    echo "💾 Лог сохранён в xmrig.log"
    
    # Сохраняем отчёт в файл
    echo "$MESSAGE" > session_report.txt
    
) &

# Даём майнеру 15 сек на прогрев и подключение
sleep 15

echo "⏳ Осталось 14:50... XMRig гонит на 4 ядрах на 100%. Ничего не трогай."

# Ждём завершения фонового процесса
wait

echo "🏁 СЕССИЯ ЗАВЕРШЕНА. VPS скоро удалится. Profit: ~$0.003–0.004"
