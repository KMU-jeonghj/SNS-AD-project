import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import threading
import struct
from utils import log_enter, update_GUI


class ClientTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        self.var_host = tk.StringVar(value="127.0.0.1")
        self.var_port = tk.StringVar(value="9000")

        ttk.Label(top, text="IP:").pack(side="left")
        ttk.Entry(top, textvariable=self.var_host,
                  width=14).pack(side="left", padx=2)
        ttk.Label(top, text="Port:").pack(side="left")
        ttk.Entry(top, textvariable=self.var_port,
                  width=6).pack(side="left", padx=2)

        ttk.Button(top, text="접속", command=self.connect).pack(
            side="left", padx=4)
        ttk.Button(top, text="해제", command=self.disconnect).pack(
            side="left", padx=4)

        # 전송 옵션 영역 (라디오 버튼 + 체크박스)
        opt = ttk.LabelFrame(self, text="전송 옵션", padding=8)
        opt.pack(fill="x", padx=5, pady=5)

        self.var_mode = tk.StringVar(value="VAR")

        # 가변 길이
        ttk.Radiobutton(opt, text="VAR (가변, \\n)", variable=self.var_mode,
                        value="VAR").pack(side="left", padx=4)

        # 고정 길이
        ttk.Radiobutton(opt, text="FIXED (32byte)", variable=self.var_mode,
                        value="FIXED").pack(side="left", padx=4)

        # 고정 + 가변
        ttk.Radiobutton(opt, text="MIX (4byte + Data)", variable=self.var_mode,
                        value="MIX").pack(side="left", padx=4)

        # 전송 후 종료 체크박스
        self.var_send_close = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt, text="전송 후 종료", variable=self.var_send_close).pack(
            side="right", padx=4)

        # 메시지 입력 및 전송
        msg_frame = ttk.Frame(self, padding=8)
        msg_frame.pack(fill="x")

        self.var_msg = tk.StringVar(value="hello")
        ttk.Entry(msg_frame, textvariable=self.var_msg).pack(
            side="left", fill="x", expand=True, padx=4)
        ttk.Button(msg_frame, text="전송",
                   command=self.send_msg).pack(side="right")

        self.out = scrolledtext.ScrolledText(self, height=15)
        self.out.pack(fill="both", expand=True, padx=5, pady=5)

    def log(self, s):
        log_enter(self.out, s)

    def connect(self):
        if self.app.client_connected:
            return

        host = self.var_host.get()
        try:
            port = int(self.var_port.get())
        except ValueError:
            self.log("[오류] 포트는 숫자여야 합니다.")
            return

        try:
            self.app.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.app.client_socket.connect((host, port))
            self.app.client_connected = True

            self.log(f"[클라] 서버({host}:{port}) 접속 성공")

            # 수신 스레드 시작
            threading.Thread(target=self._recv_loop, daemon=True).start()
        except Exception as e:
            self.log(f"[오류] 접속 실패: {e}")

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
        """서버로부터 데이터를 받는 스레드"""
        while self.app.client_connected:
            try:
                data = self.app.client_socket.recv(1024)
                if not data:  # 연결 끊김
                    break

                text = data.decode('utf-8', errors='replace')

                # 그림판 기능
                if text.startswith("DRAW:") and hasattr(self.app, 'tab_draw'):
                    update_GUI(
                        self.out, lambda: self.app.tab_draw.draw_remote(text))
                else:
                    update_GUI(self.out, lambda: self.log(f"[수신] {text}"))
            except OSError:
                break  # 소켓이 닫히면 종료
            except Exception as e:
                update_GUI(self.out, lambda: self.log(f"[수신 오류] {e}"))
                break

        self.app.client_connected = False
        update_GUI(self.out, lambda: self.log("[알림] 서버와 연결이 끊어졌습니다."))

    def send_msg(self):
        if not self.app.client_connected:
            self.log("[오류] 서버에 연결되어 있지 않습니다.")
            return

        raw_msg = self.var_msg.get()
        mode = self.var_mode.get()
        socket_data = b""  # 최종적으로 보내는 소켓 데이터는 바이트 처리

        try:
            # 메시지를 바이트로 변환
            payload = raw_msg.encode('utf-8')

            # 모드 별 분기
            if mode == "VAR":
                # 가변 길이: 뒤에 \n 추가
                socket_data = payload + b'\n'
                log_text = f"[VAR] {raw_msg} (길이:{len(socket_data)})"

            elif mode == "FIXED":
                # 고정 길이: 32바이트
                fixed_len = 32
                if len(payload) > fixed_len:
                    socket_data = payload[:fixed_len]
                else:
                    # 짧으면 null로 채움
                    socket_data = payload + b'\x00' * \
                        (fixed_len - len(payload))
                log_text = f"[FIXED] {raw_msg} (길이:{len(socket_data)}bytes)"

            elif mode == "MIX":
                # MIX
                # 네트워크 바이트이므로 !I 로 표기 (unsignedInt, 4bytes)
                prefix = struct.pack('!I', len(payload))
                socket_data = prefix + payload
                log_text = f"[MIX] prefix(4b) + {raw_msg}({len(payload)})"

            self.app.client_socket.sendall(socket_data)
            self.log(log_text)
            self.var_msg.set("")  # 입력창 비우기

            # 전송 후 연결 종료
            if self.var_send_close.get():
                self.log("전송 후 종료 옵션에 의해 연결을 해제합니다.")
                self.disconnect()

        except Exception as e:
            self.log(f"[오류] 전송 실패: {e}")
