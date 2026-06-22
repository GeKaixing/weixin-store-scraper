# Session Details (observed 2026-05-12)

## Page Structure

- URL: `https://store.weixin.qq.com/shop/ec-agency/market/home`
- Uses micro-app shadow DOM similar to talent square
- Tabs: 带货机构 / 推客机构
- Agency cards are `.service-box` divs inside `.content-wrap` > `.content-scroll` > `.scroll-wrap`
- Cards have `cursor: pointer` but no explicit `onclick` — click handler is Vue-bound
- Each card shows: avatar, nickname, industry tags, brand logos, 动销带货者, 动销商品, 带货销售额, 合作热招品牌

## Observed Data Count

- **Total agencies** (totalNum): 22,463 (talent square was ~2,200 per category)
- **Per page** (limit=200): 200 items per page, except last page (63 items)
- **Total pages**: 113 pages (with limit=200)

## Performance Benchmarks

- **List API** (limit=200): ~104 seconds for 22,463 items across 113 pages
- **Detail API** (sequential): ~2条/秒 (too slow for all 22k)
- **Detail API** (10x concurrent via `Promise.all` in `page.evaluate`): ~30条/秒
- **Detail full run** (10 concurrent): ~12-15 minutes for 22,463 records
- **Rate limiting**: 0.3s sleep between batches is sufficient; no throttling observed at ~30条/秒

## Resume/Progress Pattern (proven to work)

The detail scraping script at `templates/scrape_agency_detail.py` uses a **separate progress cache**:

1. Progress saved to `/tmp/weixin_agency_detail_progress.json` (periodically every 100 batches)
2. Main list data stays in `/tmp/weixin_agency_all_data.json` (unchanged)
3. On restart: load progress cache, skip already-fetched `ilinkUserId`s
4. After full completion: merge progress into main list data → generate Excel

This was battle-tested: the previous session's background process was killed mid-way but had saved 2,620 records. The next session resumed cleanly from that point.

**Important**: Even with `python3 -u`, background process output via `notify_on_complete` may not capture stdout. Always run foreground first (with 120-180s timeout) to confirm initial progress, then background. Poll periodically with `process(log)`.

## Resume Scenario (observed 2026-05-12)

Previous session killed during detail scraping. Only `/tmp/weixin_agency_all_data.json` (22,463 list records) and incomplete `/tmp/scrape_agency_detail.py` existed. No progress file on filesystem from the killed process — but the re-run's progress detection showed 2,620 cached entries, meaning the script's periodic save (every 100 batches ≈ 1000 records) had persisted data from the prior session.

## First-run Observations

- Initial page load returns 36 items (default limit from Vue)
- Scrolling in headless mode did NOT trigger more API calls — API pagination via offset/limit is the only reliable approach
- The list API with `credentials: 'include'` from `page.evaluate` works after navigating to the domain once

## Detail Page URL Pattern

First observed clicking a `.service-box`:
- Navigated to: `https://store.weixin.qq.com/shop/ec-agency/market/detail?id=d283f865-...@finderecmcn@im.ilinkapp_06000091c663bb&type=SUPPLIER`
- Detail API key: `ilinkUserId` (same as in list API response)

## Order Types

| orderType | Label |
|-----------|-------|
| 1 | 综合 (default) |
| 2 | 动销带货者数 |
| 3 | 动销商品数 |
| 4 | 热招品牌数 |
