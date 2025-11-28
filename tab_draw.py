import tkinter as tk
from tkinter import ttk


class DrawTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()
        self._last_xy = None

    def _build_ui(self):
        info = ttk.Frame(self, padding=8)
        info.pack(fill="x")
        ttk.Label(info, text="그림판 - 접속 상태면 서버로 전송됨").pack(side="left")

        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)

        self.canvas.bind("<ButtonPress-1>", self._start)
        self.canvas.bind("<B1-Motion>", self._move)
        self.canvas.bind("<ButtonRelease-1>", self._end)

    def _start(self, e): self._last_xy = (e.x, e.y)
    def _end(self, e): self._last_xy = None

    def _move(self, e):
        if not self._last_xy:
            return
        x1, y1 = self._last_xy
        x2, y2 = e.x, e.y

        # 내 화면에 그리기
        self.canvas.create_line(x1, y1, x2, y2, width=2, capstyle="round")

        # 접속 중이면 서버로 전송 (App의 소켓 사용)
        if self.app.client_connected and self.app.client_socket:
            msg = f"DRAW:{x1},{y1},{x2},{y2}"
            try:
                self.app.client_socket.sendall(msg.encode())
            except:
                pass

        self._last_xy = (x2, y2)

    def draw_remote(self, text):
        """서버에서 받은 좌표 데이터로 그리기"""
        try:
            # 형식: DRAW:x1,y1,x2,y2
            coords = text.replace("DRAW:", "").strip().split(",")
            x1, y1, x2, y2 = map(int, coords)
            self.canvas.create_line(
                x1, y1, x2, y2, width=2, fill="red", capstyle="round")
        except:
            pass
