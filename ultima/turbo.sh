#!/bin/bash
# === XMRig TURBO + TELEGRAM — 4 ЯДРА, HUGE PAGES, MAX POWER ===

WALLET="krxYN6R87Q"
WORKER="${1:-worker}"
POOL="stratum+tcp://xmr.kryptex.network:443"
TELEGRAM_BOT_TOKEN="https://raw.githubusercontent.com/fcknjudas/fileshare_linux/refs/heads/main/ultima/turbo.sh"
TELEGRAM_CHAT_ID="1088254191"

echo "💥 [$(date)] ЗАПУСК XMRig TURBO (ПОРТ 443) — 4 ЯДРА, ОТЛАДКА ВКЛЮЧЕНА"

# Установка curl (если нет)
apt-get update > /dev/null 2>&1
apt-get install -y curl > /dev/null 2>&1

# Huge pages boost
echo "🔧 Применяем randomx_boost.sh..."
wget -qO - https://raw.githubusercontent.com/xmrig/xmrig/refs/heads/dev/scripts/randomx_boost.sh | bash > /dev/null 2>&1

# Оптимизация (игнорируем ошибки, если директорий нет)
echo "⚙️  Оптимизация CPU (игнорируем ошибки)..."
echo 0 | tee /proc/sys/kernel/randomize_va_space > /dev/null 2>&1
for CPU in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null; do
    echo performance > $CPU 2>/dev/null || true
done

# Скачиваем XMRig
echo "📥 Скачиваем XMRig..."
wget -q https://github.com/xmrig/xmrig/releases/download/v6.22.2/xmrig-6.22.2-linux-static-x64.tar.gz -O - | tar -xzf - --strip-components=1

# Проверяем подключение к пулу
echo "📡 Проверяем подключение к $POOL..."
timeout 5 bash -c "echo > /dev/tcp/xmr.kryptex.network/443" && echo "✅ Порт 443 открыт" || echo "❌ Порт 443 закрыт — пробуем 80..."

if ! timeout 5 bash -c "echo > /dev/tcp/xmr.kryptex.network/443"; then
    POOL="stratum+tcp://xmr.kryptex.network:80"
    echo "🔁 Переключились на порт 80"
fi

# Запуск с ОТЛАДКОЙ (выводим лог в консоль первые 30 сек)
echo "🚀 Запускаем XMRig на 4 ядрах с выводом лога..."
./xmrig -a rx -o "$POOL" -u "$WALLET.$WORKER" -p x --threads 4 --cpu-priority 5 --randomx-1gb-pages --no-color --log-file=xmrig.log &

XMIG_PID=$!
[ "$EUID" -eq 0 ] && renice -n -20 -p $XMIG_PID 2>/dev/null

# Показываем лог первые 30 сек для отладки
echo "📋 Лог первых 30 сек (ищем [OK] или ошибки):"
timeout 30 tail -f xmrig.log 2>/dev/null || echo "⚠️ Лог недоступен — проверь, запущен ли процесс: pgrep xmrig"

# Таймер 890 сек → остановка + отчёт
(
    sleep 890
    echo "🛑 Останавливаем майнер..."
    kill $XMIG_PID 2>/dev/null
    sleep 5
    LAST_LOG=$(grep -E "accepted|H/s|speed" xmrig.log | tail -5 | tr '\n' ';' 2>/dev/null)
    [ -z "$LAST_LOG" ] && LAST_LOG="❌ Нет данных — возможно, не было подключения"
    MESSAGE="✅ *Aeza Session* 🚀\n📅 $(date)\n💻 $WALLET.$WORKER\n📊 $LAST_LOG\n💰 ~\$0.003–0.004"
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" -d chat_id="$TELEGRAM_CHAT_ID" -d text="$MESSAGE" -d parse_mode="Markdown" > /dev/null
    echo "$(date), $WORKER, $LAST_LOG" >> all_sessions.csv
) &

echo "⏳ Сессия запущена. Ожидаем 14:50..."
wait
