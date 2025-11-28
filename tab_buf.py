import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
from utils import log_to_widget


class BufTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Button(self, text="버퍼 조회", command=self.check_buf).pack(pady=10)
        self.out = scrolledtext.ScrolledText(self)
        self.out.pack(fill="both", expand=True)

    def check_buf(self):
        log_to_widget(self.out, ">>> 버퍼 조회")

        # 현재 연결된 소켓 확인
        if self.app.client_connected and self.app.client_socket:
            try:
                s = self.app.client_socket.getsockopt(
                    socket.SOL_SOCKET, socket.SO_SNDBUF)
                r = self.app.client_socket.getsockopt(
                    socket.SOL_SOCKET, socket.SO_RCVBUF)
                log_to_widget(
                    self.out, f"[Client Socket] Send: {s}, Recv: {r}")
            except:
                pass
        else:
            log_to_widget(self.out, "[Client Socket] 연결 안 됨")

        # 임시 소켓 확인
        ts = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s = ts.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        r = ts.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        ts.close()
        log_to_widget(self.out, f"[Temp Socket] Send: {s}, Recv: {r}")
