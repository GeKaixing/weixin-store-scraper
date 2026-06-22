
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

from playwright.sync_api import sync_playwright
import json, time
import openpyxl

INDUSTRY_MAP = {
    1: "服饰家居", 2: "玉翠文玩", 3: "食品生鲜", 4: "个护美妆",
    5: "图书课程", 6: "数码家电", 7: "家清日用", 8: "家装建材",
    9: "宠物绿植", 10: "母婴玩具", 11: "本地生活", 12: "会员充值",
    13: "教育培训", 14: "汽摩电动"
}

DETAIL_URL_TPL = "https://store.weixin.qq.com/shop/ec-agency/market/detail?id={ilinkUserId}&type=SUPPLIER"
JSON_BACKUP = get_temp_file('weixin_agency_all_data.json')
EXCEL_OUTPUT = get_desktop_path('带货机构列表.xlsx')

ORDER_TYPE = 1       # 1=综合, 2=动销带货者数, 3=动销商品数, 4=热招品牌数
FETCH_DETAIL = False

with open(STATE_PATH) as f:
    state = json.load(f)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=state, viewport={'width': 1400, 'height': 900})
    page = ctx.new_page()

    print("正在登录会话...")
    page.goto('https://store.weixin.qq.com/shop/ec-agency/market/home', wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(3000)
    print("登录完成，开始抓取数据")

    all_items = []
    start_time = time.time()
    limit = 200
    offset = 0
    total_num = None
    page_count = 0

    while True:
        page_count += 1
        result = page.evaluate(f"""async () => {{
            const resp = await fetch(
                'https://store.weixin.qq.com/shop-faas/mmeckolnode/square/getSearchSupplierAgencyList?lang=zh_CN',
                {{
                    method: 'POST',
                    credentials: 'include',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{orderType: {ORDER_TYPE}, limit: {limit}, offset: {offset}}})
                }}
            );
            const data = await resp.json();
            if (data.code !== 0) return {{error: data.message || 'code=' + data.code}};
            return {{items: data.data.itemList || [], totalNum: data.data.totalNum}};
        }}""")

        if 'error' in result:
            print(f"  第{page_count}页出错: {result['error']}，等5秒重试...")
            time.sleep(5)
            continue

        items = result['items']
        if total_num is None:
            total_num = result.get('totalNum', 0)
            print(f"  总条数: {total_num}")

        if not items:
            print(f"  第{page_count}页空数据，结束")
            break

        for item in items:
            industries = [INDUSTRY_MAP.get(ind.get('id'), f"未知({ind.get('id')})") for ind in item.get('industryInfos', [])]
            ilink_id = item.get('ilinkUserId', '')
            entry = {
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
            }
            all_items.append(entry)

        offset += len(items)
        elapsed = time.time() - start_time
        if total_num:
            pct = offset / total_num * 100
            print(f"  第{page_count}页 (offset={offset}/{total_num}) → {len(items)}条 | 累计{len(all_items)}条 ({pct:.1f}%) | {elapsed:.0f}s")
        else:
            print(f"  第{page_count}页 (offset={offset}) → {len(items)}条 | 累计{len(all_items)}条 | {elapsed:.0f}s")

        time.sleep(0.3)

    elapsed = time.time() - start_time
    print(f"\n列表数据完成！{len(all_items)} 条，耗时 {elapsed:.0f} 秒")

    if FETCH_DETAIL and all_items:
        print("\n开始抓取详情数据...")
        detail_start = time.time()
        detail_count = 0
        for i, entry in enumerate(all_items):
            if 'shopDsrScore' in entry:
                continue
            ilink_id = entry.get('ilinkUserId', '')
            if not ilink_id:
                continue
            detail = page.evaluate(f"""async () => {{
                const resp = await fetch(
                    'https://store.weixin.qq.com/shop-faas/mmeckolnode/square/getGetAgencySquareDetail?lang=zh_CN',
                    {{
                        method: 'POST',
                        credentials: 'include',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{ilinkUserId: '{ilink_id}'}})
                    }}
                );
                const data = await resp.json();
                if (data.code === 0 && data.data?.detail?.coreData) {{
                    return data.data.detail.coreData;
                }}
                return null;
            }}""")
            if detail:
                entry['平均店铺评分'] = detail.get('shopDsrScore', '')
                entry['评分等级'] = detail.get('shopDsrScoreLevel', '')
            else:
                entry['平均店铺评分'] = ''
                entry['评分等级'] = ''
            detail_count += 1
            if detail_count % 200 == 0:
                print(f"  详情进度: {detail_count}/{len(all_items)} ({detail_count/len(all_items)*100:.1f}%)")
                time.sleep(0.5)

        detail_elapsed = time.time() - detail_start
        print(f"  详情完成！{detail_count} 条，耗时 {detail_elapsed:.0f} 秒")

    with open(JSON_BACKUP, 'w') as f:
        json.dump(all_items, f, ensure_ascii=False)
    print(f"JSON 备份: {JSON_BACKUP}")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "带货机构列表"

    headers = ['机构名称', '擅长行业', '动销带货者数', '动销商品数', '动销店铺数',
               '带货销售额', '平均佣金率', '合作热招品牌数', '机构详情链接']
    if FETCH_DETAIL:
        headers += ['平均店铺评分', '评分等级']

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
