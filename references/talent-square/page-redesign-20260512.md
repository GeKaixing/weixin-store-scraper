# 页面重构报告 — 2026-05-12

## 概述

2026年5月11日（上次成功爬取后）到5月12日之间，微信小店达人广场页面被**完全重构**。所有原有的 table 结构、下拉筛选、分页控件都已被替换为新的组件。

## 新旧结构对比

| 方面 | 旧版 (2026-05-11 前) | 新版 (2026-05-12) |
|------|---------------------|-------------------|
| 达人列表渲染 | `<table> <tr> <td>` 表格 | `<div.grid.grid-cols-4>` 卡片网格 |
| 每行/卡片数据 | 7列: 昵称/粉丝数/带货额/直播/短视频/公众号/详情 | 头像+昵称+类目+评分（4张卡片/行） |
| 类目筛选 | 下拉面板→勾选checkbox→关闭下拉触发刷新 | checkbox**始终可见**（`hide-cate`类名存在但display:flex可见） |
| 分页 | 输入框+跳转按钮 | **不存在** — 无 pagination 组件 |
| 数据量 | ~20条/页（19数据行） | 仅4张智能推荐卡片，无完整列表 |
| 筛选触发 | 勾选后关闭下拉自动刷新 | 勾选后无数据加载（出现"删除"按钮但无新数据） |
| 详情链接 | `<td>:last-child a` (javascript:void(0)) | 未知（旧卡片格式无详情按钮/链接） |
| body类名 | 无特别 | `finder-find-container` + `form-filter-container` |
| 顶部导航 | 无 | "找达人" / "达人招商" / "我的邀约" / "邀约模版" |
| Tab切换 | 无 | "全部达人" / "直播达人" / "短视频达人" |

## 新页面DOM结构描述

```
micro-app → shadowRoot → micro-app-body
  └─ div#app
       └─ div.finder-find-container
            ├─ header "达人广场"
            ├─ div.weui-desktop-msg (通知横幅)
            ├─ div.flex.items-center.h-[64px] (顶部导航: 找达人/达人招商/我的邀约/邀约模版)
            ├─ div.bg-[var...].rounded-[12px] (智能推荐区域)
            │    ├─ div.flex.justify-between (标题"智能推荐" + "更多"按钮)
            │    └─ div.grid.grid-cols-4
            │         └─ 4× div.border-[0.5px].rounded-[8px] (卡片: 头像img+昵称+类目+评分)
            └─ div.weui-desktop-block
                 └─ div.weui-desktop-block__main
                      └─ div.weui-desktop-block__content
                           └─ div.form-filter-container
                                ├─ div.mt-4.flex.justify-between (tab: 全部达人/直播达人/短视频达人 + 搜索框)
                                └─ form
                                     ├─ div.weui-desktop-form__control-group (带货类目)
                                     │    ├─ label "带货类目"
                                     │    └─ div.weui-desktop-form__controls
                                     │         └─ div.inline-block
                                     │              └─ div.hide-cate (始终可见! display:flex)
                                     │                   └─ 34× label.weui-desktop-form__check-label
                                     │                        ├─ input[type=checkbox][value=topCatId]
                                     │                        └─ span > span "类目名称"
                                     └─ div.weui-desktop-form__control-group (其他筛选)
```

## 关键发现

1. **`hide-cate` 类名不隐藏元素** — `display: flex; visibility: visible;` 所有checkbox始终可见
2. **筛选不触发数据加载** — 勾选checkbox后（已确认checked=true），页面无新数据加载。可能是新版需要配合"搜索"按钮或API调用
3. **未找到完整的达人列表** — 页面只有"智能推荐"区域的4张卡片，没有传统分页列表
4. **"更多"按钮导航到其他页面** — 点击后跳转到新的URL，不在finder-detail页面内
5. **"全部达人" tab 点击有效但无数据出现** — click dispatchEvent 成功但数据区域为空
6. **Session依然有效** — 登录态未过期

## 下次尝试方向

1. **hook Network API** — 拦截 `getSquareTalentList` / `getAllFilter` / `finderSquare` 相关API请求
2. **查看新版"搜索"按钮** — 可能在checkbox筛选后需要点击搜索按钮才触发
3. **检查 "智能推荐" → "更多" 跳转后的页面** — 可能是新的达人列表页面
4. **尝试调整 viewport 大小** — 新版可能响应式，移动端/小窗口可能显示不同UI
5. **检查 localStorage / sessionStorage 中的配置** — 新版可能用本地存储控制UI状态
