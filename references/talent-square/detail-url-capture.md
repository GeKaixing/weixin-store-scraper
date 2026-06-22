# 详情URL双路径修复

## 问题

`window.open` override捕获的URL已经是绝对路径：

```
/shop/findersquare/finder-detail?from=1&fromTab=all&finderUsername=...
```

旧代码在pass1 JS和pass2 Python中都错误地再拼接了一次路径：

```js
// ❌ 旧代码 — 创建双路径
'https://store.weixin.qq.com/shop/findersquare/' + url
// 结果: https://store.weixin.qq.com/shop/findersquare//shop/findersquare/finder-detail?... → 404
```

## 修复

```js
// ✅ 正确 — 只拼域名
'https://store.weixin.qq.com' + url
```

## 需要修复的两处

1. **pass1 JS** — `get_list_data_with_urls()`中的window.open override (line ~157):
   ```js
   captured._openUrl = url.startsWith('http') ? url
       : 'https://store.weixin.qq.com' + url;
   ```

2. **pass2 Python** — URL拼接 (line ~406):
   ```python
   full_url = url if url.startswith('http') else 'https://store.weixin.qq.com' + url
   ```

## 验证

- 修复前: `page.goto`报 `404` 或 `net::ERR_CONNECTION_CLOSED`
- 修复后: 详情页正常加载, 2/20条有详情数据 → 18/20条

## 注意

window.open回调的`url`参数格式是绝对路径(以`/`开头), 不是相对路径:
- `window.open('/shop/findersquare/finder-detail?...', ...)` → url = `/shop/findersquare/finder-detail?...`
