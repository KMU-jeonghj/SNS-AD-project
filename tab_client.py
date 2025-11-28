import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import threading
import struct
from utils import log_to_widget, safe_gui_update


class ClientTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app  # App 인스턴스 (shared state)
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        self.var_host = tk.StringVar(value="127.0.0.1")
        self.var_port = tk.StringVar(value="9000")
        ttk.Entry(top, textvariable=self.var_host, width=14).pack(side="left")
        ttk.Entry(top, textvariable=self.var_port,
                  width=6).pack(side="left", padx=4)
        ttk.Button(top, text="접속", command=self.connect).pack(
            side="left", padx=4)
        ttk.Button(top, text="해제", command=self.disconnect).pack(
            side="left", padx=4)

        opt = ttk.Frame(self, padding=8)
        opt.pack(fill="x")
        self.var_mode = tk.StringVar(value="VAR")
        ttk.Radiobutton(opt, text="VAR", variable=self.var_mode,
                        value="VAR").pack(side="left")
        ttk.Radiobutton(opt, text="FIXED", variable=self.var_mode,
                        value="FIXED").pack(side="left", padx=6)
        ttk.Radiobutton(opt, text="MIX", variable=self.var_mode,
                        value="MIX").pack(side="left", padx=6)

        msg = ttk.Frame(self, padding=8)
        msg.pack(fill="x")
        self.var_msg = tk.StringVar(value="hello")
        ttk.Entry(msg, textvariable=self.var_msg, width=40).pack(side="left")
        ttk.Button(msg, text="전송", command=self.send_msg).pack(
            side="left", padx=6)

        self.out_cli = scrolledtext.ScrolledText(self, height=20)
        self.out_cli.pack(fill="both", expand=True)

    def log(self, s): log_to_widget(self.out_cli, s)

    def connect(self):
        if self.app.client_connected:
            return
        try:
            # 소켓 생성 및 App에 저장 (공유 목적)
            self.app.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.app.client_socket.connect(
                (self.var_host.get(), int(self.var_port.get())))
            self.app.client_connected = True

            threading.Thread(target=self._recv_loop, daemon=True).start()
            self.log("[클라] 연결 성공")
        except Exception as e:
            self.log(f"연결 실패: {e}")

    def disconnect(self):
        if not self.app.client_connected:
            return
        try:
            self.app.client_socket.close()
        except:
            pass
        self.app.client_connected = False
        self.app.client_socket = None
        self.log("[클라] 연결 해제")

    def _recv_loop(self):
        while self.app.client_connected:
            try:
                data = self.app.client_socket.recv(1024)
                if not data:
                    break
                text = data.decode('utf-8', errors='ignore')

                if text.startswith("DRAW:"):
                    # 그림판 탭에 그리기 요청
                    if hasattr(self.app, 'tab_draw'):
                        safe_gui_update(
                            self, lambda: self.app.tab_draw.draw_remote(text))
                else:
                    safe_gui_update(self, lambda: self.log(f"[수신] {text}"))
            except:
                break
        self.app.client_connected = False

    def send_msg(self):
        if not self.app.client_connected:
            return
        try:
            m = self.var_msg.get().encode('utf-8')
            mode = self.var_mode.get()
            if mode == "VAR":
                d = m + b"\n"
            elif mode == "FIXED":
                d = m[:32].ljust(32, b'\0')
            else:
                d = struct.pack("!I", len(m)) + m

            self.app.client_socket.sendall(d)
            self.log(f"[송신] {self.var_msg.get()}")
        except Exception as e:
            self.log(f"전송 실패: {e}")
