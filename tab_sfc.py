import tkinter as tk
from tkinter import ttk, scrolledtext
import json
from utils import log_to_widget

# requests 유무 체크
try:
    import requests
    HAS_REQ = True
except:
    HAS_REQ = False


class SFCTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        self.var_url = tk.StringVar(value="http://127.0.0.1:8080")
        ttk.Label(top, text="Ryu URL").pack(side="left")
        ttk.Entry(top, textvariable=self.var_url,
                  width=25).pack(side="left", padx=5)
        ttk.Button(top, text="SFC 설치 (Demo)",
                   command=self.install_sfc).pack(side="left")

        self.out = scrolledtext.ScrolledText(self)
        self.out.pack(fill="both", expand=True)

    def log(self, s): log_to_widget(self.out, s)

    def install_sfc(self):
        if not HAS_REQ:
            self.log("Error: requests 모듈 없음 (pip install requests)")
            return

        url = self.var_url.get() + "/stats/flowentry/add"
        self.log(f">>> SFC 설치 요청: {url}")

        # 예제 플로우 데이터
        flow = {"dpid": 1, "priority": 100, "match": {
            "in_port": 1}, "actions": [{"port": 2}]}

        try:
            # 실제로는 류 컨트롤러가 켜져 있어야 함
            self.log(f"Data: {json.dumps(flow)}")
            # resp = requests.post(url, json=flow, timeout=1) # 실제 전송 시 주석 해제
            self.log("... (Ryu 연결 시 전송됨) ...")
        except Exception as e:
            self.log(f"전송 실패: {e}")
