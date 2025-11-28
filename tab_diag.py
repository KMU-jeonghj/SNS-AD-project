import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import platform
import socket
from utils import log_to_widget


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

        # IP Config
        ttk.Label(left, text="IP 구성 / netstat / 포트 검사").pack(anchor="w")
        ttk.Button(left, text="IP 구성 확인", command=self.do_ipconfig).pack(
            fill="x", pady=2)

        # Netstat
        self.var_netstat = tk.StringVar(value="9000")
        row = ttk.Frame(left)
        row.pack(fill="x", pady=2)
        ttk.Entry(row, textvariable=self.var_netstat,
                  width=10).pack(side="left")
        ttk.Button(row, text="netstat 필터", command=self.do_netstat).pack(
            side="left", padx=4)

        # Port Check
        row2 = ttk.Frame(left)
        row2.pack(fill="x", pady=(6, 2))
        self.var_host = tk.StringVar(value="127.0.0.1")
        self.var_port = tk.StringVar(value="9000")
        ttk.Entry(row2, textvariable=self.var_host, width=14).pack(side="left")
        ttk.Entry(row2, textvariable=self.var_port,
                  width=6).pack(side="left", padx=4)
        ttk.Button(row2, text="포트 오픈 검사", command=self.do_check_port).pack(
            side="left", padx=4)

        ttk.Separator(left).pack(fill="x", pady=8)

        # Byte/IP Utils
        ttk.Button(left, text="hton/ntoh 데모",
                   command=self.do_hton).pack(fill="x", pady=2)

        self.var_ipv4 = tk.StringVar(value="8.8.8.8")
        row3 = ttk.Frame(left)
        row3.pack(fill="x", pady=2)
        ttk.Entry(row3, textvariable=self.var_ipv4, width=18).pack(side="left")
        ttk.Button(row3, text="inet_pton(IPv4)",
                   command=self.do_inet4).pack(side="left", padx=4)

        # DNS
        ttk.Separator(left).pack(fill="x", pady=8)
        self.var_dns = tk.StringVar(value="google.com")
        row5 = ttk.Frame(left)
        row5.pack(fill="x", pady=2)
        ttk.Entry(row5, textvariable=self.var_dns, width=18).pack(side="left")
        ttk.Button(row5, text="DNS 조회", command=self.do_dns).pack(
            side="left", padx=4)

        self.out_diag = scrolledtext.ScrolledText(right, height=30)
        self.out_diag.pack(fill="both", expand=True)

    def log(self, s): log_to_widget(self.out_diag, s)

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
        self.log(f">>> netstat {p}")
        cmd = f"netstat -an -p tcp | findstr {p}" if platform.system(
        ) == "Windows" else f"netstat -an | grep {p}"
        try:
            res = subprocess.check_output(cmd, shell=True)
            self.log(res.decode('utf-8', errors='ignore'))
        except:
            self.log("결과 없음")

    def do_check_port(self):
        h, p = self.var_host.get(), int(self.var_port.get())
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            r = s.connect_ex((h, p))
            self.log(f"Port {p}: {'Open' if r==0 else 'Closed'}")

    def do_hton(self):
        v = 0x1234
        self.log(f"Orig: {hex(v)}, htons: {hex(socket.htons(v))}")

    def do_inet4(self):
        try:
            self.log(
                f"pton: {socket.inet_pton(socket.AF_INET, self.var_ipv4.get()).hex()}")
        except Exception as e:
            self.log(f"Error: {e}")

    def do_dns(self):
        try:
            self.log(f"DNS: {socket.gethostbyname(self.var_dns.get())}")
        except Exception as e:
            self.log(f"Error: {e}")
