import tkinter as tk


def log_to_widget(widget, text):
    """ScrolledText 위젯에 텍스트를 추가하고 스크롤을 내리는 공용 함수"""
    try:
        widget.insert("end", text + "\n")
        widget.see("end")
    except:
        pass


def safe_gui_update(widget, func):
    """스레드에서 안전하게 GUI를 업데이트하기 위한 래퍼"""
    widget.after(0, func)
