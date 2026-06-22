---
name: weixin-store-scraper
category: social-media
description: Scrape data from 微信小店 (WeChat Store) — includes 达人广场 (talent square) and 机构广场 (agency market). Handles Playwright session auth, micro-app shadow DOM, Vue SPA, API pagination, and Excel output.
platforms: [macos, linux, windows]
---

# 微信小店 Scraper

Scrape structured data from 微信小店 store.weixin.qq.com — both the 达人广场 (talent square) and 机构广场 (agency market / 带货机构). Handles session auth, micro-app shadow DOM, Vue SPA interactions, direct API pagination, and Excel delivery.

## Shared Prerequisites

- WeChat login session at `assets/weixin_store_state.json` (relative to skill directory, Playwright `storage_state`)
- Python 3.9+ with `playwright`
- Playwright browsers installed: `playwright install chromiu

## Session State

Persistent login state is stored **inside the skill** at `assets/weixin_store_state.json`. Templates should resolve this path relative to the skill directory. Example:

```python
import os
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(SKILL_DIR, '..', '..', 'assets', 'weixin_store_state.json')
```

## Shared User Preferences

- **Execute first, don't show code** — the user says "不需要编写脚本". Run scripts directly, deliver Excel on Desktop. Do not display code/script content.
- **Excel output** → Desktop (via `get_desktop_path()`)
- **Save JSON backup** before generating Excel (resume from breakpoint)
- **Progress files** in temp dir (via `get_temp_file()`) for resumption
- **Long-running jobs** use background mode with `notify_on_complete=True`, then send WeChat DM completion notification to `weixin:o9cq807VdcwVNBW2iw06V0elNJUM@im.wechat`
- **Contact filter** — `FILTER_HAS_CONTACT = True/False` 是否筛选有联系方式（**默认开启**）。重要：pass1 开启此选项后，列表页只显示已公开联系方式的达人，pass2 才能捕获到 roomId，pass3 才能提取到联系方式。关闭此选项会导致 pass3 大量 "暂无联系方式"（实测差异：开启后 10/10 条全部有联系方式，关闭后 0/10）。联系方式不能通过正则从全页文本提取（会误抓左侧会话列表中的其他微信号），只能依靠 pass3 的 `.contact-popover` 流程。
- **Excel output has fixed 41-column layout**

## Cross-Platform Compatibility

All templates include these cross-platform helper functions at the top:

```python
import os, tempfile, sys

def get_temp_file(filename):
    \"\"\"跨平台临时文件路径\"\"\"
    return os.path.join(tempfile.gettempdir(), filename)

def get_desktop_path(sub_dir=None):
    \"\"\"跨平台桌面路径 (macOS/Windows/Linux)\"\"\"
    home = os.path.expanduser("~")
    if sys.platform == 'darwin':       # macOS
        base = os.path.join(home, "Desktop")
    elif sys.platform == 'win32':      # Windows
        base = os.path.join(home, "Desktop")
    else:                               # Linux (XDG 约定)
        base = os.environ.get('XDG_DESKTOP_DIR',
                              os.path.join(home, "Desktop"))
    if not os.path.exists(base):
        base = home  # 回退到用户目录
    return os.path.join(base, sub_dir) if sub_dir else base

def get_platform_ua():
    \"\"\"跨平台 User-Agent\"\"\"
    if sys.platform == 'darwin':
        return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    elif sys.platform == 'win32':
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    else:
        return 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
```

- **`get_temp_file(name)`** — returns platform temp path (Windows: `C:\\Users\\<user>\\AppData\\Local\\Temp\\name`, macOS/Linux: `/tmp/name`)
- **`get_desktop_path(sub_dir)`** — returns Desktop path (macOS: `~/Desktop`, Windows: `~/Desktop`, Linux: `$XDG_DESKTOP_DIR` or `~/Desktop`, fallback to `~` when Desktop doesn't exist)
- **`get_platform_ua()`** — returns a platform-specific User-Agent string for HTTP requests
- **`STATE_PATH`** — resolved relative to skill `assets/` directory, not hardcoded

## Shared Patterns

### Session Handling

```python
import os
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(SKILL_DIR, '..', '..', 'assets', 'weixin_store_state.json')
with open(STATE_PATH) as f:
    state = json.load(f)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(storage_state=state, viewport={'width': 1400, 'height': 900})
    page = ctx.new_page()
