import tkinter as tk
from tkinter import ttk, messagebox

# 분리한 모듈들 import
from tab_diag import DiagTab
from tab_server import ServerTab
from tab_client import ClientTab
from tab_draw import DrawTab
from tab_buf import BufTab
from tab_sfc import SFCTab


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("스마트 네트워크 서비스")
        self.geometry("1100x750")

        # --- 공용 상태 변수 (서로 다른 탭끼리 공유할 데이터) ---
        self.client_socket = None
        self.client_connected = False

        # --- 탭 구성 ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # 각 탭 생성 및 추가 (self를 넘겨서 App의 변수에 접근하게 함)
        self.tab_diag = DiagTab(self.notebook, self)
        self.notebook.add(self.tab_diag, text="네트워크 진단")

        self.tab_server = ServerTab(self.notebook, self)
        self.notebook.add(self.tab_server, text="TCP 서버")

        self.tab_client = ClientTab(self.notebook, self)
        self.notebook.add(self.tab_client, text="TCP 클라이언트")

        self.tab_buf = BufTab(self.notebook, self)
        self.notebook.add(self.tab_buf, text="버퍼/소켓")

        self.tab_draw = DrawTab(self.notebook, self)
        self.notebook.add(self.tab_draw, text="네트워크 그림판")

        self.tab_sfc = SFCTab(self.notebook, self)
        self.notebook.add(self.tab_sfc, text="Ryu SFC")


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"실행 중 오류: {e}")
