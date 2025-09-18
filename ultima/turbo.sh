#!/bin/bash
# === XMRig TURBO + TELEGRAM — 4 ЯДРА, HUGE PAGES, MAX POWER ===

WALLET="krxYN6R87Q"
WORKER="${1:-worker}"
POOL="stratum+tcp://xmr.kryptex.network:7777"
TELEGRAM_BOT_TOKEN="https://raw.githubusercontent.com/fcknjudas/fileshare_linux/refs/heads/main/ultima/turbo.sh"
TELEGRAM_CHAT_ID="1088254191"

echo "💥 [$(date)] ЗАПУСК XMRig TURBO — 4 ЯДРА, MAX POWER"

# Установка
apt-get update > /dev/null 2>&1
apt-get install -y psmisc curl > /dev/null 2>&1

# Boost
wget -qO - https://raw.githubusercontent.com/xmrig/xmrig/refs/heads/dev/scripts/randomx_boost.sh | bash > /dev/null 2>&1

# Оптимизация
echo 0 | tee /proc/sys/kernel/randomize_va_space > /dev/null 2>&1
for CPU in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance > $CPU 2>/dev/null; done
[ "$EUID" -eq 0 ] && ulimit -n 65536

# Скачиваем XMRig
wget -q https://github.com/xmrig/xmrig/releases/download/v6.22.2/xmrig-6.22.2-linux-static-x64.tar.gz -O - | tar -xzf - --strip-components=1

# Запуск
./xmrig -a rx -o "$POOL" -u "$WALLET.$WORKER" -p x --threads 4 --cpu-priority 5 --randomx-1gb-pages --no-color --log-file=xmrig.log > /dev/null 2>&1 &
XMIG_PID=$!
[ "$EUID" -eq 0 ] && renice -n -20 -p $XMIG_PID 2>/dev/null

# Таймер 890 сек
(
    sleep 890
    kill $XMIG_PID 2>/dev/null
    sleep 5
    LAST_LOG=$(tail -n 15 xmrig.log | grep -E "speed|accepted|H/s" | tail -3)
    [ -z "$LAST_LOG" ] && LAST_LOG="⚠️ Лог пуст"
    MESSAGE="✅ *Aeza Session* 🚀\n📅 $(date)\n💻 $WALLET.$WORKER\n📊 $LAST_LOG\n💰 ~\$0.003–0.004"
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" -d chat_id="$TELEGRAM_CHAT_ID" -d text="$MESSAGE" -d parse_mode="Markdown" > /dev/null
    echo "$MESSAGE" >> all_sessions.csv
) &
sleep 15
wait
