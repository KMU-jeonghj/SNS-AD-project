import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import sys
import threading
import struct
import subprocess
import platform
import time
import requests # pip install requests 필요
import json

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("스마트 네트워크 서비스 - 완성본")
        self.geometry("1100x750")

        # --- 전역 상태 변수 ---
        self.server_socket = None
        self.server_running = False
        self.server_thread = None
        self.server_lock = threading.Lock() # Req 16: 임계영역 보호
        self.shutdown_event = threading.Event() # Req 16: 안전 종료 이벤트
        
        self.client_socket = None
        self.client_connected = False
        self.client_thread = None
        
        self.clients = [] # 서버에 접속한 클라이언트 리스트
        self.shared_counter = 0 # 서버 공유 카운터 (Req 15)

        # --- GUI 구성 ---
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self.pg_diag = ttk.Frame(nb)
        nb.add(self.pg_diag, text="네트워크 진단")
        
        self.pg_server = ttk.Frame(nb)
        nb.add(self.pg_server, text="TCP 서버")
        
        self.pg_client = ttk.Frame(nb)
        nb.add(self.pg_client, text="TCP 클라이언트")
        
        self.pg_buf = ttk.Frame(nb)
        nb.add(self.pg_buf, text="버퍼/소켓")
        
        self.pg_draw = ttk.Frame(nb)
        nb.add(self.pg_draw, text="네트워크 그림판")
        
        self.pg_sfc = ttk.Frame(nb)
        nb.add(self.pg_sfc, text="Ryu SFC")

        self._build_diag()
        self._build_server()
        self._build_client()
        self._build_buf()
        self._build_draw()
        self._build_sfc()

    # ====================================================================
    # 1. 네트워크 진단 탭
    # ====================================================================
    def _build_diag(self):
        left = ttk.Frame(self.pg_diag, padding=8)
        left.pack(side="left", fill="y")
        right = ttk.Frame(self.pg_diag, padding=8)
        right.pack(side="right", fill="both", expand=True)

        # IP Config
        ttk.Label(left, text="IP 구성 / netstat / 포트 검사").pack(anchor="w")
        ttk.Button(left, text="IP 구성 확인", command=self.do_ipconfig).pack(fill="x", pady=2)

        # Netstat
        self.var_netstat = tk.StringVar(value="9000")
        row = ttk.Frame(left)
        row.pack(fill="x", pady=2)
        ttk.Entry(row, textvariable=self.var_netstat, width=10).pack(side="left")
        ttk.Button(row, text="netstat 필터", command=self.do_netstat).pack(side="left", padx=4)

        # Port Check
        row2 = ttk.Frame(left)
        row2.pack(fill="x", pady=(6, 2))
        self.var_host = tk.StringVar(value="127.0.0.1")
        self.var_port = tk.StringVar(value="9000")
        ttk.Entry(row2, textvariable=self.var_host, width=14).pack(side="left")
        ttk.Entry(row2, textvariable=self.var_port, width=6).pack(side="left", padx=4)
        ttk.Button(row2, text="포트 오픈 검사", command=self.do_check_port).pack(side="left", padx=4)

        ttk.Separator(left).pack(fill="x", pady=8)

        # Byte Order
        ttk.Label(left, text="바이트/주소 변환").pack(anchor="w")
        ttk.Button(left, text="hton/ntoh 데모", command=self.do_hton).pack(fill="x", pady=2)

        # IP Conversion
        self.var_ipv4 = tk.StringVar(value="8.8.8.8")
        self.var_ipv6 = tk.StringVar(value="2001:4860:4860::8888")
        
        row3 = ttk.Frame(left); row3.pack(fill="x", pady=2)
        ttk.Entry(row3, textvariable=self.var_ipv4, width=18).pack(side="left")
        ttk.Button(row3, text="inet_pton/ntop(IPv4)", command=self.do_inet4).pack(side="left", padx=4)

        row4 = ttk.Frame(left); row4.pack(fill="x", pady=2)
        ttk.Entry(row4, textvariable=self.var_ipv6, width=26).pack(side="left")
        ttk.Button(row4, text="inet_pton/ntop(IPv6)", command=self.do_inet6).pack(side="left", padx=4)

        ttk.Separator(left).pack(fill="x", pady=8)

        # DNS
        ttk.Label(left, text="DNS/이름 변환").pack(anchor="w")
        self.var_dns = tk.StringVar(value="example.com")
        self.var_rev = tk.StringVar(value="8.8.8.8")
        
        row5 = ttk.Frame(left); row5.pack(fill="x", pady=2)
        ttk.Entry(row5, textvariable=self.var_dns, width=18).pack(side="left")
        ttk.Button(row5, text="DNS 조회", command=self.do_dns).pack(side="left", padx=4)
        
        row6 = ttk.Frame(left); row6.pack(fill="x", pady=2)
        ttk.Entry(row6, textvariable=self.var_rev, width=18).pack(side="left")
        ttk.Button(row6, text="역방향 조회", command=self.do_reverse).pack(side="left", padx=4)

        self.out_diag = scrolledtext.ScrolledText(right, height=30)
        self.out_diag.pack(fill="both", expand=True)

    def log_diag(self, s): self._append(self.out_diag, s)

    # Req 1: ifconfig/ipconfig
    def do_ipconfig(self):
        self.log_diag(">>> IP 구성 확인 실행")
        cmd = "ipconfig" if platform.system() == "Windows" else "ifconfig"
        try:
            # 한글 윈도우 인코딩 호환을 위해 cp949 디코딩 시도
            res = subprocess.check_output(cmd, shell=True)
            try:
                text = res.decode('cp949')
            except:
                text = res.decode('utf-8', errors='ignore')
            self.log_diag(text)
        except Exception as e:
            self.log_diag(f"Error: {e}")

    # Req 6: netstat filtering
    def do_netstat(self):
        port = self.var_netstat.get()
        self.log_diag(f">>> netstat 필터 실행 (Port: {port})")
        
        if platform.system() == "Windows":
            cmd = f"netstat -an -p tcp | findstr {port}"
        else:
            cmd = f"netstat -an | grep {port}"
            
        try:
            res = subprocess.check_output(cmd, shell=True)
            self.log_diag(res.decode('utf-8', errors='ignore'))
        except subprocess.CalledProcessError:
            self.log_diag("결과 없음 (해당 포트 대기중 아님)")
        except Exception as e:
            self.log_diag(f"Error: {e}")

    # Req 5: Port check
    def do_check_port(self):
        host = self.var_host.get()
        port = int(self.var_port.get())
        self.log_diag(f">>> 포트 검사: {host}:{port}")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        if result == 0:
            self.log_diag(f"결과: Open (성공)")
        else:
            self.log_diag(f"결과: Closed or Filtered (코드: {result})")
        sock.close()

    # Req 2: Byte order
    def do_hton(self):
        self.log_diag(">>> hton/ntoh 데모 (Host to Network / Network to Host)")
        val = 0x1234
        self.log_diag(f"Original: {hex(val)}")
        packed = socket.htons(val)
        self.log_diag(f"htons(16bit): {hex(packed)}")
        unpacked = socket.ntohs(packed)
        self.log_diag(f"ntohs(16bit): {hex(unpacked)}")
        
        val32 = 0x12345678
        packed32 = socket.htonl(val32)
        self.log_diag(f"htonl(32bit): {hex(packed32)}")

    # Req 3: IP conversion
    def do_inet4(self):
        ip = self.var_ipv4.get()
        try:
            packed = socket.inet_pton(socket.AF_INET, ip)
            self.log_diag(f"inet_pton({ip}) -> Hex: {packed.hex()}")
            unpacked = socket.inet_ntop(socket.AF_INET, packed)
            self.log_diag(f"inet_ntop -> {unpacked}")
        except Exception as e:
            self.log_diag(f"Error: {e}")

    def do_inet6(self):
        ip = self.var_ipv6.get()
        try:
            packed = socket.inet_pton(socket.AF_INET6, ip)
            self.log_diag(f"inet_pton(IPv6) -> Len: {len(packed)} bytes")
            unpacked = socket.inet_ntop(socket.AF_INET6, packed)
            self.log_diag(f"inet_ntop -> {unpacked}")
        except Exception as e:
            self.log_diag(f"Error: {e}")

    # Req 4: DNS
    def do_dns(self):
        domain = self.var_dns.get()
        try:
            ip = socket.gethostbyname(domain)
            self.log_diag(f"DNS 조회({domain}) -> {ip}")
        except Exception as e:
            self.log_diag(f"DNS Error: {e}")

    def do_reverse(self):
        ip = self.var_rev.get()
        try:
            name, alias, ip_list = socket.gethostbyaddr(ip)
            self.log_diag(f"역방향 조회({ip}) -> {name}")
        except Exception as e:
            self.log_diag(f"Reverse Error: {e}")

    # ====================================================================
    # 2. TCP 서버 탭
    # ====================================================================
    def _build_server(self):
        top = ttk.Frame(self.pg_server, padding=8); top.pack(fill="x")
        self.var_srv_port = tk.StringVar(value="9000")
        ttk.Label(top, text="포트").pack(side="left")
        ttk.Entry(top, textvariable=self.var_srv_port, width=6).pack(side="left", padx=4)
        
        self.var_broadcast = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="그림판 브로드캐스트", variable=self.var_broadcast).pack(side="left", padx=8)
        
        ttk.Button(top, text="서버 시작", command=self.server_start).pack(side="left", padx=4)
        ttk.Button(top, text="서버 정지", command=self.server_stop).pack(side="left", padx=4)

        stat = ttk.Frame(self.pg_server, padding=8); stat.pack(fill="x")
        self.lbl_clients = ttk.Label(stat, text="접속: 0")
        self.lbl_clients.pack(side="left")
        self.lbl_counter = ttk.Label(stat, text="카운터: 0")
        self.lbl_counter.pack(side="left", padx=12)
        ttk.Button(stat, text="상태 갱신", command=self.server_status).pack(side="left")

        self.out_srv = scrolledtext.ScrolledText(self.pg_server, height=28)
        self.out_srv.pack(fill="both", expand=True)

    def log_srv(self, s): self._append(self.out_srv, s)

    def server_start(self):
        if self.server_running:
            return
        
        port = int(self.var_srv_port.get())
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 주소 재사용 옵션
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('', port))
            self.server_socket.listen(5)
            self.server_running = True
            self.shutdown_event.clear()
            
            # Accept Thread 시작
            self.server_thread = threading.Thread(target=self._accept_loop, daemon=True)
            self.server_thread.start()
            
            self.log_srv(f"[서버] 시작 @ {port}")
        except Exception as e:
            self.log_srv(f"[서버] 시작 실패: {e}")

    def server_stop(self):
        if not self.server_running: return
        
        self.log_srv("[서버] 정지 요청...")
        self.server_running = False
        self.shutdown_event.set() # Req 16: Event set
        
        # 강제로 소켓 닫아서 accept 블로킹 해제
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None

        # 연결된 클라이언트 정리
        for conn, addr in self.clients:
            try: conn.close()
            except: pass
        self.clients = []
        self.log_srv("[서버] 완전히 정지됨")

    def server_status(self):
        self.lbl_clients.config(text=f"접속: {len(self.clients)}")
        self.lbl_counter.config(text=f"카운터: {self.shared_counter}")
        self.log_srv(f"[상태] 클라수={len(self.clients)}, 카운터={self.shared_counter}")

    def _accept_loop(self):
        while self.server_running:
            try:
                conn, addr = self.server_socket.accept()
                if self.shutdown_event.is_set():
                    break
                    
                self.log_srv(f"[서버] 접속 됨: {addr}")
                
                # Req 15: 공유 카운터 임계영역 보호
                with self.server_lock:
                    self.clients.append((conn, addr))
                    self.shared_counter += 1
                
                # 클라이언트 핸들러 스레드 시작
                t = threading.Thread(target=self._client_handler, args=(conn, addr), daemon=True)
                t.start()
                
                # UI 업데이트 (메인 스레드가 아니지만 Tkinter에서 insert는 보통 허용됨)
                self.server_status()
                
            except OSError:
                break # 소켓이 닫히면 루프 종료

    def _client_handler(self, conn, addr):
        while self.server_running:
            try:
                data = conn.recv(1024)
                if not data: 
                    break
                
                # 받은 데이터 처리
                try:
                    decoded_data = data.decode('utf-8', errors='ignore')
                    
                    # 1. 그림판 좌표 패킷 처리 (DRAW:x1,y1,x2,y2)
                    if decoded_data.startswith("DRAW:"):
                        if self.var_broadcast.get():
                            self._broadcast(data, sender=conn)
                    else:
                        # 2. 일반 텍스트 메시지
                        self.log_srv(f"[{addr}] {decoded_data.strip()}")
                        
                except:
                    pass # 바이너리 데이터 등의 에러 무시

            except:
                break
        
        self.log_srv(f"[서버] 접속 해제: {addr}")
        with self.server_lock:
            if (conn, addr) in self.clients:
                self.clients.remove((conn, addr))
            self.shared_counter -= 1
        conn.close()
        self.server_status()

    def _broadcast(self, data, sender):
        # Req 10: 네트워크 그림판 (서버가 브로드캐스트)
        dead_clients = []
        with self.server_lock:
            for client in self.clients:
                c_sock, c_addr = client
                if c_sock != sender: # 보낸 사람 제외하고 전송
                    try:
                        c_sock.sendall(data)
                    except:
                        dead_clients.append(client)
            
            # 전송 실패한 클라이언트 정리
            for dc in dead_clients:
                self.clients.remove(dc)

    # ====================================================================
    # 3. TCP 클라이언트 탭
    # ====================================================================
    def _build_client(self):
        top = ttk.Frame(self.pg_client, padding=8); top.pack(fill="x")
        
        self.var_cli_host = tk.StringVar(value="127.0.0.1")
        self.var_cli_port = tk.StringVar(value="9000")
        
        ttk.Label(top, text="호스트").pack(side="left")
        ttk.Entry(top, textvariable=self.var_cli_host, width=16).pack(side="left", padx=4)
        ttk.Label(top, text="포트").pack(side="left")
        ttk.Entry(top, textvariable=self.var_cli_port, width=6).pack(side="left", padx=4)
        
        ttk.Button(top, text="접속", command=self.cli_connect).pack(side="left", padx=4)
        ttk.Button(top, text="해제", command=self.cli_close).pack(side="left", padx=4)

        opt = ttk.Frame(self.pg_client, padding=8); opt.pack(fill="x")
        self.var_mode = tk.StringVar(value="VAR")
        
        # Req 11, 12, 13: 전송 모드 선택
        ttk.Radiobutton(opt, text="VAR(\\n)", variable=self.var_mode, value="VAR").pack(side="left")
        ttk.Radiobutton(opt, text="FIXED(32B)", variable=self.var_mode, value="FIXED").pack(side="left", padx=6)
        ttk.Radiobutton(opt, text="MIX(4B len+data)", variable=self.var_mode, value="MIX").pack(side="left", padx=6)
        
        # Req 14: 전송 후 종료
        self.var_after_close = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt, text="전송 후 종료", variable=self.var_after_close).pack(side="left", padx=8)

        msg = ttk.Frame(self.pg_client, padding=8); msg.pack(fill="x")
        self.var_msg = tk.StringVar(value="hello")
        ttk.Entry(msg, textvariable=self.var_msg, width=60).pack(side="left")
        ttk.Button(msg, text="전송", command=self.cli_send).pack(side="left", padx=6)

        self.out_cli = scrolledtext.ScrolledText(self.pg_client, height=28)
        self.out_cli.pack(fill="both", expand=True)

    def log_cli(self, s): self._append(self.out_cli, s)

    def cli_connect(self):
        if self.client_connected: return
        
        host = self.var_cli_host.get()
        try:
            port = int(self.var_cli_port.get())
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
            self.client_connected = True
            
            # 수신 스레드 시작
            t = threading.Thread(target=self._cli_recv_loop, daemon=True)
            t.start()
            
            self.log_cli(f"[클라] 연결 성공 -> {host}:{port}")
        except Exception as e:
            self.log_cli(f"[클라] 연결 실패: {e}")

    def cli_close(self):
        if not self.client_connected: return
        try:
            self.client_socket.close()
        except: pass
        self.client_connected = False
        self.client_socket = None
        self.log_cli("[클라] 연결 해제")

    def _cli_recv_loop(self):
        while self.client_connected:
            try:
                data = self.client_socket.recv(1024)
                if not data: break
                
                text = data.decode('utf-8', errors='ignore')
                
                # 그림판 데이터인지 확인 ("DRAW:x1,y1,x2,y2")
                if text.startswith("DRAW:"):
                    try:
                        coords = text.replace("DRAW:", "").strip().split(",")
                        x1, y1, x2, y2 = map(int, coords)
                        # GUI 스레드에서 그리기
                        self.canvas.after(0, lambda: self.canvas.create_line(x1, y1, x2, y2, width=2, fill="red"))
                    except:
                        pass
                else:
                    self.log_cli(f"[수신] {text}")
            except:
                break
        self.client_connected = False

    def cli_send(self):
        if not self.client_connected:
            messagebox.showerror("에러", "서버에 연결되지 않았습니다.")
            return

        raw_msg = self.var_msg.get()
        mode = self.var_mode.get()
        data_to_send = b""

        try:
            if mode == "VAR":
                # Req 12: 가변 길이 (\n)
                data_to_send = (raw_msg + "\n").encode('utf-8')
            elif mode == "FIXED":
                # Req 11: 고정 길이 (32바이트)
                encoded = raw_msg.encode('utf-8')
                if len(encoded) > 32:
                    data_to_send = encoded[:32]
                else:
                    data_to_send = encoded + b'\0' * (32 - len(encoded))
            elif mode == "MIX":
                # Req 13: 헤더(4B) + 데이터
                encoded = raw_msg.encode('utf-8')
                length = len(encoded)
                header = struct.pack("!I", length) # Big Endian Unsigned Int
                data_to_send = header + encoded
            
            self.client_socket.sendall(data_to_send)
            self.log_cli(f"[송신-{mode}] {raw_msg}")

            # Req 14: 전송 후 종료
            if self.var_after_close.get():
                self.log_cli("[클라] 전송 후 종료 옵션으로 연결 끊음")
                self.cli_close()

        except Exception as e:
            self.log_cli(f"[오류] 전송 실패: {e}")

    # ====================================================================
    # 4. 버퍼/소켓 탭
    # ====================================================================
    def _build_buf(self):
        top = ttk.Frame(self.pg_buf, padding=8); top.pack(fill="x")
        ttk.Button(top, text="클라 소켓 버퍼 조회", command=self.buf_client).pack(side="left", padx=4)
        ttk.Button(top, text="임시 소켓 버퍼 조회", command=self.buf_temp).pack(side="left", padx=4)
        
        self.out_buf = scrolledtext.ScrolledText(self.pg_buf, height=30)
        self.out_buf.pack(fill="both", expand=True)

    def log_buf(self, s): self._append(self.out_buf, s)

    # Req 9: SO_SNDBUF/SO_RCVBUF 조회
    def buf_client(self):
        if not self.client_connected or not self.client_socket:
            self.log_buf("오류: 클라이언트가 연결되지 않았습니다.")
            return
        
        snd = self.client_socket.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        rcv = self.client_socket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        self.log_buf(f"[현재연결] Send Buf: {snd}, Recv Buf: {rcv}")

    def buf_temp(self):
        temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        snd = temp.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        rcv = temp.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        temp.close()
        self.log_buf(f"[임시소켓] Send Buf: {snd}, Recv Buf: {rcv}")

    # ====================================================================
    # 5. 네트워크 그림판 탭
    # ====================================================================
    def _build_draw(self):
        info = ttk.Frame(self.pg_draw, padding=8); info.pack(fill="x")
        ttk.Label(info, text="그림판 - 드래그 시 선 그리기, (접속 시) 서버 경유 브로드캐스트").pack(side="left")
        
        self.canvas = tk.Canvas(self.pg_draw, bg="white", height=520)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)
        
        self.canvas.bind("<ButtonPress-1>", self._draw_start)
        self.canvas.bind("<B1-Motion>", self._draw_move)
        self.canvas.bind("<ButtonRelease-1>", self._draw_end)
        
        self._last_xy = None

    def _draw_start(self, e):
        self._last_xy = (e.x, e.y)

    def _draw_move(self, e):
        if not self._last_xy: return
        x1, y1 = self._last_xy
        x2, y2 = e.x, e.y
        
        # 로컬 캔버스에 그리기
        self.canvas.create_line(x1, y1, x2, y2, width=2)
        
        # Req 10: 접속 상태면 서버로 좌표 전송 (포맷: DRAW:x1,y1,x2,y2)
        if self.client_connected and self.client_socket:
            msg = f"DRAW:{x1},{y1},{x2},{y2}"
            try:
                self.client_socket.sendall(msg.encode('utf-8'))
            except:
                pass # 전송 에러 무시
                
        self._last_xy = (x2, y2)

    def _draw_end(self, e):
        self._last_xy = None

    # ====================================================================
    # 6. Ryu SFC 탭 (REST API)
    # ====================================================================
    def _build_sfc(self):
        top = ttk.Frame(self.pg_sfc, padding=8); top.pack(fill="x")
        
        self.var_rest_host = tk.StringVar(value="127.0.0.1")
        self.var_rest_port = tk.StringVar(value="8080")
        self.var_dpid = tk.StringVar(value="1")
        self.var_prio = tk.StringVar(value="100")
        
        # 포트 매핑 정보 (h1, fw, nat, h2)
        self.var_h1 = tk.StringVar(value="1")
        self.var_fw = tk.StringVar(value="2")
        self.var_nat = tk.StringVar(value="3")
        self.var_h2 = tk.StringVar(value="4")

        # 컨트롤 행
        ttk.Label(top, text="Ryu IP").grid(row=0, column=0, sticky="e")
        ttk.Entry(top, textvariable=self.var_rest_host, width=14).grid(row=0, column=1)
        ttk.Label(top, text=":").grid(row=0, column=2)
        ttk.Entry(top, textvariable=self.var_rest_port, width=6).grid(row=0, column=3, padx=4)
        
        ttk.Label(top, text="DPID").grid(row=0, column=4, sticky="e")
        ttk.Entry(top, textvariable=self.var_dpid, width=6).grid(row=0, column=5)
        
        ttk.Label(top, text="Prio").grid(row=0, column=6, sticky="e")
        ttk.Entry(top, textvariable=self.var_prio, width=6).grid(row=0, column=7)

        # 포트 설정 행
        ports = ttk.Frame(self.pg_sfc, padding=8); ports.pack(fill="x")
        for i, (lab, var) in enumerate([("h1", self.var_h1), ("fw", self.var_fw), 
                                        ("nat", self.var_nat), ("h2", self.var_h2)]):
            ttk.Label(ports, text=lab).grid(row=0, column=i*2)
            ttk.Entry(ports, textvariable=var, width=6).grid(row=0, column=i*2+1, padx=4)

        btns = ttk.Frame(self.pg_sfc, padding=8); btns.pack(fill="x")
        ttk.Button(btns, text="SFC 설치", command=self.sfc_install).pack(side="left", padx=4)
        ttk.Button(btns, text="바이패스", command=self.sfc_bypass).pack(side="left", padx=4)
        ttk.Button(btns, text="플로우 조회", command=self.sfc_dump).pack(side="left", padx=4)
        ttk.Button(btns, text="플로우 삭제", command=self.sfc_clear).pack(side="left", padx=4)

        self.out_sfc = scrolledtext.ScrolledText(self.pg_sfc, height=24)
        self.out_sfc.pack(fill="both", expand=True, padx=8, pady=8)

    def log_sfc(self, s): self._append(self.out_sfc, s)
    
    def _get_ryu_url(self, endpoint):
        return f"http://{self.var_rest_host.get()}:{self.var_rest_port.get()}{endpoint}"

    # SFC Req: REST API POST
    def sfc_install(self):
        dpid = self.var_dpid.get()
        prio = int(self.var_prio.get())
        h1 = int(self.var_h1.get())
        fw = int(self.var_fw.get())
        nat = int(self.var_nat.get())
        h2 = int(self.var_h2.get())
        
        # 예시: h1 -> fw -> nat -> h2 체인 구성
        # 실제 류 컨트롤러가 요구하는 JSON 포맷에 맞춰야 함 (여기서는 표준적인 OpenFlow add flow 예시)
        flows = [
            {"dpid": int(dpid), "priority": prio, "match": {"in_port": h1}, "actions": [{"port": fw}]},
            {"dpid": int(dpid), "priority": prio, "match": {"in_port": fw}, "actions": [{"port": nat}]},
            {"dpid": int(dpid), "priority": prio, "match": {"in_port": nat}, "actions": [{"port": h2}]},
            {"dpid": int(dpid), "priority": prio, "match": {"in_port": h2}, "actions": [{"port": nat}]} # 역방향 등 필요 시 추가
        ]
        
        self.log_sfc(">>> SFC 설치 요청 (h1->fw->nat->h2)")
        url = self._get_ryu_url("/stats/flowentry/add")
        
        for flow in flows:
            try:
                # Ryu REST API는 보통 POST로 플로우 추가
                resp = requests.post(url, json=flow, timeout=2)
                if resp.status_code == 200:
                    self.log_sfc(f"성공: in_port={flow['match']['in_port']} -> out={flow['actions']}")
                else:
                    self.log_sfc(f"실패: {resp.status_code} {resp.text}")
            except Exception as e:
                self.log_sfc(f"에러: {e}")

    def sfc_bypass(self):
        # SFC를 거치지 않고 h1 <-> h2 직접 통신
        dpid = self.var_dpid.get()
        prio = int(self.var_prio.get()) + 10 # 더 높은 우선순위
        h1 = int(self.var_h1.get())
        h2 = int(self.var_h2.get())
        
        flows = [
            {"dpid": int(dpid), "priority": prio, "match": {"in_port": h1}, "actions": [{"port": h2}]},
            {"dpid": int(dpid), "priority": prio, "match": {"in_port": h2}, "actions": [{"port": h1}]}
        ]
        
        self.log_sfc(">>> 바이패스 설치 (h1 <-> h2)")
        url = self._get_ryu_url("/stats/flowentry/add")
        
        for flow in flows:
            try:
                requests.post(url, json=flow, timeout=2)
                self.log_sfc(f"바이패스 룰 추가 완료")
            except Exception as e:
                self.log_sfc(f"에러: {e}")

    def sfc_dump(self):
        dpid = self.var_dpid.get()
        self.log_sfc(f">>> 플로우 조회 (dpid={dpid})")
        url = self._get_ryu_url(f"/stats/flow/{dpid}")
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                self.log_sfc(json.dumps(data, indent=2))
            else:
                self.log_sfc(f"조회 실패: {resp.status_code}")
        except Exception as e:
            self.log_sfc(f"에러: {e} (Ryu 컨트롤러 미실행?)")

    def sfc_clear(self):
        dpid = self.var_dpid.get()
        self.log_sfc(f">>> 플로우 전체 삭제 (dpid={dpid})")
        url = self._get_ryu_url(f"/stats/flowentry/clear/{dpid}")
        try:
            # DELETE 메서드
            resp = requests.delete(url, timeout=2)
            if resp.status_code == 200:
                self.log_sfc("삭제 성공")
            else:
                self.log_sfc(f"삭제 실패: {resp.status_code}")
        except Exception as e:
            self.log_sfc(f"에러: {e}")

    # ====================================================================
    # 공용 유틸리티
    # ====================================================================
    # 로그 출력 함수
    def _append(self, widget, text):
        widget.insert("end", text + "\n")
        widget.see("end")

if __name__ == "__main__":
    app = App()
    app.mainloop()