import argparse
import json
import matplotlib.pyplot as plt
import matplotlib as mpl
from os import system, environ
from time import sleep

SPEEDTEST_TIMES = 3 

def isip(tar: str) -> bool:
    for each in tar.split('.'):
        if not each.isdigit():
            return False
    return True

def setColumnAlign(table:plt.table, column: int, align: str):
    cells = [key for key in table._cells if (key[1] == column and key[0] != 0)]
    for cell in cells:
        table._cells[cell].set_text_props(ha=align)
        table._cells[cell].PAD = 0.01

class nodeResult:
    def __init__(self, name: str, jsonStr: str, ipJsonStr: str, icmping: float, nfu: int, hipisp: str, avgSpeed: float, s2: float):
        self.name = name
        self._json = json.loads(jsonStr)
        self.icmping = icmping
        self.ping = self._json['ping']['latency']
        self.jitter = self._json['ping']['jitter']
        self.download = str(float(self._json['download']['bandwidth']) * 8 / 1000000.0)
        self.upload = str(float(self._json['upload']['bandwidth']) * 8 / 1000000.0)
        self.avgSpeed = avgSpeed
        self.s2 = s2
        try:
            self._ipJson = json.loads(ipJsonStr)
            self.isp = self._ipJson['org']
            self.country = self._ipJson['country']
            self.region = self._ipJson['region']
            self.city = self._ipJson['city']
            self.hipisp = hipisp
        except:
            self.isp = 'Unknown'
            self.country = 'Unknown'
            self.region = 'Unknown'
            self.city = 'Unknown'
            self.hipisp = 'Unknown'
        self.nfu = nfu

    def __str__(self):
        return f'ISP: {self.isp} Latency: {self.ping}\nDownload: {float(self.download):.2f} Mbps, Upload: {float(self.upload):.2f} Mbps'

    def inlineStr(self) -> str:
        return '\t\t\t\t'.join([self.isp, str(self.ping), f'{float(self.download):.2f} Mbps', f'{float(self.upload):.2f} Mbps'])

    @staticmethod
    def inlineHeaders() -> str:
        return '\t\t\t\t'.join(['ISP', 'Latency', 'Download', 'Upload'])

def colour(speed: str('Mbps')):
    if speed > 500:
        return '#204CE8'
    else:
        return f'#20{hex(int(181-(speed/500.0)*(181-85)))[2:].zfill(2).upper()}E8'

def s2colour(s2: float):
    if s2> 500:
        return '#9B000F'
    else:
        return f'#9B{hex(int(255-(s2/500.0)*(255-0)))[2:].zfill(2).upper()}0F'

def laColour(latency):
    la = float(latency)
    if la > 700:
        return '#9B000F'
    else:
        return f'#9B{hex(int(255-(latency/700.0)*(255-0)))[2:].zfill(2).upper()}0F'

def deploy(configURL: str, mmdbPath: str):
    if system('ls src && find src/clash') != 0:
        raise(Exception('Resource directory not found. Have you downloaded Clash?'))
    if mmdbPath:
        system(f'rm src/Country.mmdb;(cp {mmdbPath} src/Country.mmdb) && cd src && wget {configURL} --user-agent="clash/1.0.0" -O config.raw.yaml')
    else:
        system(f'cd src && rm Country.mmdb;wget https://github.com/Dreamacro/maxmind-geoip/releases/download/20220812/Country.mmdb && wget --user-agent="clash/1.0.0" {configURL} -O config.raw.yaml')
    with open('src/config.raw.yaml') as config:
        proxies = [f'  -{each}' if each.strip() else None for each in '\n'.join(config.readlines()).split('proxies:')[1].split('proxy-groups')[0].split('\n  -')]
        if len(proxies) == 1:
            proxies = proxies[0].split('\n')
            start = 2
        else:
            start = 1
        # print(proxies)
    seq = []
    print(nodeResult.inlineHeaders())
    for proxy in proxies[start:]:
        # print(proxy)
        # print('----------')
        n, s = switch(proxy)
        tmp = speedtest(n, s)
        if tmp:
            try:
                print(tmp.inlineStr())
            except (KeyError, AttributeError):
                with open('result.json') as fil:
                    print('\n'.join(fil.readlines()))
                    print('Failed.')
            seq.append(tmp)
            
    return seq

