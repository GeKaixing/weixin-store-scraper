
import os
import tempfile
def get_temp_file(filename):
    return os.path.join(tempfile.gettempdir(), filename)
def get_desktop_path(sub_dir=None):
    base = os.path.join(os.path.expanduser("~"), "Desktop")
    return os.path.join(base, sub_dir) if sub_dir else base

from playwright.sync_api import sync_playwright
import json, time, math
from datetime import datetime

# Load existing list data
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(SKILL_DIR, '..', '..', 'assets', 'weixin_store_state.json')
with open(STATE_PATH) as f:
    state = json.load(f)

with open(get_temp_file('weixin_agency_all_data.json')) as f:
    all_items = json.load(f)

print(f"总机构数: {len(all_items)}")

# Progress cache file — separate from main list data
progress_path = get_temp_file('weixin_agency_detail_progress.json')
detail_map = {}  # ilinkUserId -> detail dict

try:
    with open(progress_path) as f:
        detail_map = json.load(f)
    print(f"已有详情缓存: {len(detail_map)} 条")
except:
    pass

# Filter items that still need detail
pending = [item for item in all_items if item['ilinkUserId'] and item['ilinkUserId'] not in detail_map]
print(f"还需抓取: {len(pending)} 条")

if not pending:
    print("全部已完成，直接生成 Excel")
else:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(storage_state=state, viewport={'width': 1400, 'height': 900})
        page = ctx.new_page()

        page.goto('https://store.weixin.qq.com/shop/ec-agency/market/home',
                  wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(3000)

        BATCH = 10  # concurrent requests per batch
        total_pending = len(pending)
        start_time = time.time()

        for batch_start in range(0, total_pending, BATCH):
            batch = pending[batch_start:batch_start + BATCH]
            batch_ids = [item['ilinkUserId'] for item in batch]
            ids_json = json.dumps(batch_ids)

            try:
                results = page.evaluate(f"""async () => {{
                    const ids = {ids_json};
                    const results = await Promise.all(ids.map(async (id) => {{
                        try {{
                            const resp = await fetch(
                                'https://store.weixin.qq.com/shop-faas/mmeckolnode/square/getGetAgencySquareDetail?lang=zh_CN',
                                {{
                                    method: 'POST',
                                    credentials: 'include',
                                    headers: {{'Content-Type': 'application/json'}},
                                    body: JSON.stringify({{ilinkUserId: id}})
                                }}
                            );
                            const data = await resp.json();
                            if (data.code === 0 && data.data?.detail) {{
                                const d = data.data.detail;
                                return {{
                                    ilinkUserId: id,
                                    entityName: d.baseInfo?.entityName || '',
                                    settledTime: d.baseInfo?.settledTime || 0,
                                    outerContactWay: d.baseInfo?.outerContactWay || '',
                                    outerWechatId: d.baseInfo?.outerWechatId || '',
                                    shopDsrScore: d.coreData?.shopDsrScore || 0,
                                    shopDsrScoreLevel: d.coreData?.shopDsrScoreLevel || ''
                                }};
                            }}
                            return {{ilinkUserId: id, error: 'no detail'}};
                        }} catch(e) {{
                            return {{ilinkUserId: id, error: e.message || String(e)}};
                        }}
                    }}));
                    return results;
                }}""")
            except Exception as e:
                print(f"  ⚠ 浏览器错误，等3秒重试... {e}")
                time.sleep(3)
                continue

            for r in results:
                if 'error' not in r:
                    detail_map[r['ilinkUserId']] = r

            elapsed = time.time() - start_time
            done = len(detail_map)
            rate = done / elapsed if elapsed > 0 else 0
            remaining = (total_pending - done + len(batch)) / max(rate, 0.1)

            # Save progress periodically (every 100 batches = ~1000 records)
            if batch_start % 100 == 0 or batch_start + BATCH >= total_pending:
                print(f"  {done}/{total_pending}条 | {rate:.1f}条/秒 | 预计剩余{int(remaining/60)}分钟")
                with open(progress_path, 'w') as f:
                    json.dump(detail_map, f, ensure_ascii=False)

            time.sleep(0.3)

        # Final save
        with open(progress_path, 'w') as f:
            json.dump(detail_map, f, ensure_ascii=False)

        total_time = time.time() - start_time
        print(f"\n✅ 详情抓取完成！{len(detail_map)} 条，耗时 {int(total_time/60)}分{int(total_time%60)}秒")
        browser.close()

# Merge detail data into all_items
print("\n合并数据...")
for item in all_items:
    uid = item.get('ilinkUserId', '')
    if uid in detail_map:
        d = detail_map[uid]
        item['主体名称'] = d.get('entityName', '')
        item['微信号'] = d.get('outerWechatId', '')
        item['手机号码'] = d.get('outerContactWay', '')
        item['平均店铺评分'] = d.get('shopDsrScore', 0)
        item['评分等级'] = d.get('shopDsrScoreLevel', '')
        ts = d.get('settledTime', 0)
        item['入住时间'] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts else ''
    else:
        for k in ('主体名称', '微信号', '手机号码', '评分等级', '入住时间'):
            item[k] = ''
        item['平均店铺评分'] = 0

# Save Excel
import openpyxl
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "带货机构列表"

headers = ['机构名称', '擅长行业', '动销带货者数', '动销商品数', '动销店铺数',
           '带货销售额', '平均佣金率', '平均店铺评分', '合作热招品牌数',
           '主体名称', '微信号', '手机号码', '入住时间', '机构详情链接']
ws.append(headers)

for item in all_items:
    ws.append([item.get(h, '') for h in headers])

for col in ws.columns:
    max_len = 0
    col_letter = col[0].column_letter
    for cell in col:
        if cell.value:
            max_len = max(max_len, len(str(cell.value)))
    ws.column_dimensions[col_letter].width = min(max_len + 4, 60)

output_path = 'get_desktop_path() + os.sep带货机构列表.xlsx'
wb.save(output_path)
print(f"📁 Excel: {output_path}")
print(f"📁 JSON (progress): {progress_path}")
print(f"\n字段数: {len(headers)}")
print(f"含评分的机构: {sum(1 for item in all_items if item.get('平均店铺评分', 0) > 0)}")
print(f"含微信号的机构: {sum(1 for item in all_items if item.get('微信号', ''))}")
print(f"含手机号的机构: {sum(1 for item in all_items if item.get('手机号码', ''))}")
print(f"含主体名称的机构: {sum(1 for item in all_items if item.get('主体名称', ''))}")