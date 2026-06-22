# Pagination Investigation — 2026-05-11

## Session Context
Running `scrape_v11_onepass.py` to scrape 母婴 category, 2-page test.

## Key Discovery: Tab-opening pollutes Vue state → pagination breaks

Even without `window.open` override, opening 18+ detail tabs via `ctx.expect_page` then closing them pollutes the main page's Vue state. After that, `goto_page` (dispatchEvent to input + jump button) silently fails — page 2 returns identical data to page 1.

### Evidence
- 36 total items, only 18 unique nicknames (page 1 and page 2 data are identical)
- `get_list_data` returns same 19 rows on both pages
- Pagination input accepts typed number, jump button is clicked (no error), but Vue doesn't re-render

### Root Cause
Vue SPA component state gets corrupted after the micro-app recovers from 18+ tab open/close cycles. This is the same class of issue as the `window.open` override pollution documented earlier, just triggered differently.

## Pagination HTML Structure (as of 2026-05-11)

```html
<span class="weui-desktop-pagination__nav">
  <span class="weui-desktop-pagination__num__wrp spread">
    <label class="weui-desktop-pagination__num weui-desktop-pagination__num_current">1</label>
    <label class="weui-desktop-pagination__num">2</label>
    <label class="weui-desktop-pagination__num">3</label>
    <label class="weui-desktop-pagination__num">4</label>
    <label class="weui-desktop-pagination__num weui-desktop-pagination__ellipsis">...</label>
    <label class="weui-desktop-pagination__num">250</label>
  </span>
  <a href="javascript:;" class="weui-desktop-btn weui-desktop-btn_default weui-desktop-btn_mini">下一页</a>
</span>
<span class="weui-desktop-pagination__form">
  <input type="number" class="weui-desktop-pagination__input">
  <a href="javascript:;" class="weui-desktop-link">跳转</a>
</span>
```

**Text output:** `1234...250下一页跳转`
**Correct max page extraction:** `text.match(/\.\.\.(\d+)/)` → 250
**Wrong extraction:** `Math.max(...digits)` → 1234

## Per-page Data Count
- `document.querySelectorAll('tr')` inside shadow DOM = 20 total (1 header + 19 data rows)
- `td:last-child a` count = 19-20 (detail buttons)
- Template's `get_list_data` returns 18-19 rows (filtered by `tds.length < 3`)

## Filter Application Status (母婴)
- Filter successfully applied (pagination changed from 500 → 250 total pages)
- 19 data rows on filtered page 1
- Category filter checkbox dispatchEvent works correctly

## Session State
- Login session at `/tmp/weixin_store_state.json` — still valid (5 cookies)
- biz_magic cookie: `8cdd8ba4f5db11abb02c440dabd57b6a08b369345acabcc30904ba7a95d573e4`
- 总页数 unfiltered: 500
- 总页数 filtered (母婴): 250
