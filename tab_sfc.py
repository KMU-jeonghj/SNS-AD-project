import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
from utils import log_to_widget

# requests 모듈 체크
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
        # --- 상단 컨트롤 패널 (스켈레톤 UI 구조 반영) ---
        panel = ttk.Frame(self, padding=10)
        panel.pack(fill="x")

        # 1행: Ryu 주소 및 DPID/Priority 설정
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

        # 2행: 포트 매핑 (SFC 경로 설정용)
        # 기본값: h1(1번) -> fw(2번) -> nat(3번) -> h2(4번)
        self.var_h1 = tk.StringVar(value="1")
        self.var_fw = tk.StringVar(value="2")
        self.var_nat = tk.StringVar(value="3")
        self.var_h2 = tk.StringVar(value="4")

        row2 = ttk.Frame(panel)
        row2.pack(fill="x", pady=5)

        # Grid 레이아웃으로 포트 입력 배치 (스켈레톤 스타일)
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

        # 3행: 버튼들 (설치, 바이패스, 조회, 삭제)
        row3 = ttk.Frame(panel)
        row3.pack(fill="x", pady=5)

        ttk.Button(row3, text="SFC 설치 (Chain)",
                   command=self.sfc_install).pack(side="left", padx=2)
        ttk.Button(row3, text="바이패스 (Direct)",
                   command=self.sfc_bypass).pack(side="left", padx=2)
        ttk.Button(row3, text="플로우 조회", command=self.sfc_dump).pack(
            side="left", padx=2)
        ttk.Button(row3, text="플로우 삭제 (Reset)",
                   command=self.sfc_delete).pack(side="left", padx=2)

        # --- 하단 로그창 ---
        self.out = scrolledtext.ScrolledText(self, height=15)
        self.out.pack(fill="both", expand=True, padx=5, pady=5)

    def log(self, s): log_to_widget(self.out, s)

    def get_base_url(self):
        return f"http://{self.var_rest_host.get()}:{self.var_rest_port.get()}"

    def send_flow(self, match, actions):
        if not HAS_REQ:
            self.log("Error: requests 모듈 없음")
            return

        url = self.get_base_url() + "/stats/flowentry/add"
        dpid = int(self.var_dpid.get())
        prio = int(self.var_prio.get())

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
        """SFC 체이닝: h1 -> fw -> nat -> h2 순서로 강제 이동"""
        self.log(f"\n>>> SFC 설치 (h1->fw->nat->h2)")

        h1 = int(self.var_h1.get())
        fw = int(self.var_fw.get())
        nat = int(self.var_nat.get())
        h2 = int(self.var_h2.get())

        # Flow 1: Host1에서 오면 -> 방화벽(fw)으로 보내라
        self.send_flow(match={"in_port": h1}, actions=[{"port": fw}])

        # Flow 2: 방화벽(fw)에서 오면 -> NAT로 보내라 (여기서는 단순 포트 포워딩으로 구현)
        self.send_flow(match={"in_port": fw}, actions=[{"port": nat}])

        # Flow 3: NAT에서 오면 -> Host2(목적지)로 보내라
        self.send_flow(match={"in_port": nat}, actions=[{"port": h2}])

    def sfc_bypass(self):
        """바이패스: 중간 장비 무시하고 h1 -> h2 바로 연결"""
        self.log(f"\n>>> 바이패스 설치 (h1 -> h2 직결)")

        h1 = int(self.var_h1.get())
        h2 = int(self.var_h2.get())

        # 중간 단계(fw, nat) 무시하고 바로 목적지로 쏨
        self.send_flow(match={"in_port": h1}, actions=[{"port": h2}])

    def sfc_dump(self):
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
        # 모든 플로우를 지우는 명령
        url = self.get_base_url() + f"/stats/flowentry/clear/{dpid}"
        self.log(f"\n>>> 플로우 전체 삭제 요청")

        try:
            # delete 메소드 사용
            resp = requests.delete(url, timeout=2)
            if resp.status_code == 200:
                self.log("[삭제 성공] 모든 규칙이 초기화되었습니다.")
            else:
                self.log(f"[실패] {resp.status_code} {resp.text}")
        except Exception as e:
            self.log(f"[에러] {e}")
