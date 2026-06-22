
import os
import tempfile
def get_temp_file(filename):
    return os.path.join(tempfile.gettempdir(), filename)
def get_desktop_path(sub_dir=None):
    base = os.path.join(os.path.expanduser("~"), "Desktop")
    return os.path.join(base, sub_dir) if sub_dir else base

"""补爬缺失的详情数据 — 用于网络断连后恢复"""
import asyncio, json, os
from playwright.async_api import async_playwright

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(SKILL_DIR, "..", "..", "assets", "weixin_store_state.json")
TEMP_JSON = get_temp_file("weixin_pass1_data.json")

# 详情页字段解析 JS (同 scrape_v11_onepass.py 中的 DETAIL_PARSE_JS)
DETAIL_PARSE_JS = """
() => {
    function getText(el) {
        if (!el || el.tagName === 'STYLE' || el.tagName === 'SCRIPT') return '';
        let text = '';
        for (const node of el.childNodes) {
            if (node.nodeType === 3) { const t = node.textContent.trim(); if (t) text += t + '\\n'; }
            else if (node.nodeType === 1) text += getText(node);
        }
        return text;
    }
    const sr = document.querySelector('micro-app')?.shadowRoot;
    const root = sr || document;
    const body = root.querySelector('body') || root;
    const raw = getText(body);
    const lines = raw.split('\\n').map(l => l.trim()).filter(l => l);
    function valAfter(label) {
        for (let i = 0; i < lines.length; i++)
            if (lines[i] === label && i + 1 < lines.length) return lines[i + 1];
        return '';
    }
    const 总销量 = valAfter('总销量');
    const 跟买人数 = valAfter('跟买人数');
    const 回头客 = valAfter('回头客');
    let 品类占比 = '';
    { const si = lines.indexOf('品类占比');
      if (si !== -1) {
        const pairs = [];
        for (let i = si + 1; i < lines.length; i++) {
          const l = lines[i];
          if (['带货概览','粉丝特征','直播带货','短视频带货','带货渠道'].includes(l)) break;
          if (i + 1 < lines.length && lines[i+1].endsWith('%')) {
            pairs.push(l + ' ' + lines[i+1]); i++;
          }
        }
        品类占比 = pairs.join(', ');
      }
    }
    let 带货销售额='', 客单价='', 粉丝数带货概览='', 直播占比='';
    { const si = lines.indexOf('带货概览');
      if (si !== -1) {
        for (let i = si + 1; i < lines.length && i < si + 20; i++) {
          const l = lines[i];
          if (['粉丝特征','品类占比','带货渠道','直播带货','短视频带货'].includes(l)) break;
          if (l === '带货销售额' && i+1 < lines.length) 带货销售额 = lines[i+1];
          else if (l === '客单价' && i+1 < lines.length) 客单价 = lines[i+1];
          else if (l === '粉丝数' && i+1 < lines.length) 粉丝数带货概览 = lines[i+1];
          else if (l === '直播' && i+1 < lines.length) 直播占比 = lines[i+1];
        }
      }
    }
    let 粉丝性别='', 粉丝年龄='', 粉丝地域='', 粉丝人群类别='', 粉丝购物偏好='';
    { const si = lines.indexOf('粉丝特征');
      if (si !== -1) {
        for (let i = si + 1; i < lines.length && i < si + 30; i++) {
          const l = lines[i];
          if (['直播带货','带货渠道','品类占比','带货概览','购买力区间'].includes(l)) break;
          if (l === '性别' && i+3 < lines.length) 粉丝性别 = lines[i+1] + ' ' + lines[i+3];
          else if (l === '年龄' && i+3 < lines.length) 粉丝年龄 = lines[i+1] + ' ' + lines[i+3];
          else if (l === '地域' && i+3 < lines.length) 粉丝地域 = lines[i+1] + ' ' + lines[i+3];
          else if (l === '人群类别' && i+3 < lines.length) 粉丝人群类别 = lines[i+1] + ' ' + lines[i+3];
          else if (l === '购物偏好' && i+3 < lines.length) 粉丝购物偏好 = lines[i+1] + ' ' + lines[i+3];
        }
      }
    }
    let 带货渠道 = '';
    { const si = lines.indexOf('带货渠道');
      if (si !== -1) {
        const kept = [];
        const skip = ['微信扫码','联系','打开微信','扫码入群','邀请带货','恭喜',
          '互相感兴趣','未留下联系方式','昨日','近7日','近30日','直播明细','直播信息',
          '直播观看人数','带货商品','带货片段','下一页','跳转','评分','达人详情','找达人',
          '带货概览','粉丝特征','品类占比','直播带货','短视频带货'];
        for (let i = si + 1; i < lines.length; i++) {
          const l = lines[i];
          if (skip.some(p => l.includes(p))) break;
          if (l.length > 1 && !/^\\d+$/.test(l) && !l.includes('%') && !l.startsWith('￥')) kept.push(l);
        }
        带货渠道 = kept.join('; ');
      }
    }
    return {总销量,跟买人数,回头客,品类占比,带货销售额,客单价,粉丝数带货概览,直播占比,
            粉丝性别,粉丝年龄,粉丝地域,粉丝人群类别,粉丝购物偏好,带货渠道};
}
"""

async def main():
    if not os.path.exists(TEMP_JSON):
        print("❌ 找不到 get_temp_file("weixin_pass1_data.json")")
        return
    with open(TEMP_JSON) as f:
        all_talents = json.load(f)
    missing = [(i, t['达人详情链接'], t['昵称'])
               for i, t in enumerate(all_talents)
               if t.get('达人详情链接') and not t.get('总销量')]
    total_all = len(all_talents)
    print(f"总条数: {total_all}, 待补爬: {len(missing)}")
    if not missing:
        print("全部已完成"); return
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(storage_state=STATE_PATH, viewport={"width":1920,"height":1080})
        for idx, (orig_idx, url, name) in enumerate(missing):
            full_url = url if url.startswith('http') else 'https://store.weixin.qq.com' + url
            try:
                dp = await ctx.new_page()
                await dp.goto(full_url, wait_until="domcontentloaded", timeout=20000)
                await asyncio.sleep(3)
                data = await dp.evaluate(DETAIL_PARSE_JS)
                for k, v in data.items(): all_talents[orig_idx][k] = v
                await dp.close()
                print(f"  [{idx+1}/{len(missing)}] ✓ {name[:20]}", flush=True)
            except Exception as e:
                print(f"  [{idx+1}/{len(missing)}] ✗ {name[:20]}: {str(e)[:40]}", flush=True)
            if (idx + 1) % 20 == 0:
                with open(TEMP_JSON, 'w') as f: json.dump(all_talents, f, ensure_ascii=False)
        await browser.close()
    with open(TEMP_JSON, 'w') as f: json.dump(all_talents, f, ensure_ascii=False)
    done = sum(1 for t in all_talents if t.get('总销量'))
    print(f"补爬完成: {done}/{total_all}")

if __name__ == '__main__':
    asyncio.run(main())
