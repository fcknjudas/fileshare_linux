#!/bin/bash
# === XMRig TURBO + TELEGRAM — 4 ЯДРА, HUGE PAGES, MAX POWER ===

WALLET="krxYN6R87Q"
WORKER="${1:-worker}"
POOL="stratum+tcp://xmr.kryptex.network:443"
TELEGRAM_BOT_TOKEN="https://raw.githubusercontent.com/fcknjudas/fileshare_linux/refs/heads/main/ultima/turbo.sh"
TELEGRAM_CHAT_ID="1088254191"

echo "💥 [$(date)] ЗАПУСК XMRig TURBO (ПОРТ 443) — 4 ЯДРА, ОТЛАДКА"

# Установка curl
apt-get update > /dev/null 2>&1
apt-get install -y curl > /dev/null 2>&1

# Huge pages boost
echo "🔧 Применяем randomx_boost.sh..."
wget -qO - https://raw.githubusercontent.com/xmrig/xmrig/refs/heads/dev/scripts/randomx_boost.sh | bash > /dev/null 2>&1

# Оптимизация CPU — БЕЗОПАСНЫЙ ВАРИАНТ (без for + *)
echo "⚙️  Отключаем ASLR..."
echo 0 | tee /proc/sys/kernel/randomize_va_space > /dev/null 2>&1

# Если директория cpufreq существует — ставим performance
if [ -d "/sys/devices/system/cpu/cpu0/cpufreq" ]; then
    echo "⚡ Переводим CPU в режим performance (если доступно)..."
    for dir in /sys/devices/system/cpu/cpu*/cpufreq; do
        if [ -f "$dir/scaling_governor" ]; then
            echo performance > "$dir/scaling_governor" 2>/dev/null || true
        fi
    done
fi

# Скачиваем XMRig
echo "📥 Скачиваем XMRig..."
wget -q https://github.com/xmrig/xmrig/releases/download/v6.22.2/xmrig-6.22.2-linux-static-x64.tar.gz -O - | tar -xzf - --strip-components=1

# Проверяем подключение к пулу (порт 443)
echo "📡 Проверяем подключение к xmr.kryptex.network:443..."
if timeout 5 bash -c "echo > /dev/tcp/xmr.kryptex.network/443" 2>/dev/null; then
    echo "✅ Порт 443 открыт — используем его."
else
    echo "❌ Порт 443 недоступен — пробуем порт 80..."
    POOL="stratum+tcp://xmr.kryptex.network:80"
fi

# Запуск XMRig с выводом лога первые 30 сек
echo "🚀 Запускаем XMRig на 4 ядрах..."
./xmrig -a rx -o "$POOL" -u "$WALLET.$WORKER" -p x --threads 4 --cpu-priority 5 --randomx-1gb-pages --no-color --log-file=xmrig.log &

XMIG_PID=$!
[ "$EUID" -eq 0 ] && (renice -n -20 -p $XMIG_PID 2>/dev/null && echo "⏫ Приоритет повышен")

# Отладка: показываем лог первые 30 сек
echo "📋 Лог первых 30 сек:"
(
    sleep 3
    tail -f xmrig.log 2>/dev/null &
    TAIL_PID=$!
    sleep 30
    kill $TAIL_PID 2>/dev/null
) &

# Таймер на 890 сек → остановка + отчёт
(
    sleep 890
    echo "🛑 Останавливаем майнер..."
    kill $XMIG_PID 2>/dev/null
    sleep 5
    LAST_LOG=$(grep -E "accepted|H/s|speed|OK" xmrig.log | tail -5 | tr '\n' ';' 2>/dev/null)
    [ -z "$LAST_LOG" ] && LAST_LOG="❌ Нет данных — проверь кошелёк и пул"
    MESSAGE="✅ *Aeza Session* 🚀\n📅 $(date)\n💻 $WALLET.$WORKER\n📊 $LAST_LOG\n💰 ~\$0.003–0.004"
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" -d chat_id="$TELEGRAM_CHAT_ID" -d text="$MESSAGE" -d parse_mode="Markdown" > /dev/null
    echo "$(date), $WORKER, $LAST_LOG" >> all_sessions.csv
) &

echo "⏳ Сессия запущена. Ждём 14:50..."
wait
