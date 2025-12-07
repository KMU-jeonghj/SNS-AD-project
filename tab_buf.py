import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
from utils import log_enter


class BufTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(fill="x")

        # 클라이언트 소켓 조회
        ttk.Button(btn_frame, text="클라이언트 소켓 조회", command=self.check_client_socket).pack(
            side="left", fill="x", expand=True, padx=2)

        # 임시 소켓 조회
        ttk.Button(btn_frame, text="임시 소켓(OS 기본) 조회", command=self.check_temp_socket).pack(
            side="left", fill="x", expand=True, padx=2)

        # 로그
        self.out = scrolledtext.ScrolledText(self)
        self.out.pack(fill="both", expand=True)

    def check_client_socket(self):
        """현재 연결된 클라이언트 소켓의 버퍼 크기 확인"""
        log_enter(self.out, "\n>>> [1] 클라이언트 소켓 버퍼 조회")

        if self.app.client_connected and self.app.client_socket:
            try:
                sock = self.app.client_socket
                # SO_SNDBUF: 송신 버퍼, SO_RCVBUF: 수신 버퍼
                s = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
                r = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)

                log_enter(self.out, f"상태: 연결됨 (Connected)")
                log_enter(self.out, f"Send Buffer: {s} bytes")
                log_enter(self.out, f"Recv Buffer: {r} bytes")
            except Exception as e:
                log_enter(self.out, f"오류 발생: {e}")
        else:
            log_enter(self.out, "상태: 연결 안 됨")
            log_enter(self.out, "(먼저 'TCP 클라이언트' 탭에서 접속해주세요)")

    def check_temp_socket(self):
        """ 임시 소켓을 만들어 OS 기본 버퍼 크기 확인"""
        log_enter(self.out, "\n>>> [2] 임시 소켓(OS 기본값) 버퍼 조회")

        try:
            # 연결하지 않고 소켓 생성만 해도 버퍼는 할당됨
            ts = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s = ts.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
            r = ts.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
            ts.close()  # 확인 후 바로 닫음

            log_enter(self.out, f"상태: 임시 소켓 생성 성공")
            log_enter(self.out, f"Default Send: {s} bytes")
            log_enter(self.out, f"Default Recv: {r} bytes")
        except Exception as e:
            log_enter(self.out, f"오류 발생: {e}")
