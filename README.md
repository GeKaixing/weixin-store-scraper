# 微信小店 Scraper

微信小店达人数据采集工具集，支持达人广场、机构广场、合作管理的数据采集与导出。

## 功能

- **达人广场（Talent Square）** — 按类目筛选达人，采集完整 41 字段数据（含直播/短视频带货明细、联系方式），输出 Excel
- **机构广场（Agency Market）** — 采集带货机构列表与详情（9 字段），支持批量并发请求
- **合作管理（Cooperation Management）** — 导出带货者/机构合作信息（ZIP 下载）
- **联系方式提取** — 自动从合作 IM 页面提取微信号 + 手机号
- **断点续爬** — 进度缓存支持中断恢复，无需重新开始

## 数据字段（达人广场 41 列）

| 字段 | 说明 |
|------|------|
| 头像、昵称 | 达人基本信息 |
| 带货类目 1/2/3 | 主营类目（最多 3 个） |
| 评分、粉丝数、带货销售总额 | 核心数据 |
| 直播销售额、场均成交额、场观、总场次、直播明细 | 直播带货数据 |
| 视频销售额、条均成交额、点赞数、总条数、短视频明细 | 短视频带货数据 |
| 微信号、手机号、IM 链接 | 联系方式 |
| 粉丝画像（性别/年龄/地域/人群/偏好/购买力） | 粉丝分析 |

## 项目结构

```
weixin-store-scraper/
├── SKILL.md                         # Hermes Agent skill 主文档
├── assets/
│   └── weixin_store_state.json      # Playwright 持久化登录态（已 gitignore）
├── templates/
│   ├── talent-square/               # 达人广场模板
│   │   ├── scrape_v11_onepass.py    # [推荐] 两遍采集主流程
│   │   ├── scrape_pass3_contact.py  # 第三遍联系方式提取
│   │   ├── scrape_all_34.py         # 全 34 类目批量采集
│   │   └── resume_detail_scrape.py  # 详情页断点续爬
│   ├── agency-market/               # 机构广场模板
│   │   ├── scrape_agency_list.py    # 列表采集
│   │   ├── scrape_agency_detail.py  # 详情采集（并发）
│   │   └── resume_agency.py        # 断点恢复
│   └── coop-manage/
│       └── export_coop.py           # 合作管理导出
├── references/                       # 参考文档
│   ├── talent-square/               # 达人广场页面结构、字段解析、注意事项
│   ├── agency-market/               # API 端点、行业映射
│   └── coop-manage/                 # 导出流程
├── scripts/
│   └── talent-square/
│       └── check_page_state.py      # 页面版本诊断
├── README.md
└── .gitignore
```

## 前置条件

- Python 3.9+
- Playwright：`pip install playwright && playwright install chromium`
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

### 2. 采集达人数据

```bash
python templates/talent-square/scrape_v11_onepass.py
```

输出 Excel 到桌面。

### 3. 提取联系方式

```bash
python templates/talent-square/scrape_pass3_contact.py
```

从合作 IM 页面提取微信号 + 手机号，补充到 Excel。

## 采集方式

| 模块 | 采集方式 | 特点 |
|------|----------|------|
| 达人广场 | Playwright + Shadow DOM + Vue SPA | 三遍架构，页面交互复杂 |
| 机构广场 | 直接 API 调用 | 速度快，支持并发 |
| 合作管理 | 原生导出按钮 | ZIP 自动下载 |

## 注意事项

- 每日查看达人联系方式次数有限制，达到上限后自动跳过
- 登录态通常有效数天至数周，过期需重新生成
- Excel 文件名中不可包含 `/`，已自动替换为 `、`

## License

MIT
