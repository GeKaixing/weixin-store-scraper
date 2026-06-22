
import os
import tempfile
def get_temp_file(filename):
    return os.path.join(tempfile.gettempdir(), filename)
def get_desktop_path(sub_dir=None):
    base = os.path.join(os.path.expanduser("~"), "Desktop")
    return os.path.join(base, sub_dir) if sub_dir else base

from playwright.sync_api import sync_playwright
import json, time

INDUSTRY_MAP = {
    1: "服饰家居", 2: "玉翠文玩", 3: "食品生鲜", 4: "个护美妆",
    5: "图书课程", 6: "数码家电", 7: "家清日用", 8: "家装建材",
    9: "宠物绿植", 10: "母婴玩具", 11: "本地生活", 12: "会员充值",
    13: "教育培训", 14: "汽摩电动"
}
DETAIL_URL_TPL = "https://store.weixin.qq.com/shop/ec-agency/market/detail?id={ilinkUserId}&type=SUPPLIER"
JSON_BACKUP = get_temp_file('weixin_agency_all_data.json')
EXCEL_OUTPUT = get_desktop_path('带货机构列表.xlsx')

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(SKILL_DIR, '..', '..', 'assets', 'weixin_store_state.json')
with open(STATE_PATH) as f:
    state = json.load(f)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=state, viewport={'width': 1400, 'height': 900})
    page = ctx.new_page()

    page.goto('https://store.weixin.qq.com/shop/ec-agency/market/home', wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(3000)

    with open(JSON_BACKUP) as f:
        all_items = json.load(f)

    print(f"已有 {len(all_items)} 条，从 offset={len(all_items)} 续抓")

    limit = 200
    offset = len(all_items)
    max_total = 22463

    while offset < max_total:
        result = page.evaluate(f"""async () => {{
            const resp = await fetch(
                'https://store.weixin.qq.com/shop-faas/mmeckolnode/square/getSearchSupplierAgencyList?lang=zh_CN',
                {{
                    method: 'POST',
                    credentials: 'include',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{orderType: 1, limit: {limit}, offset: {offset}}})
                }}
            );
            const data = await resp.json();
            if (data.code !== 0) return {{error: data.message || 'code=' + data.code}};
            return {{items: data.data.itemList || [], totalNum: data.data.totalNum}};
        }}""")

        if 'error' in result:
            print(f"  出错: {result['error']}，等5秒重试...")
            time.sleep(5)
            continue

        items = result['items']
        if not items:
            print("  空数据，结束")
            break

        for item in items:
            industries = [INDUSTRY_MAP.get(ind.get('id'), f"未知({ind.get('id')})") for ind in item.get('industryInfos', [])]
            ilink_id = item.get('ilinkUserId', '')
            all_items.append({
                '机构名称': item.get('name', ''),
                '擅长行业': '、'.join(industries),
                '动销带货者数': item.get('payFuinCnt', 0),
                '动销商品数': item.get('paySpuCnt', 0),
                '动销店铺数': item.get('shopCnt', 0),
                '带货销售额': item.get('payAmountToStr', ''),
                '平均佣金率': item.get('avgCommissionRate', 0),
                '合作热招品牌数': item.get('hotBrandCnt', 0),
                '机构详情链接': DETAIL_URL_TPL.format(ilinkUserId=ilink_id) if ilink_id else '',
                'ilinkUserId': ilink_id,
                'appid': item.get('appid', '')
            })

        offset += len(items)
        print(f"  offset={offset} → {len(items)}条 | 累计{len(all_items)}条")
        time.sleep(0.5)

    print(f"\n最终完成：{len(all_items)} 条")

    with open(JSON_BACKUP, 'w') as f:
        json.dump(all_items, f, ensure_ascii=False)

    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "带货机构列表"
    headers = ['机构名称', '擅长行业', '动销带货者数', '动销商品数', '动销店铺数',
               '带货销售额', '平均佣金率', '合作热招品牌数', '机构详情链接']
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
    wb.save(EXCEL_OUTPUT)
    print(f"Excel: {EXCEL_OUTPUT}")

    browser.close()