def switch(nodeBlob: str):
    if '{' in nodeBlob:
        name = nodeBlob[nodeBlob.find('name: ')+6:nodeBlob[nodeBlob.find('name: '):].find(',')+nodeBlob.find('name: ')]
    else:
        name = nodeBlob[nodeBlob.find('name: ')+6:nodeBlob[nodeBlob.find('name: '):].find('\n')+nodeBlob.find('name: ')]
    if '{' in nodeBlob:
        server = nodeBlob[nodeBlob.find('server: ')+8:nodeBlob[nodeBlob.find('server: '):].find(',')+nodeBlob.find('server: ')]
    else:
        server = nodeBlob[nodeBlob.find('server: ')+8:nodeBlob[nodeBlob.find('server: '):].find('\n')+nodeBlob.find('server: ')]
    if name.startswith("'") or name.startswith('"'):
        name = name[1:-1]
    profile = f'''
port: 7890
socks-port: 7891
allow-lan: false
mode: rule
log-level: info
external-controller: '0.0.0.0:9090'

dns:
  enable: true
  ipv6: false
  listen: '0.0.0.0:53'
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  nameserver:
    - 119.29.29.29
    - 1.1.1.1
  fallback:
    - 1.0.0.1
    - 8.8.8.8
  fallback-filter:
    geoip: true
    ipcidr:
      - 240.0.0.0/4

proxies:
{nodeBlob}

rules:
  - MATCH, '''+name+'\n'

    with open('src/config.yaml', 'w') as config:
        print(profile, file=config)
    return name, server

def speedtest(name: str, server: str) -> nodeResult:
    environ['ALL_PROXY'] = 'http://127.0.0.1:7890'
    system('((kill -9 $(pidof clash)) 2>err);(nohup src/clash -d src 1>clash_logs 2>&1 &)')
    sleep(3)
    # system('echo hello 1> result.json 2>err')fr i 
    speeds = []
    for _ in range(SPEEDTEST_TIMES):
        system('(speedtest --accept-gdpr -f json 1> result.json 2>err)')
        try: 
            with open('result.json') as resultFile:
                speeds.append(float(json.loads('\n'.join(resultFile.readlines()))['download']['bandwidth'])*8/1048576.0)
        except:
            speeds.append(0)
    avgSpeed = 0
    for i in range(SPEEDTEST_TIMES):
        avgSpeed += speeds[i]
    avgSpeed /= float(SPEEDTEST_TIMES)
    s2 = 0
    for i in range(SPEEDTEST_TIMES):
        s2 += (speeds[i] - avgSpeed) ** 2
    s2 /= float(SPEEDTEST_TIMES)
    with open('result.json') as resultFile:
        try:
            system('curl -m 10 --connect-timeout 10 ipinfo.io > ipinfo')
            # print('hello')
            system(f'dig {server} +short > homeip')
            with open('homeip') as fil:
                candidates = [each.strip() for each in fil.readlines()]
                ip = 'stop.is'
                for each in candidates:
                    if isip(each):
                        ip = each
                system(f'curl -m 10 --connect-timeout 10 ipinfo.io/{ip} > hipinfo')
            with open('hipinfo') as fil:
                hipinfo = json.loads('\n'.join(fil.readlines()))
            hipisp = hipinfo['org']
        except:
            hipisp = '--'
        try:
            system('curl -m 10 --connect-timeout 10 ip.sb | xargs -I {} -d "\n" ping -c 4 {} > icmping')
            sum = 0
            with open('icmping') as fil:
                for line in fil.readlines()[1:5]:
                    sum += float(line[line.find('time=')+5:line.find(' ms')])
        except:
            sum = 0.0
        try:
            system('curl -L -m 10 --connect-timeout 10 -w %{http_code} -o /dev/null https://www.netflix.com/sg-zh/title/70143836 > nfu')
            with open('nfu') as fil:
                code = fil.readlines()[0].strip()
                nfu = 2 if code in ('200', '302') else (1 if code == '404' else 0)
            if code == '404':
                system('curl -L -m 10 --connect-timeout 10 -w %{http_code} -o /dev/null https://www.netflix.com/title/70153373 > nfu')
                with open('nfu') as fil:
                    code = fil.readlines()[0].strip()
                    if code in ('200', '302'):
                        nfu = 2
        except:
            nfu = 0
        try:
            with open('ipinfo') as fil:
                r = nodeResult(name, resultFile.readlines()[0].strip(), '\n'.join(fil.readlines()), float(sum)/4.0, nfu, hipisp, avgSpeed, s2)
        except (IndexError, KeyError):
            r = name
            return r
    # system('rm result.json')
    return r

