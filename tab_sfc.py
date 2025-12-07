import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
from utils import log_enter

# requests 모듈
try:
    import requests
    HAS_REQ = True
except ImportError:
    HAS_REQ = False


class SFCTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        panel = ttk.Frame(self, padding=10)
        panel.pack(fill="x")

        #  Ryu 주소 및 DPID/Priority 설정
        self.var_rest_host = tk.StringVar(value="127.0.0.1")
        self.var_rest_port = tk.StringVar(value="8080")
        self.var_dpid = tk.StringVar(value="1")
        self.var_prio = tk.StringVar(value="100")

        row1 = ttk.Frame(panel)
        row1.pack(fill="x", pady=2)

        ttk.Label(row1, text="Ryu Host:").pack(side="left")
        ttk.Entry(row1, textvariable=self.var_rest_host,
                  width=12).pack(side="left", padx=2)
        ttk.Label(row1, text="Port:").pack(side="left")
        ttk.Entry(row1, textvariable=self.var_rest_port,
                  width=5).pack(side="left", padx=2)

        ttk.Label(row1, text="DPID:").pack(side="left", padx=(10, 0))
        ttk.Entry(row1, textvariable=self.var_dpid,
                  width=5).pack(side="left", padx=2)
        ttk.Label(row1, text="Prio:").pack(side="left")
        ttk.Entry(row1, textvariable=self.var_prio,
                  width=5).pack(side="left", padx=2)

        # 기본값: h1(1번) -> fw(2번) -> nat(3번) -> h2(4번)
        self.var_h1 = tk.StringVar(value="1")
        self.var_fw = tk.StringVar(value="2")
        self.var_nat = tk.StringVar(value="3")
        self.var_h2 = tk.StringVar(value="4")

        row2 = ttk.Frame(panel)
        row2.pack(fill="x", pady=5)

        ports_frame = ttk.Frame(row2)
        ports_frame.pack(side="left")

        ttk.Label(ports_frame, text="h1(In):").grid(row=0, column=0, padx=2)
        ttk.Entry(ports_frame, textvariable=self.var_h1,
                  width=4).grid(row=0, column=1, padx=2)

        ttk.Label(ports_frame, text="fw:").grid(row=0, column=2, padx=2)
        ttk.Entry(ports_frame, textvariable=self.var_fw,
                  width=4).grid(row=0, column=3, padx=2)

        ttk.Label(ports_frame, text="nat:").grid(row=0, column=4, padx=2)
        ttk.Entry(ports_frame, textvariable=self.var_nat,
                  width=4).grid(row=0, column=5, padx=2)

        ttk.Label(ports_frame, text="h2(Out):").grid(row=0, column=6, padx=2)
        ttk.Entry(ports_frame, textvariable=self.var_h2,
                  width=4).grid(row=0, column=7, padx=2)

        row3 = ttk.Frame(panel)
        row3.pack(fill="x", pady=5)

        ttk.Button(row3, text="SFC 설치",
                   command=self.sfc_install).pack(side="left", padx=2)
        ttk.Button(row3, text="바이패스",
                   command=self.sfc_bypass).pack(side="left", padx=2)
        ttk.Button(row3, text="플로우 조회", command=self.sfc_get_flows).pack(
            side="left", padx=2)
        ttk.Button(row3, text="플로우 삭제",
                   command=self.sfc_delete).pack(side="left", padx=2)

        # 로그창
        self.out = scrolledtext.ScrolledText(self, height=15)
        self.out.pack(fill="both", expand=True, padx=5, pady=5)

    def log(self, s): log_enter(self.out, s)

    def get_base_url(self):
        return f"http://{self.var_rest_host.get()}:{self.var_rest_port.get()}"

    def add_flow(self, match, actions):
        if not HAS_REQ:
            self.log("Error: requests 모듈 없음")
            return

        url = self.get_base_url() + "/stats/flowentry/add"
        dpid = int(self.var_dpid.get())
        prio = int(self.var_prio.get())

        # flow table
        payload = {
            "dpid": dpid,
            "cookie": 1,
            "cookie_mask": 1,
            "table_id": 0,
            "priority": prio,
            "flags": 1,
            "match": match,
            "actions": actions
        }

        try:
            resp = requests.post(url, json=payload, timeout=2)
            if resp.status_code == 200:
                self.log(f"[설치 성공] Match={match} -> Action={actions}")
            else:
                self.log(f"[실패] {resp.status_code} {resp.text}")
        except Exception as e:
            self.log(f"[에러] {e}")

    # --- 기능 구현 ---

    def sfc_install(self):
        """SFC 체이닝: h1 -> fw -> nat -> h2 순서"""
        self.log(f"\n>>> SFC 설치 (h1->fw->nat->h2)")

        h1 = int(self.var_h1.get())
        fw = int(self.var_fw.get())
        nat = int(self.var_nat.get())
        h2 = int(self.var_h2.get())

        # Flow modification
        self.add_flow(match={"in_port": h1}, actions=[
            {"type": "OUTPUT", "port": fw}])

        self.add_flow(match={"in_port": fw}, actions=[
            {"type": "OUTPUT", "port": nat}])

        self.add_flow(match={"in_port": nat}, actions=[
            {"type": "OUTPUT", "port": h2}])

    def sfc_bypass(self):
        """바이패스: 중간 장비 무시하고 h1 -> h2 바로 연결"""
        self.log(f"\n>>> 바이패스 설치 (h1 -> h2 직결)")

        h1 = int(self.var_h1.get())
        h2 = int(self.var_h2.get())

        # 바로 h2 로 포워딩
        self.add_flow(match={"in_port": h1}, actions=[
            {"type": "OUTPUT", "port": h2}])

    def sfc_get_flows(self):
        """현재 스위치에 설치된 플로우 조회"""
        if not HAS_REQ:
            return

        dpid = self.var_dpid.get()
        url = self.get_base_url() + f"/stats/flow/{dpid}"
        self.log(f"\n>>> 플로우 조회: {url}")

        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                # 보기 좋게 JSON 정렬해서 출력
                formatted = json.dumps(data, indent=2)
                self.log(formatted)
            else:
                self.log(f"[조회 실패] {resp.status_code}")
        except Exception as e:
            self.log(f"[에러] {e}")

    def sfc_delete(self):
        """모든 플로우 삭제 (초기화)"""
        if not HAS_REQ:
            return

        dpid = self.var_dpid.get()
        url = self.get_base_url() + f"/stats/flowentry/clear/{dpid}"
        self.log(f"\n>>> 플로우 전체 삭제 요청")

        try:
            # delete 메소드 사용
            resp = requests.delete(url, timeout=2)
            if resp.status_code == 200:
                self.log("모든 플로우가 초기화되었습니다.")
            else:
                self.log(f"[실패] {resp.status_code} {resp.text}")
        except Exception as e:
            self.log(f"[에러] {e}")
