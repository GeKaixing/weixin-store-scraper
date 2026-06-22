"""
合作管理 — 导出带货者信息 / 导出机构信息
从 store.weixin.qq.com/shop/shopleague/coop-manage 导出CSV/ZIP到桌面

用法:
  EXPORT_TYPE = "promoter"   # 导出带货者信息
  EXPORT_TYPE = "agency"     # 导出机构信息
"""

import os, time, tempfile

def get_temp_file(filename):
    return os.path.join(tempfile.gettempdir(), filename)
def get_desktop_path(sub_dir=None):
    base = os.path.join(os.path.expanduser("~"), "Desktop")
    return os.path.join(base, sub_dir) if sub_dir else base

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(SKILL_DIR, '..', '..', 'assets', 'weixin_store_state.json')

# ═══ 配置 ═══
EXPORT_TYPE = "promoter"  # "promoter" 或 "agency"
# ═══════════

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=STATE_PATH, viewport={'width': 1920, 'height': 1080},
                              accept_downloads=True)
    page = ctx.new_page()

    downloads = []
    page.on('download', lambda dl: downloads.append(dl))

    page.goto('https://store.weixin.qq.com/shop/shopleague/coop-manage', wait_until='domcontentloaded')
    time.sleep(5)

    # 关通知弹窗
    page.evaluate("""() => {
        const sr = document.querySelector('micro-app')?.shadowRoot;
        if(!sr) return;
        for(const e of sr.querySelectorAll('*')) {
            if(e.offsetParent === null) continue;
            if(e.textContent.trim() === '我知道了') {
                e.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
                break;
            }
        }
    }""")
    time.sleep(1)

    # 如果需要机构导出，先切tab
    if EXPORT_TYPE == "agency":
        page.evaluate("""() => {
            const sr = document.querySelector('micro-app')?.shadowRoot;
            if(!sr) return;
            for(const e of sr.querySelectorAll('*')) {
                if(e.offsetParent === null) continue;
                if(e.textContent.trim() === '机构管理' && e.className.includes('tab-item')) {
                    e.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
                    break;
                }
            }
        }""")
        time.sleep(3)

    # 点击导出按钮
    export_text = "导出带货者信息" if EXPORT_TYPE == "promoter" else "导出机构信息"
    page.evaluate(f"""((txt) => {{
        const sr = document.querySelector('micro-app')?.shadowRoot;
        if(!sr) return;
        for(const e of sr.querySelectorAll('span')) {{
            if(e.offsetParent === null) continue;
            if(e.textContent.trim().includes(txt)) {{
                ['mouseenter','mousedown','mouseup','click'].forEach(evt => {{
                    e.dispatchEvent(new MouseEvent(evt, {{bubbles:true, cancelable:true, view:window, button:0}}));
                }});
                break;
            }}
        }}
    }})('{export_text}')""")
    time.sleep(3)

    # 找dialog中"导出"按钮，用mouse.click（dispatchEvent对dialog无效）
    btn_pos = page.evaluate("""() => {
        const sr = document.querySelector('micro-app')?.shadowRoot;
        if(!sr) return null;
        for(const e of sr.querySelectorAll('*')) {
            if(e.offsetParent === null) continue;
            if(e.textContent.trim() === '导出') {
                const rect = e.getBoundingClientRect();
                return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
            }
        }
        return null;
    }""")

    if btn_pos:
        print(f'确认导出, 点击 ({btn_pos["x"]:.0f}, {btn_pos["y"]:.0f})', flush=True)
        page.mouse.click(btn_pos['x'], btn_pos['y'])
    else:
        print('❌ 未找到导出确认按钮', flush=True)
        page.screenshot(path='/tmp/export_fail.png')
        ctx.close()
        browser.close()
        exit(1)

    # 等待导出完成 + 自动下载
    label = "带货者" if EXPORT_TYPE == "promoter" else "机构"
    print(f'等待{label}导出完成...', flush=True)
    for i in range(30):
        time.sleep(1)
        if downloads:
            break
        status = page.evaluate(f"""((lb) => {{
            const sr = document.querySelector('micro-app')?.shadowRoot;
            if(!sr) return '';
            const seen = [];
            for(const e of sr.querySelectorAll('*')) {{
                if(e.offsetParent === null) continue;
                const t = e.textContent.trim();
                if(t && t.length < 60 && (t.includes('已导出') || t.includes('下载数据') || t.includes('成功'))) {{
                    seen.push(t);
                }}
            }}
            return [...new Set(seen)].join(' | ');
        }})('{label}')""")
        if status:
            print(f'  [{i+1}s] {status}', flush=True)

    if downloads:
        dl = downloads[0]
        fname = dl.suggested_filename or f'{label}列表_{time.strftime("%Y%m%d_%H%M%S")}.zip'
        fpath = get_desktop_path(fname)
        dl.save_as(fpath)
        print(f'✅ 下载成功: {fpath} ({os.path.getsize(fpath)} bytes)', flush=True)
    else:
        print('❌ 未捕获到下载', flush=True)
        page.screenshot(path='/tmp/export_no_dl.png')

    ctx.close()
    browser.close()
