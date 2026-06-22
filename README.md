# 微信小店 Scraper

微信小店数据采集工具集，跨平台支持（macOS / Windows / Linux），覆盖达人广场、机构广场、商品列表、合作管理。

## 功能

- **达人广场（Talent Square）** — 按类目筛选达人，采集完整 41 字段数据（含直播/短视频带货明细、联系方式），输出 Excel
- **联系方式提取** — 自动从合作 IM 页面提取微信号 + 手机号，PASS1 筛选后 100% 成功率
- **商品列表（Goods List）** — 调用官方 API 采集全部商品信息（21 字段），无需浏览器
- **机构广场（Agency Market）** — 采集带货机构列表与详情（9 字段），支持批量并发请求
- **合作管理（Cooperation Management）** — 导出带货者/机构合作信息（ZIP 下载）
- **断点续爬** — 进度缓存支持中断恢复，EPIPE 崩溃后增量保存不丢数据

## 达人广场数据字段（41 列）

| 字段 | 说明 |
|------|------|
| 头像、昵称 | 达人基本信息 |
| 带货类目 1/2/3 | 主营类目（最多 3 个） |
| 评分、粉丝数、带货销售总额 | 核心数据 |
| 直播销售额、场均成交额、场观、总场次、直播明细 | 直播带货数据 |
| 视频销售额、条均成交额、点赞数、总条数、短视频明细 | 短视频带货数据 |
| 微信号、手机号、IM 链接 | 联系方式 |
| 粉丝画像（性别/年龄/地域/人群/偏好/购买力） | 粉丝分析 |

## 商品列表数据字段（21 列）

商品ID、SPU编码、商品名称、副标题、价格(元)、最高价(元)、总库存、总销量、总订单数、总曝光量、状态、子状态、上架时间、编辑时间、品牌、SKU数、商品类型、类目ID、发货方式、主图、销售渠道

## 项目结构

```
weixin-store-scraper/
├── SKILL.md                         # Hermes Agent skill 主文档
├── assets/
│   └── weixin_store_state.json      # Playwright 持久化登录态（已 gitignore）
├── templates/
│   ├── talent-square/               # 达人广场模板
│   │   ├── scrape_v11_onepass.py    # [推荐] 两遍采集主流程（PASS1列表+roomId, PASS2详情）
│   │   ├── scrape_pass3_contact.py  # 第三遍联系方式提取
│   │   ├── scrape_all_34.py         # 全 34 类目批量采集
│   │   └── resume_detail_scrape.py  # 详情页断点续爬
│   ├── agency-market/               # 机构广场模板
│   │   ├── scrape_agency_list.py    # 列表采集
│   │   ├── scrape_agency_detail.py  # 详情采集（并发）
│   │   └── resume_agency.py        # 断点恢复
│   ├── goods-list/                  # 商品列表模板
│   │   └── scrape_goods_list.py     # API 采集全部商品（跨平台）
│   └── coop-manage/
│       └── export_coop.py           # 合作管理导出
├── references/                       # 参考文档
│   ├── talent-square/               # 达人广场页面结构、字段解析、注意事项
│   ├── agency-market/               # API 端点、行业映射
│   ├── goods-list/                  # 商品列表 API 参考
│   └── coop-manage/                 # 导出流程
├── scripts/
│   └── talent-square/
│       └── check_page_state.py      # 页面版本诊断
├── README.md
└── .gitignore
```

## 前置条件

- Python 3.9+
- Playwright：`pip install playwright && playwright install chromium`（仅达人广场需要）
- 微信小店商家后台登录态

## 快速开始

### 1. 准备登录态

用 Playwright 打开微信小店并扫码登录，保存 storage_state：

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto("https://store.weixin.qq.com")
    input("扫码登录后按 Enter...")
    ctx.storage_state(path="assets/weixin_store_state.json")
```

### 2. 采集达人数据（含联系方式）

**关键：** 编辑 `scrape_v11_onepass.py`，将 `FILTER_HAS_CONTACT = True`，这样 PASS3 才能 100% 提取到联系方式。

```bash
# PASS1 + PASS2：列表采集 + 详情页 + roomId
python templates/talent-square/scrape_v11_onepass.py

# PASS3：提取微信号 + 手机号
python templates/talent-square/scrape_pass3_contact.py
```

输出 Excel 到桌面 `微信小店达人数据(DOM)/`。

### 3. 采集商品列表

```bash
python templates/goods-list/scrape_goods_list.py
```

输出 Excel 到桌面 `微信小店商品数据/商品列表_全量.xlsx`。

## 采集方式

| 模块 | 采集方式 | 特点 |
|------|----------|------|
| 达人广场 | Playwright + Shadow DOM + Vue SPA | 三遍架构，页面交互复杂 |
| 商品列表 | 直接 API 调用（biz_magic 认证） | 速度快，跨平台，无需浏览器 |
| 机构广场 | 直接 API 调用 | 速度快，支持并发 |
| 合作管理 | 原生导出按钮 | ZIP 自动下载 |

## 核心流程（达人广场三遍架构）

```
PASS1: 列表采集 ──→ 筛选有联系方式的达人（FILTER_HAS_CONTACT=True）
                       ↓
PASS2: 打开详情页 ──→ 爬取41字段数据 + 点击"联系"捕获 roomId
                       ↓
PASS3: collab/im ──→ 提取微信号 + 手机号（100% 成功的前提是 PASS1 已筛选）
```

## 跨平台兼容

所有脚本自动检测操作系统：
- **桌面路径**：macOS → `~/Desktop`，Windows → `~/Desktop`，Linux → `$XDG_DESKTOP_DIR` 或 `~/Desktop`
- **User-Agent**：根据系统自动适配
- **临时文件**：统一使用系统临时目录

## 注意事项

- **PASS1 必须设置 `FILTER_HAS_CONTACT = True`**，否则 PASS3 会大量"暂无联系方式"
- 每日查看达人联系方式次数有限制，达到上限后自动跳过
- 登录态通常有效数天至数周，过期需重新生成
- EPIPE 崩溃（Python 3.9 + Playwright）已通过增量保存解决，崩溃后重新运行即可继续
- Excel 文件名中不可包含 `/`，已自动替换为 `、`

## License

MIT
