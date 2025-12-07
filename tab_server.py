import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import threading
import time
from utils import log_enter, update_GUI


class ServerTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # 공유 데이터
        self.server_socket = None
        self.clients = []           # 클라이언트 리스트
        self.client_count = 0       # 클라이언트 카운터

        # 동기화 도구 (Lock, Event)
        self.lock = threading.Lock()        # 임계영역 lock
        self.stop_event = threading.Event()  # 안전 종료 신호용 이벤트

        self._build_ui()

    def _build_ui(self):
        # 상단 컨트롤 패널 (포트, 시작, 정지)
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        self.var_port = tk.StringVar(value="9000")
        ttk.Label(top, text="Port:").pack(side="left")
        ttk.Entry(top, textvariable=self.var_port,
                  width=6).pack(side="left", padx=4)

        self.var_broadcast = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="그림판 브로드캐스트", variable=self.var_broadcast).pack(
            side="left", padx=8)

        ttk.Button(top, text="서버 시작", command=self.server_start).pack(
            side="left", padx=2)
        ttk.Button(top, text="서버 정지", command=self.server_stop).pack(
            side="left", padx=2)

        stat = ttk.Frame(self, padding=5)
        stat.pack(fill="x")

        # 접속자 수 (리스트 길이)
        self.lbl_clients = ttk.Label(
            stat, text="접속: 0")
        self.lbl_clients.pack(side="left", padx=5)

        # 공유 카운터 (정수 변수)
        self.lbl_counter = ttk.Label(stat, text="카운터: 0")
        self.lbl_counter.pack(side="left", padx=12)

        # 이벤트 상태 표시
        self.lbl_event = ttk.Label(stat, text="상태: 정지")
        self.lbl_event.pack(side="left", padx=12)

        # 상태 갱신 버튼
        ttk.Button(stat, text="상태 갱신",
                   command=self.server_status).pack(side="left")

        # 3. 로그창
        self.out = scrolledtext.ScrolledText(self, height=15)
        self.out.pack(fill="both", expand=True, padx=5, pady=5)

    def log(self, s):
        log_enter(self.out, s)

    def server_status(self):
        """버튼 클릭 시 공유 자원(Lock)을 읽어 UI 라벨 업데이트"""

        #  임계영역 진입
        if self.lock.acquire(blocking=True, timeout=1.0):
            try:
                cnt = self.client_count
                lst_len = len(self.clients)

                self.lbl_clients.config(text=f"접속: {lst_len}")
                self.lbl_counter.config(text=f"카운터: {cnt}")

            finally:
                self.lock.release()  # 락 해제
        else:
            self.log("[오류] Lock 획득 실패 (Deadlock 의심)")

        # 이벤트(Event) 상태 확인
        if self.stop_event.is_set():
            self.lbl_event.config(text="상태: 정지")
        elif self.server_socket:
            self.lbl_event.config(
                text="상태: 실행 중")
        else:
            self.lbl_event.config(text="상태: 대기")

    def server_start(self):
        if not self.stop_event.is_set() and self.server_socket:
            return

        try:
            port = int(self.var_port.get())
            self.server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', port))
            self.server_socket.listen(5)

            self.stop_event.clear()  # 이벤트 초기화 (실행 상태)

            with self.lock:
                self.client_count = 0
                self.clients.clear()

            self.log(f"[서버] 포트 {port}에서 시작되었습니다.")
            self.server_status()  # 상태 UI 갱신

            threading.Thread(target=self._accept_loop, daemon=True).start()

        except Exception as e:
            self.log(f"[오류] 서버 시작 실패: {e}")

    def server_stop(self):
        self.stop_event.set()  # 이벤트 발생 (종료 신호)

        try:
            if self.server_socket:
                self.server_socket.close()
        except:
            pass

        with self.lock:
            for conn, addr in self.clients:
                try:
                    conn.close()
                except:
                    pass
            self.clients.clear()
            self.client_count = 0

        self.log("[서버] 종료되었습니다.")
        self.server_status()  # 종료 후 상태 UI 갱신

    def _accept_loop(self):
        while not self.stop_event.is_set():
            try:
                self.server_socket.settimeout(1.0)
                try:
                    # 클라이언트의 소켓 객체와 주소 저장
                    conn, addr = self.server_socket.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break

                self.app.server_client_socket = conn

                # [임계영역] 접속자 증가
                with self.lock:
                    self.clients.append((conn, addr))
                    self.client_count += 1

                update_GUI(self.out, lambda: self.log(f"[접속] {addr}"))

                # 접속 시 자동으로 상태창 갱신 (선택 사항)
                # update_GUI(self.out, self.server_status)

                threading.Thread(target=self._client_handler,
                                 args=(conn, addr), daemon=True).start()

            except Exception as e:
                if not self.stop_event.is_set():
                    update_GUI(self.out, lambda: self.log(f"[Accept 오류] {e}"))
                break

    def _client_handler(self, conn, addr):
        while not self.stop_event.is_set():
            try:
                conn.settimeout(1.0)
                try:
                    data = conn.recv(1024)
                except socket.timeout:
                    continue

                if not data:
                    break

                recv_len = len(data)
                text_decoded = data.decode(
                    'utf-8', errors='replace').strip('\x00').strip()

                if text_decoded.startswith("DRAW:") and self.var_broadcast.get():
                    self._broadcast(data, conn)
                else:
                    update_GUI(self.out, lambda: self.log(
                        f"[{addr}] Len:{recv_len}B | Msg: {text_decoded}"))
            except:
                break

        # [임계영역] 접속자 감소
        with self.lock:
            if (conn, addr) in self.clients:
                self.clients.remove((conn, addr))
                self.client_count -= 1

        try:
            conn.close()
        except:
            pass

        update_GUI(self.out, lambda: self.log(f"[해제] {addr}"))
        # 해제 시 자동으로 상태창 갱신
        # update_GUI(self.out, self.server_status)

    def _broadcast(self, data, sender):
        with self.lock:
            for c, a in self.clients:
                if c != sender:
                    try:
                        c.sendall(data)
                    except:
                        pass
