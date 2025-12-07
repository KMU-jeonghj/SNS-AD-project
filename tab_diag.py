import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import platform
import socket
import sys
from utils import log_enter


class DiagTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):

        left = ttk.Frame(self, padding=8)
        left.pack(side="left", fill="y")

        right = ttk.Frame(self, padding=8)
        right.pack(side="right", fill="both", expand=True)
        self.out = scrolledtext.ScrolledText(right)
        self.out.pack(fill="both", expand=True)

        # ========================================================
        # 섹션 1: 시스템 네트워크 진단
        # ========================================================
        ttk.Label(left, text="[시스템 네트워크 진단]").pack(anchor="w", pady=(0, 5))

        #  IP 구성 확인
        ttk.Button(left, text="IP 구성 확인 (ipconfig)",
                   command=self.do_ipconfig).pack(fill="x", pady=2)

        #  Netstat
        row_net = ttk.Frame(left)
        row_net.pack(fill="x", pady=2)
        self.var_netstat = tk.StringVar(value="9000")
        ttk.Entry(row_net, textvariable=self.var_netstat,
                  width=8).pack(side="left")
        ttk.Button(row_net, text="포트 확인(netstat)", command=self.do_netstat).pack(
            side="left", padx=4, fill="x", expand=True)

        #  포트 오픈 검사
        row_port = ttk.Frame(left)
        row_port.pack(fill="x", pady=2)
        self.var_host = tk.StringVar(value="127.0.0.1")
        self.var_port = tk.StringVar(value="9000")
        ttk.Entry(row_port, textvariable=self.var_host,
                  width=12).pack(side="left")
        ttk.Entry(row_port, textvariable=self.var_port,
                  width=6).pack(side="left", padx=2)
        ttk.Button(row_port, text="연결 확인", command=self.do_check_port).pack(
            side="left", padx=2)

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=10)

        # ========================================================
        # 섹션 2: 바이트 순서 / 주소 변환
        # ========================================================
        ttk.Label(left, text="[바이트/주소 변환]").pack(anchor="w", pady=(0, 5))

        #  hton
        row_hton = ttk.Frame(left)
        row_hton.pack(fill="x", pady=2)
        self.var_hton_val = tk.StringVar(value="9000")
        ttk.Entry(row_hton, textvariable=self.var_hton_val,
                  width=8).pack(side="left")
        ttk.Button(row_hton, text="바이트 변환 (htons)", command=self.do_hton).pack(
            side="left", padx=4, fill="x", expand=True)

        #  IPv4 pton
        ttk.Label(
            left, text="inet_pton (IPv4 -> Hex)").pack(anchor="w", pady=(5, 0))
        row_v4 = ttk.Frame(left)
        row_v4.pack(fill="x", pady=2)
        self.var_pton_v4 = tk.StringVar(value="127.0.0.1")
        ttk.Entry(row_v4, textvariable=self.var_pton_v4, width=25).pack(
            side="left", fill="x", expand=True)
        ttk.Button(row_v4, text="IPv4 변환", command=self.do_pton_v4).pack(
            side="left", padx=4)

        #  IPv6 pton
        ttk.Label(
            left, text="inet_pton (IPv6 -> Hex)").pack(anchor="w", pady=(2, 0))
        row_v6 = ttk.Frame(left)
        row_v6.pack(fill="x", pady=2)
        self.var_pton_v6 = tk.StringVar(value="2001:db8::1")
        ttk.Entry(row_v6, textvariable=self.var_pton_v6, width=25).pack(
            side="left", fill="x", expand=True)
        ttk.Button(row_v6, text="IPv6 변환", command=self.do_pton_v6).pack(
            side="left", padx=4)

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=10)

        # ========================================================
        # 섹션 3: DNS / 이름 변환
        # ========================================================
        ttk.Label(left, text="[DNS/이름 변환]").pack(anchor="w", pady=(0, 5))

        #  정방향 조회 (도메인 -> IP)
        ttk.Label(left, text="정방향 (Domain -> IP)").pack(anchor="w", pady=(5, 0))
        row_dns_fwd = ttk.Frame(left)
        row_dns_fwd.pack(fill="x", pady=2)

        self.var_dns_fwd = tk.StringVar(value="www.google.com")
        ttk.Entry(row_dns_fwd, textvariable=self.var_dns_fwd,
                  width=25).pack(side="left", fill="x", expand=True)
        ttk.Button(row_dns_fwd, text="조회", command=self.do_dns_forward).pack(
            side="left", padx=4)

        #  역방향 조회 (IP -> 도메인)
        ttk.Label(left, text="역방향 (IP -> Domain)").pack(anchor="w", pady=(2, 0))
        row_dns_rev = ttk.Frame(left)
        row_dns_rev.pack(fill="x", pady=2)

        # 역방향 조회를 위해 8.8.8.8 (Google DNS)을 기본값으로 설정
        self.var_dns_rev = tk.StringVar(value="8.8.8.8")
        ttk.Entry(row_dns_rev, textvariable=self.var_dns_rev,
                  width=25).pack(side="left", fill="x", expand=True)
        ttk.Button(row_dns_rev, text="조회", command=self.do_dns_reverse).pack(
            side="left", padx=4)

    # --- 기능 구현 ---

    def log(self, s):
        log_enter(self.out, s)

    def do_ipconfig(self):
        self.log(">>> IP 구성 확인")
        cmd = "ipconfig" if platform.system() == "Windows" else "ifconfig"
        try:
            res = subprocess.check_output(cmd, shell=True)
            try:
                text = res.decode('cp949')
            except:
                text = res.decode('utf-8', errors='ignore')
            self.log(text)
        except Exception as e:
            self.log(f"Error: {e}")

    def do_netstat(self):
        p = self.var_netstat.get()
        self.log(f">>> netstat 포트 {p} 확인")
        cmd = f"netstat -an | findstr :{p}" if platform.system(
        ) == "Windows" else f"netstat -an | grep :{p}"
        try:
            res = subprocess.check_output(cmd, shell=True)
            self.log(res.decode('utf-8', errors='ignore'))
        except:
            self.log("결과 없음 (Closed)")

    def do_check_port(self):
        h, p = self.var_host.get(), int(self.var_port.get())
        self.log(f">>> 연결 시도 {h}:{p}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((h, p))
            status = "Open (성공)" if result == 0 else f"Closed (실패, 코드={result})"
            self.log(f"결과: {status}")

    def do_hton(self):
        try:
            val_str = self.var_hton_val.get()
            val = int(val_str)

            n_val = socket.htons(val)
            h_val = socket.ntohs(n_val)

            self.log(f">>> 바이트 변환 테스트 (입력: {val})")
            self.log(f"Original: {val} (Hex: {hex(val)})")

            endian = "Little Endian" if sys.byteorder == 'little' else "Big Endian"
            self.log(f"System: {endian} <-> Network: Big Endian")

            self.log(f"htons() -> {n_val} (Hex: {hex(n_val)})")
            self.log(f"ntohs() -> {h_val} (Hex: {hex(h_val)})")

        except ValueError:
            self.log("[오류] 변환할 숫자를 입력하세요.")
        except Exception as e:
            self.log(f"[오류] {e}")

    def do_pton_v4(self):
        """IPv4 전용 pton"""
        ip_str = self.var_pton_v4.get().strip()
        self.log(f">>> [IPv4 pton] '{ip_str}' 변환")
        try:
            packed = socket.inet_pton(socket.AF_INET, ip_str)
            self.log(f"결과(Hex): {packed.hex()}")
            self.log(f"길이: {len(packed)} bytes (32 bit)")
        except OSError:
            self.log("[실패] 유효한 IPv4 형식이 아닙니다.")
        except Exception as e:
            self.log(f"[오류] {e}")

    def do_pton_v6(self):
        """IPv6 전용 pton"""
        ip_str = self.var_pton_v6.get().strip()
        self.log(f">>> [IPv6 pton] '{ip_str}' 변환")
        try:
            packed = socket.inet_pton(socket.AF_INET6, ip_str)
            self.log(f"결과(Hex): {packed.hex()}")
            self.log(f"길이: {len(packed)} bytes (128 bit)")
        except OSError:
            self.log("[실패] 유효한 IPv6 형식이 아닙니다.")
        except Exception as e:
            self.log(f"[오류] {e}")

    def do_dns_forward(self):
        """정방향 조회 (도메인 입력 -> IP 출력)"""
        domain = self.var_dns_fwd.get().strip()
        self.log(f">>> DNS 정방향 조회: {domain}")
        try:
            ip = socket.gethostbyname(domain)
            self.log(f"결과(IP): {ip}")
        except Exception as e:
            self.log(f"[실패] {e}")

    def do_dns_reverse(self):
        """역방향 조회 (IP 입력 -> 도메인 출력)"""
        target = self.var_dns_rev.get().strip()
        self.log(f">>> DNS 역방향 조회(PTR): {target}")
        try:
            # 입력값이 IP인지 확인
            try:
                socket.inet_aton(target)
                ip = target
            except:
                # IP가 아니면 DNS 조회를 통해 IP를 먼저 얻음
                self.log(f"(입력값이 도메인 같음 -> IP로 변환 시도)")
                ip = socket.gethostbyname(target)
                self.log(f"변환된 IP: {ip}")

            # 역방향 조회
            name, alias, addresslist = socket.gethostbyaddr(ip)
            self.log(f"결과(Domain): {name}")
            if alias:
                self.log(f"별칭: {alias}")

        except Exception as e:
            self.log(f"[실패] 호스트 정보를 찾을 수 없음: {e}")
