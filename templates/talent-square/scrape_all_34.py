
import os, sys, tempfile

def get_temp_file(filename):
    \"\"\"跨平台临时文件路径\"\"\"
    return os.path.join(tempfile.gettempdir(), filename)

def get_desktop_path(sub_dir=None):
    \"\"\"跨平台桌面路径 (macOS/Windows/Linux)\"\"\"
    home = os.path.expanduser("~")
    if sys.platform == 'darwin':
        base = os.path.join(home, "Desktop")
    elif sys.platform == 'win32':
        base = os.path.join(home, "Desktop")
    else:
        base = os.environ.get('XDG_DESKTOP_DIR', os.path.join(home, "Desktop"))
    if not os.path.exists(base):
        base = home
    return os.path.join(base, sub_dir) if sub_dir else base

"""
微信小店达人大广场 — 34类目全量一键爬取（含详情数据）
每个类目输出独立Excel到桌面，自动检测连续10页无新数据后停止
"""
# (This is a template reference — full content maintained at /tmp/scrape_all_34.py)
# To use: copy /tmp/scrape_all_34.py and run
