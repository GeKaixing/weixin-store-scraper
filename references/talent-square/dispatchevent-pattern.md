# dispatchEvent 交互模式 — 微信小店达人广场

## 问题

`page.mouse.click(x, y)` 在 shadow DOM + Vue SPA 中经常不触发 Vue 事件处理器，导致所有点击行为静默失败：翻页不翻页、筛选不筛选、详情不弹窗。

## 根因

Playwright 的 `page.mouse.click` 发送操作系统级别的合成点击事件。Micro-app 的 shadow DOM 边界可能阻挡事件传播，且 Vue 的响应式劫持可能不被浏览器原生事件触发。具体机制待确认，但现象稳定复现。

## 解决方案：dispatchEvent 模式

所有 UI 交互统一使用：

```javascript
// ✅ 有效
el.dispatchEvent(new MouseEvent('click', {
    bubbles: true,
    cancelable: true,
    view: window
}));
```

### checkbox 切换（如类目筛选）

checkbox 被 CSS 定位到屏幕外 (left: -133310px)，不可见不可坐标点击。必须 dispatch 三个事件：

```javascript
const cb = label.querySelector('input[type=checkbox]');
cb.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
cb.dispatchEvent(new Event('change', {bubbles: true}));   // Vue 需要 change 事件
cb.dispatchEvent(new Event('input', {bubbles: true}));     // 部分页面还需 input 事件
```

实测：只发 click+change 有时筛选不生效（总页数=0），加上 input 后稳定正常（总页数=168）。

### 详情点击（获取链接）

详情链接通过 `window.open(url)` 打开新标签页。`<a>` 标签的 href 是 `javascript:void(0)`。有两种方式：

**A) window.open 覆盖（快，但污染翻页状态）：**
```javascript
const orig = window.open;
window.open = function(url) {
    results.push(url);
    return null;
};
for (const link of links) {
    link.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
}
window.open = orig;
```

⚠️ 20 次详情点击会修改 Vue 组件内部状态，导致"下一页"按钮失效。必须配合输入框翻页使用。

**B) 逐个开标签（可靠但慢，~3秒/条）：**
逐个点击，Playwright 的 `ctx.expect_page()` 捕获新标签页，读 URL，关标签。

### 翻页

用 dispatchEvent 点击"下一页"可行（已验证）。但如果之前执行过 window.open 覆盖操作，Vue 状态可能已污染，此时必须用输入框+跳转按钮翻页。

输入框操作有两种方式：

**方式 1（推荐 — dispatchevent 点击）：**
```python
# 1. dispatchEvent 点击输入框聚焦
sr.querySelector('input.weui-desktop-pagination__input')
  .dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}))

# 2. Meta+A 全选后输入页码
await page.keyboard.press('Meta+a')
await page.keyboard.type(str(page_num))

# 3. dispatchEvent 点击跳转按钮
sr.querySelector('div:nth-child(1) > div:nth-child(1) > div:nth-child(4) > ... > a')
  .dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}))
```

**方式 2（直接设置 value + dispatch 事件）：**
```javascript
const inp = sr.querySelector('input.weui-desktop-pagination__input');
inp.value = '2';
inp.dispatchEvent(new Event('input', {bubbles: true}));
inp.dispatchEvent(new Event('change', {bubbles: true}));
// 然后点跳转按钮
const jumpBtn = sr.querySelector('...');
jumpBtn.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
```

⚠️ 不要用 `el.click()` 原生调用 → 用 `dispatchEvent(new MouseEvent('click', ...))`。