def plot(nodeList: list):
    mpl.rcParams["font.sans-serif"]=["SimHei"]
    mpl.rcParams["font.family"] = 'sans-serif'
    lbs = ['节点名称', 'ICMPing', 'Speedtest Ping', '抖动', '下载速度', '上传速度', '方差', 'Netflix', '落地IP属地', '落地提供商', '入口提供商']
    colours = []
    texts = []
    sym = 1
    for each in nodeList:
        sym = 1 - sym
        back = '#DDDDDD' if sym == 1 else '#FFFFFF'
        if isinstance(each, nodeResult):
            colours.append([back, laColour(each.icmping) if each.icmping != 0.0 else '#969696', laColour(each.ping), laColour(each.jitter), colour(float(each.avgSpeed)), colour(float(each.upload)), s2colour(each.s2), '#00FF59' if each.nfu == 2 else ('#FFFFFF' if each.nfu == 1 else '#BF2F0B'), back, back, back])
            texts.append([each.name, f'{each.icmping:.2f} ms' if each.icmping != 0.0 else '--', f'{each.ping} ms', f'{each.jitter} ms', f'{float(each.avgSpeed):.2f} Mbps', f'{float(each.upload):.2f} Mbps', f'{each.s2:.2f} Mbps^2', '解锁' if each.nfu == 2 else ('自制' if each.nfu == 1 else '失败'), f'{each.city}, {each.region}, {each.country}', each.isp, each.hipisp])
        else:
            colours.append([back, '#FF0000', '#FF0000', '#FF0000', '#969696', '#969696', '#969696', '#969696', back, back, back])
            texts.append([each, '--', '--', '--', '--', '--', '--', '--', '--', '--', '--'])
    plt.figure(dpi=300, figsize=(1, 1))
    mpl.pyplot.axis('off')
    plt.autoscale(enable=True, tight=True)
    tb = plt.table(cellText = texts, cellLoc = 'center', colLabels = lbs, cellColours = colours, loc='best')
    tb.auto_set_font_size(False)
    tb.set_fontsize(12)
    tb.scale(1, 1.5)
    tb._autoColumns = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    for i in (0, 8, 9, 10):
        setColumnAlign(tb, i, 'left')
    plt.title('blusterSpeed [Dev]', loc='left')
    plt.savefig('result.png', bbox_inches='tight')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A way to test the speed of nodes in a Clash configuration.')
    parser.add_argument('url', metavar='configURL', type=str, help='URL of your remote configuration')
    parser.add_argument('-c', '--cdb', metavar='PATH', type=str, help='Use custom `Country.mmdb`', default='')
    args = parser.parse_args()

    MMDB = args.cdb
    URL = args.url

    results = deploy(URL, MMDB)
    plot(results)

    # print(speedtest())