```

### Resume from Breakpoint

- Save progress to a JSON cache file (via `get_temp_file()`) after every N pages/batches
- On restart: load existing data, skip already-processed items
- Progress files: `get_temp_file('weixin_*_progress.json')`

### Excel Delivery

```python
import openpyxl
wb = openpyxl.Workbook()
ws = wb.active
# ... write headers and data rows ...
# Avoid '/' in headers — use '、' instead
fp = get_desktop_path(f"微信小店达人数据(DOM)/达人_{category}_{label}.xlsx")
os.makedirs(os.path.dirname(fp), exist_ok=True)
wb.save(fp)
```

---

## Section A: 达人广场 (Talent Square)

Scrape talents from `store.weixin.qq.com/shop/findersquare/find`. The page uses micro-app + Vue SPA with shadow DOM — complex interaction model.

**Key challenges:**
- Data in shadow DOM table (not API accessible with quality)
- 详情 links hidden behind `javascript:void(0)` + `window.open` — must capture via override
- Three-pass architecture:
  - Pass 1 = list + URL capture (window.open override, no tab opens)
  - Pass 2 = detail page scrape via `page.goto`, click 短视频带货 tab via `page.mouse.click`, then **click 联系 button → capture roomId from popup URL**
  - Pass 3 = batch open `collab/im?roomId={roomId}` pages → click matching session by `[data-room-id]` → click "查看联系方式" → extract 微信号+手机号 from `.contact-popover__item` only (NO regex fallback on full page text!)
- **Detail fields (41 columns)**: sorted as: 头像, 昵称, 带货类目1/2/3(列表页拆3列), 评分, 粉丝数(列表), 带货销售总额, 短视频销售额, 回复率高, 有认证, 可开发票, 达人详情链接, 总销量, 跟买人数, 回头客, 品类占比, 带货销售额, 客单价, 粉丝数带货概览, 直播占比, 粉丝性别, 粉丝年龄, 粉丝地域, 粉丝人群类别, 粉丝购物偏好, 购买力区间, 带货渠道, 直播销售额, 场均成交额, 场均观看人数, 总带货场次, 直播明细, 视频销售额, 条均成交额, 条均点赞数, 总带货条数, 短视频明细, 微信号, 手机号, im链接
- Category filtering via UI checkbox toggle (not API topCatId — quality is poor)
- **Contact filter** — `FILTER_HAS_CONTACT = True/False` 是否筛选有联系方式（**默认开启**）。参见 Shared User Preferences 中的说明：开启后 pass1 只采集已公开联系方式的达人，确保 pass3 能提取到联系方式。
- Pagination via native value setter on input box + 跳转 button
- dispatchEvent preferred for Vue v-model interactions (checkboxes, dropdowns), but page.mouse.click required for channel tabs (直播带货/短视频带货) and dialog confirm buttons (导出弹窗等)
- Page was redesigned 2026-05-12 (new card grid layout)

**References and templates:** `references/talent-square/`, `templates/talent-square/`

**Recommended template:** `templates/talent-square/scrape_v11_onepass.py` (two-pass + roomId capture + imLink导出)

**Post-process template:** `templates/talent-square/scrape_pass3_contact.py` (pass3 — extract 微信号/手机号 from collab/im pages, 输出含im链接)

### Reference Files

| File | Contents |
|------|----------|
| `references/talent-square/category_ids.md` | 34 category IDs + label nth-child index table |
| `references/talent-square/data-quality-pitfalls.md` | Known data quality issues |
| `references/talent-square/detail-page-fields.md` | Detail page field parsing rules & verified samples |
| `references/talent-square/detail-fields-36cols.md` | Full 41-column field reference (含联系方式+im链接+类目拆分) |
| `references/talent-square/detail-url-capture.md` | URL capture double-path fix & detail page text structure |
| `references/talent-square/dispatchevent-pattern.md` | dispatchEvent interaction pattern details |
| `references/talent-square/page-redesign-20260512.md` | 2026-05-12 page redesign report |
| `references/talent-square/pagination-investigation-20260511.md` | Pagination failure investigation |
| `references/talent-square/resume-scrape.md` | Detail scrape resume instructions |
| `references/talent-square/session-20260511.md` | May 2026 page state snapshot |
| `references/talent-square/content-extension-dom-patterns.md` | Chrome extension DOM extraction patterns & field-adding workflow |\n| `references/talent-square/contact-extraction.md` | Pass3 collab/im page DOM structure & contact extraction flow |\n| `references/talent-square/three-pass-contact-filter-workflow.md` | Three-pass workflow: why FILTER_HAS_CONTACT must be True, 10/10 verified |

### Template Files

| File | Contents |
|------|----------|
| `templates/talent-square/scrape_v11_onepass.py` | **Recommended** two-pass template (pass1=列表, pass2=详情+roomId+im链接) |
| `templates/talent-square/scrape_pass3_contact.py` | **New** Pass3: 从roomId构造collab/im链接, 提取微信号+手机号, 输出含im链接 |
| `templates/talent-square/scrape_all_34.py` | Scrape all 34 categories |
| `templates/talent-square/resume_detail_scrape.py` | Resume interrupted detail scrape |

### Scripts

| File | Contents |
|------|----------|
| `scripts/talent-square/check_page_state.py` | Quick diagnostic: check if page is old table or new card grid |

---

## Section B: 机构广场 (Agency Market / 带货机构)

Scrape supplier agencies from `store.weixin.qq.com/shop/ec-agency/market/home`. Uses direct API calls with session auth — no shadow-DOM or infinite-scroll needed.

**Key characteristics:**
- Data via backend API (not DOM scraping): `getSearchSupplierAgencyList` + `getGetAgencySquareDetail`
- Two tiers: Tier 1 = list API only (6 fields, ~100s for all 22K items), Tier 2 = detail API (one call per agency, ~12-15 min with 10 concurrent requests)
- Industry ID mapping (14 categories, IDs 1-14)
- 9-column Excel output: 机构名称, 擅长行业, 动销带货者数, 动销商品数, 动销店铺数, 带货销售额, 平均佣金率, 合作热招品牌数, 机构详情链接

**References and templates:** `references/agency-market/`, `templates/agency-market/`

### Reference Files

| File | Contents |
|------|----------|
| `references/agency-market/api-endpoints.md` | Full API endpoint URLs, request/response schemas |
| `references/agency-market/industry-mapping.md` | 14 industry categories with Chinese names |
| `references/agency-market/session-details.md` | Session snapshots and observed data counts |

### Template Files

| File | Contents |
|------|----------|
| `templates/agency-market/scrape_agency_list.py` | Full scraper: paginate list API + save Excel |
| `templates/agency-market/scrape_agency_detail.py` | Detail scrape with 10-concurrent batch pattern |
| `templates/agency-market/resume_agency.py` | Resume interrupted scrape from JSON backup |

---

## Section C: 商品列表 (Goods List)

Scrape all products from `store.weixin.qq.com/shop/goods/list`. Uses direct API call (`scanProductPreview`) with session auth — no browser needed once `biz_magic` is extracted from storage_state.

**Key characteristics:**
- API URL: `POST .../mmchannelstradeproductcore/cgi/goods/scanProductPreview?token=&lang=zh_CN`
- Auth via `biz_magic` header (from cookie in `weixin_store_state.json`)
- Pagination with `pageSize=20` (max), `pageNum` iteration
- Returns ~80 fields per product (title, price, stock, SKUs, images, params, etc.)
- 21-column Excel output: 商品ID, SPU编码, 商品名称, 副标题, 价格(元), 最高价(元), 总库存, 总销量, 总订单数, 总曝光量, 状态, 子状态, 上架时间, 编辑时间, 品牌, SKU数, 商品类型, 类目ID, 发货方式, 主图, 销售渠道

**Recommended template:** `templates/goods-list/scrape_goods_list.py`

### Reference Files

| File | Contents |
|------|----------|
| `references/goods-list/api-reference.md` | API endpoint, auth mechanism, request/response schema |

### Template Files

| File | Contents |
|------|----------|
| `templates/goods-list/scrape_goods_list.py` | Full scraper: paginate API + save JSON + Excel |

## Section D: 合作管理 (Cooperation Management)

Export promoter/agency lists from `store.weixin.qq.com/shop/shopleague/coop-manage`. Uses native export buttons (ZIP/CSV download) — not DOM scraping.

**Key characteristics:**
- URL: `https://store.weixin.qq.com/shop/shopleague/coop-manage`
- Two tabs: **带货者管理** (promoter) and **机构管理** (agency)
- Each tab has an "导出XX信息" button with a confirmation dialog
- Uses `page.mouse.click` for dialog confirm button (dispatchEvent doesn't work on dialog)
- ZIP file auto-downloads after ~4s (no need to click "下载数据")

**Export flow:**
1. Dismiss notification dialog ("我知道了")
2. Click `span` containing "导出带货者信息" or "导出机构信息" (dispatchEvent OK)
3. Wait for confirmation dialog → find "导出" button → `page.mouse.click()` (required)
4. Wait ~4s → ZIP auto-downloads

**Template:** `templates/coop-manage/export_coop.py`

## Pitfalls

1. **Session expiration** — After ~100 rapid API calls or extended idle time, session may throttle. Add `time.sleep(0.3)` between pages and retry on error.
2. **Agency detail API name has double "get"**: `getGetAgencySquareDetail` — not `getSupplierAgencyDetail` (404).
3. **Talent square 详情 URL 双路径 bug** — `window.open` overridden callback returns an absolute path (`/shop/findersquare/finder-detail?…`). Prepend ONLY `'https://store.weixin.qq.com'` — **NOT** `'https://store.weixin.qq.com/shop/findersquare/'` (creates double path → 404). Fix in both `get_list_data_with_urls()` JS and `pass2()` Python URL assembly.
4. **Talent square category filters** — Open real tabs pollutes Vue state, breaking pagination. Use `window.open` override (returns dummy window object) in Pass 1.
5. **Talent square checkbox interaction** — CSS positions checkboxes off-screen (x=-133310). Must use `dispatchEvent` with all three events: `click`, `change`, `input` for Vue v-model to update.
6. **Talent square page structure** — Page may be redesigned. Run `scripts/talent-square/check_page_state.py` first to detect version.
7. **Industry ID mapping** — IDs 1-14. Unknown IDs should be preserved as `"未知({id})"`.
8. **Excel title with '/':** — openpyxl rejects `/` in sheet names. Replace with `、`。
9. **WeCom smart table uses Canvas rendering** — The enterprise WeChat smart table (doc.weixin.qq.com smartsheet) renders column headers as Canvas pixels, not DOM text nodes. DOM-based header scanning (querySelectorAll, querySelectorAllDeep) cannot detect column labels. The content extension's `dispatchPaste` approach relies on fixed column order + tab-separated values, not dynamic header alignment.
10. **Preference for Native CLI (Obscura)** — While this skill provides a Playwright template for complex UI (Shadow DOM), the user strongly prefers native `obscura fetch --eval` for simple endpoints. Only use Playwright templates when Shadow DOM/SPA complexity is unavoidable.
11. **Dialog confirm buttons need mouse.click()** — WeChat SPA dialogs (export confirm, blacklist, etc.) do NOT respond to `dispatchEvent` clicks. Must use `page.mouse.click(x, y)` with coordinates from `getBoundingClientRect()` to trigger their event handlers.
14. **短视频带货tab需要mouse.click** — Vue channel-tab组件不响应dispatchEvent, 必须用`page.mouse.click()`获取坐标后点击。
15. **Shadow DOM text extraction双保险** — `document.body.innerText` 无法穿透 `<micro-app>` 的 shadow DOM，但自定义 `getText()` 在某些页面结构异常时只返回 <10行。必须在两个 JS 解析块（`DETAIL_PARSE_JS` 和 `sv_data evaluate`）中使用双保险策略：先用 `getText(shadowRoot.body)`，如果行数 <10 则 fallback 到 `document.body.innerText`。
15. **直播明细解析** — 行组结构为`标题/日期/时长/观看数/等/N/件`(7行一组)。当详情页无直播数据时直播明细为空, 不报错。
16. **联系方式 roomId 捕获 (Pass2)** — 详情页的"联系"按钮用 Vue 绑定, dispatchEvent 无效。必须用 `page.mouse.click()` 配合坐标, 且必须用 `ctx.on('page')` 监听 popup (page.on('popup') 不可靠)。无"联系"按钮的达人: 超时后静默跳过, 不报错。
17. **Pass3 必须先点左侧会话** — 直接打开 `collab/im?roomId=X` 不会自动选中该会话。必须用 `[data-room-id]` 找到匹配的 `LI.session-item-container` 并 click(), 等待5s加载右侧面板, 再点击 contact-link。
18. **联系方式只能从 contact-popover 提取** — 禁止在全页文本中用正则搜索微信号。collab/im 页面左侧会话列表包含大量非当前达人的微信号 (如"jackey"), 正则会误抓。只从 `.contact-popover__title`(含"带货者联系方式") + `.contact-popover__value` 提取。
22. **每日查看次数上限** — 微信小店对商家每天查看达人联系方式的次数有限制。检测到"今天查看达人联系方式次数已达上限"时跳过(skip=True), 不修改数据, 次日重新跑。
23. **页面泄漏 → EPIPE 崩溃** — 所有模板在循环中使用 `ctx.new_page()` 后必须关闭页面。未关闭的页面会累积占用浏览器内存，Python 3.9 + Playwright 在 macOS 上 ~8-10 个页面后会崩溃报 `write EPIPE`。修复：用 `try/finally` 或 `try/finally/close()` 保证每个 page 关闭。已在 `scrape_pass3_contact.py` 和 `scrape_v11_onepass.py` 中修复（2026-06-21 pass3 测试验证通过），其他模板如 `scrape_all_34.py`、`resume_detail_scrape.py` 也应检查。
24. **增量保存防止 EPIPE 数据丢失** — 由于 pitfall #23 的 EPIPE 崩溃会中断长时间运行的任务，所有循环采集模板必须**每条处理完后立即增量保存到 TEMP_JSON**（不仅仅是缓存文件）。崩溃后重新运行会自动跳过已处理的条目。在 `scrape_pass3_contact.py` 中已实现（每条联系方式提取后立即保存），`scrape_v11_onepass.py` pass2 也应实现此模式。
20. **Excel输出必须是41列固定顺序** — 带货类目必须按 `,` split 后填入3列(带货类目1/2/3)。参见 `references/talent-square/detail-fields-36cols.md`。两个模板的 `save_excel()` 均使用硬编码 HEADERS + vals 字典, 不是动态 dict keys。
21. **`document.body.innerText` fallback for getText failures** — `DETAIL_PARSE_JS` 使用遍历 shadow DOM childNodes 的 `getText()` 函数, 但某些页面结构下只返回 1 行文本导致所有字段为空。修复: 先在 `DETAIL_PARSE_JS` 和 `sv_data evaluate` 两处用 `getText(shadowRoot.body)`, 若结果行数 <10 则 fallback 到 `document.body.innerText`。
22. **短视频明细 9行/组解析** — 短视频明细表实际结构为9行一组，不是4行:
    ```
    偏移  内容           示例
    i     标题           让拖地变成一件愉悦的事...
    i+1   日期            2026/05/22 16:54
    i+2   扫码看视频       微信扫码查看短视频
    i+3   点赞数(数字)     1
    i+4   分享数(数字)     1
    i+5   喜欢数(数字)     1
    i+6   商品名          [大师调香]蔬果园...
    i+7   价格+月销量     ¥39.90 月销量234
    i+8   扫码看详情       微信扫码查看商品详情
    ```
    校验: 第2行(i+1)必须是日期格式 `YYYY/MM/DD`, 第4行(i+3)必须是数字。
    使用 `i += 9` 跳跃, 不是 i += 4。仅在 `sv_data` evaluate 块中修改（DETAIL_PARSE_JS 不包含短视频明细解析）。
23. **联系方式进度缓存** — pass3 进度保存在 `weixin_contact_progress.json` (temp dir), 支持断点续爬。重新爬取前需手动删除该文件和清除 JSON 中的微信号/手机号字段。
24. **PASS1必须筛选有联系方式才能保证PASS3全部提取成功** — 如果 PASS1 不勾选 `FILTER_HAS_CONTACT`，采集的所有达人在 PASS3 中会有大量"暂无联系方式"。正确流程: PASS1 勾选 `FILTER_HAS_CONTACT = True` 只采集已公开联系方式的达人 → PASS2 点击"联系"按钮捕获 roomId → PASS3 打开 collab/im 提取微信号+手机号。此时 PASS3 应 100% 成功，不再出现"暂无联系方式"。
25. **EPIPE 崩溃 + 增量保存** — Python 3.9 + Playwright 在连续打开大量页面后(约16页)会触发 Node.js EPIPE 崩溃。两个模板均已添加: (a) `page.close()` 每个页面处理完立刻关闭; (b) 每条数据增量保存到 TEMP_JSON，崩溃后重新运行可从已有 roomId 继续。
26. **商品列表 API 需要 biz_magic 请求头** — 不同于达人广场/机构广场的 Playwright 驱动方式，商品列表 (`scanProductPreview`) 使用 requests 直接调用 API。认证依赖 `biz_magic` 请求头（值从 `weixin_store_state.json` 的 cookies 中提取。尝试用 `page.request.post()` 或裸 `fetch` 不带 `biz_magic` 头会返回 403 `"biz magic invalid"`。修复：从 storage_state cookies 中取 `biz_magic` 值，加到 headers 字典中。
27. **PASS3 运行前检查** — `scrape_pass3_contact.py` 启动时会自动检测 TEMP_JSON 中待提取条数 >5 且已有联系方式为 0 的情况，命中时打印警告提示用户可能忘记设置 `FILTER_HAS_CONTACT = True`。软检查不影响执行流程。
28. **跨平台函数用于所有模板** — `get_desktop_path()`、`get_temp_file()`、`get_platform_ua()` 三个交叉平台辅助函数已在 SKILL.md 中定义。`scrape_goods_list.py` 使用了全部三个（纯 API 调用需要 UA），Playwright 模板通常只需要前两个。新建模板时应优先引用这些函数。