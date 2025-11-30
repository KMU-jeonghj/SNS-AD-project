import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import threading
from utils import log_to_widget, safe_gui_update


class ServerTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # 서버 상태 변수
        self.server_socket = None
        self.server_running = False
        self.clients = []
        self.lock = threading.Lock()

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        self.var_port = tk.StringVar(value="9000")
        ttk.Label(top, text="포트").pack(side="left")
        ttk.Entry(top, textvariable=self.var_port,
                  width=6).pack(side="left", padx=4)

        self.var_broadcast = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="그림판 브로드캐스트", variable=self.var_broadcast).pack(
            side="left", padx=8)

        ttk.Button(top, text="서버 시작", command=self.server_start).pack(
            side="left", padx=4)
        ttk.Button(top, text="서버 정지", command=self.server_stop).pack(
            side="left", padx=4)

        stat = ttk.Frame(self, padding=8)
        stat.pack(fill="x")
        self.lbl_stat = ttk.Label(stat, text="접속: 0")
        self.lbl_stat.pack(side="left")

        self.out_srv = scrolledtext.ScrolledText(self, height=20)
        self.out_srv.pack(fill="both", expand=True)

    def log(self, s): log_to_widget(self.out_srv, s)

    def server_start(self):
        if self.server_running:
            return
        p = int(self.var_port.get())
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind(('', p))
            self.server_socket.listen(5)
            self.server_running = True
            threading.Thread(target=self._accept_loop, daemon=True).start()
            self.log(f"[서버] 시작 @ {p}")
        except Exception as e:
            self.log(f"Error: {e}")

    def server_stop(self):
        if not self.server_running:
            return
        self.server_running = False
        if self.server_socket:
            self.server_socket.close()
        self.clients = []
        self.log("[서버] 정지")

    def _accept_loop(self):
        while self.server_running:
            try:
                conn, addr = self.server_socket.accept()
                safe_gui_update(self, lambda: self.log(f"[접속] {addr}"))
                with self.lock:
                    self.clients.append((conn, addr))
                self._update_stat()
                threading.Thread(target=self._client_handler,
                                 args=(conn, addr), daemon=True).start()
            except:
                break

    def _client_handler(self, conn, addr):
        while self.server_running:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                text = data.decode('utf-8', errors='ignore')

                # 그림판 데이터 브로드캐스트
                if text.startswith("DRAW:") and self.var_broadcast.get():
                    self._broadcast(data, conn)
                else:
                    safe_gui_update(self, lambda: self.log(
                        f"[{addr}] {text.strip()}"))
            except:
                break

        with self.lock:
            if (conn, addr) in self.clients:
                self.clients.remove((conn, addr))
        conn.close()
        self._update_stat()
        safe_gui_update(self, lambda: self.log(f"[해제] {addr}"))

    def _broadcast(self, data, sender):
        with self.lock:
            for c, a in self.clients:
                if c != sender:
                    try:
                        c.sendall(data)
                    except:
                        pass

    def _update_stat(self):
        safe_gui_update(self.lbl_stat, lambda: self.lbl_stat.config(
            text=f"접속: {len(self.clients)}"))
