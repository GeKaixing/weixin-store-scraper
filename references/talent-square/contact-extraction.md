# Pass3 Contact Extraction (collab/im page)

## URL Format

```
https://store.weixin.qq.com/shop/kf/collab/im?mode=business&roomId={roomId}
```

roomId 由 pass2 从详情页"联系"按钮 popup URL 中捕获。

## DOM Structure

### Contact link (always visible in right panel)
```html
<a data-v-77a48bbd="" data-v-85b97fa7="" class="kf-link contact-link"> 查看联系方式 </a>
```
Wrapped in:
```html
<div class="weui-desktop-popover__wrp">
  <span class="weui-desktop-popover__target">...</span>
  <div class="weui-desktop-popper p-[12px]" style="width: 240px;">
    <div class="weui-desktop-popover__desc">
      <div class="contact-popover">...</div>
    </div>
  </div>
</div>
```

### Contact popover (after clicking contact-link)
**有联系方式时:**
```html
<div class="contact-popover">
  <div class="contact-popover__title"> 带货者联系方式 </div>
  <div class="contact-popover__item">
    <i class="i-weui:wechat-regular"></i>
    <span class="contact-popover__value">Guandance</span>
    <svg class="contact-popover__copy">...</svg>
  </div>
  <div class="contact-popover__item">
    <i class="i-weui:call-on-regular"></i>
    <span class="contact-popover__value">13011103811</span>
    <svg class="contact-popover__copy">...</svg>
  </div>
</div>
```

**无联系方式时:**
```html
<div class="contact-popover">
  <div class="contact-popover__title"> 带货者联系方式 </div>
  <div class="contact-popover__status">暂无联系方式</div>
</div>
```

**已达上限时:**
```html
<div class="contact-popover">
  <div class="contact-popover__status">今天查看达人联系方式次数已达上限，暂无法联系</div>
</div>
```

## Extraction Flow

1. **Navigate** to `collab/im?roomId={roomId}`
2. **Wait 5s** for page to load
3. **Click matching session** — find `[data-room-id="{roomId}"]` LI element and click it (required! URL navigation alone does NOT select the session)
4. **Wait 5s** for right-side talent info panel to load
5. **Click contact-link** — `.contact-link` or `[class*="contact-link"]`
6. **Wait 3s** for popover to appear
7. **Extract** from `.contact-popover__item`:
   - If icon contains `wechat`/`weixin` → 微信号
   - Else if value matches `1[3-9]\d{9}` → 手机号
8. **Detect skip cases**:
   - Text contains "已达上限" → skip, re-run next day
   - Text contains "暂无联系方式" → empty, mark as no contact

## ⚠️ Critical Rules

- **NEVER use regex on full page text** — the left sidebar session list contains many other talents' wechat IDs (e.g. "jackey", "Zzz_jy") that will be falsely captured
- **Only extract from `.contact-popover__item`** checking the icon HTML for wechat/weixin vs call/phone
- **Always click `[data-room-id]` session first** — URL alone doesn't select the session; without selection, the right panel shows contact-info from whatever session is at the top of the list
- **Rate limit**: 微信小店 caps daily contact views. When hit, "已达上限" appears — detect this and skip

## Key Selectors

| Element | Selector | Purpose |
|---------|----------|---------|
| Session item | `[data-room-id]` (LI) | Click to select right-panel talent |
| Contact link | `a.contact-link` | Toggle popover |
| Contact title | `.contact-popover__title` | Verify popover loaded ("带货者联系方式") |
| Contact value | `.contact-popover__value` | The wechat ID or phone number |
| Contact status | `.contact-popover__status` | "暂无联系方式" or "已达上限" |
