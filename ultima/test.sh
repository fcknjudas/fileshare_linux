#!/bin/bash
# Тестирует 3 алгоритма по 3 минуты → выбирает лучший

WALLET="krxYN6R87Q"
ALGOS=("rx" "gr" "kawpow")
POOLS=("stratum+tcp://xmr.kryptex.network:7777" "stratum+tcp://ghostrider.kryptex.network:7777" "stratum+tcp://kawpow.kryptex.network:7777")
NAMES=("RandomX" "Ghostrider" "KawPow")

# Скачиваем XMRig если нет
[ ! -f xmrig ] && wget -q https://github.com/xmrig/xmrig/releases/download/v6.22.2/xmrig-6.22.2-linux-static-x64.tar.gz -O - | tar -xzf - --strip-components=1

> algo_scores.csv

test_algo() {
    local idx=$1
    echo "🧪 Тестируем ${NAMES[$idx]}..."
    ./xmrig -a ${ALGOS[$idx]} -o ${POOLS[$idx]} -u "$WALLET.test" -p x --threads 4 --cpu-priority 5 --no-color --log-file=test.log > /dev/null 2>&1 &
    local pid=$!
    sleep 180
    kill $pid 2>/dev/null
    local speed=$(grep "speed" test.log | tail -1 | grep -o '[0-9]*\.[0-9]* H/s' | head -1)
    [ -z "$speed" ] && speed="0.0 H/s"
    echo "${NAMES[$idx]},$speed" >> algo_scores.csv
    echo "${NAMES[$idx]}: $speed"
}

for i in {0..2}; do test_algo $i; done

BEST=$(sort -t',' -k2 -nr algo_scores.csv | head -1 | cut -d',' -f1)
echo "export BEST_ALGO=\"$BEST\"" > best_algo.sh
echo "🏆 Лучший алгоритм: $BEST"
