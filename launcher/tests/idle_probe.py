"""빈 연결 N개를 열어 둔 채 ping 응답 시간을 잰다. 사용: python -I idle_probe.py <port> <n>"""
import socket, sys, time, urllib.request
port, n = int(sys.argv[1]), int(sys.argv[2])
socks = []
try:
    for _ in range(n):
        s = socket.create_connection(('127.0.0.1', port)); s.send(b'G'); socks.append(s)
except OSError:
    print('timeout'); sys.exit(0)
time.sleep(0.5)
t = time.time()
try:
    urllib.request.build_opener(urllib.request.ProxyHandler({})).open(f'http://127.0.0.1:{port}/__ebs_ping', timeout=30).read()
    print(f'{time.time() - t:.1f}')
except Exception:
    print('timeout')
for s in socks: s.close()
