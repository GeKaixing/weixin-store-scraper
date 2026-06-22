# 微信小店达人广场 — 已知问题 & 数据质量陷阱

## 1. 详情链接获取

**问题：** `<a>` 标签 href 是 `javascript:void(0)`，不是真实 URL。

**原因：** Vue click handler 用 `window.open(url)` 打开新标签页，URL 由组件数据动态构建。

**解决方案：**
- 方案 A（快，有副作用）：覆盖 `window.open` 为捕获函数，批量点击所有"详情"链接，捕获 URL 而不打开标签。
- 方案 B（慢，可靠）：逐个点击"详情"，等新标签页打开，读取 URL，关闭标签。

**副作用（方案 A）：** 20 次详情点击修改了 Vue 组件状态，导致"下一页"按钮失效。必须用输入框+跳转按钮翻页。

## 2. 类目筛选失效

**问题：** API 的 `getSquareTalentList?topCatId=` 参数返回 98% 无关结果（按商品类目匹配而非达人主营类目）。

**UI 筛选方案（已验证可行）：**
1. 点击"带货类目"下拉触发元素
2. 在 shadow DOM 中找到对应类目的 `<label>` 元素
3. checkbox 被 CSS 定位到屏幕外（x=-133310），`page.mouse.click` 坐标方式无效
4. 必须用 `cb.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}))` +
   `cb.dispatchEvent(new Event('change', {bubbles:true}))` 程序化勾选
5. 再点击下拉关闭，触发页面自动刷新数据

## 3. 翻页方式

**"下一页"按钮问题：** 如果之前用了 `window.open` 覆盖（方案 A），Vue 状态被污染，"下一页"按钮不再响应。

**可靠翻页方式：** 用页码输入框（`input.weui-desktop-pagination__input`）+ 跳转按钮（文字为"跳转"的 `<a>` 标签）。

## 4. 数据重复（翻页失败症状）

如果爬取结果中"不重复昵称"数远小于总记录数（如 10000 条但只有 20 个不重复），说明翻页没有生效——每页都是同一批数据。

**排查步骤：**
1. 检查页面是否正确导航（看首页达人名称是否变化）
2. 确认输入框 clicked/focused/typed 了正确的页码
3. 确认"跳转"按钮被点击或 Enter 键被发送

## 5. 会话过期

Playwright 登录态文件 `/tmp/weixin_store_state.json` 包含 cookies。页面如果显示"登录"/"扫码"，说明会话已过期，需要重新扫码登录。

## 6. Excel 标题含 "/"

`openpyxl` 不接受 `/` 作为 sheet 标题。如"电脑、办公"类目需替换为 `、`。

## 7. API 调用 token

`getSquareTalentList?token=***&lang=zh_CN` 中的 `***` 是 Playwright 的显示掩码，不是实际 token。真实 token 为空字符串（`token=`），API 依赖 cookies 中的 `biz_magic` 认证。
