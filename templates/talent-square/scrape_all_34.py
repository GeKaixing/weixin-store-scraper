
import os
import tempfile
def get_temp_file(filename):
    return os.path.join(tempfile.gettempdir(), filename)
def get_desktop_path(sub_dir=None):
    base = os.path.join(os.path.expanduser("~"), "Desktop")
    return os.path.join(base, sub_dir) if sub_dir else base

"""
微信小店达人大广场 — 34类目全量一键爬取（含详情数据）
每个类目输出独立Excel到桌面，自动检测连续10页无新数据后停止
"""
# (This is a template reference — full content maintained at /tmp/scrape_all_34.py)
# To use: copy /tmp/scrape_all_34.py and run
