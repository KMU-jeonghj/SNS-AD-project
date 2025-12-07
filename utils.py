import tkinter as tk


def log_enter(widget, text):
    """로그 마다 개행하기"""
    try:
        widget.insert("end", text + "\n")
        widget.see("end")
    except:
        pass


def update_GUI(widget, func):
    """GUI 업데이트가 꼬이지 않게 순서대로 처리"""
    widget.after(0, func)
