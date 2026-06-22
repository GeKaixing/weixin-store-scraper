# DETAIL_PARSE_JS结构 & 双阶段evaluate模式

## 第一阶段: 直播带货 (默认tab)

`DETAIL_PARSE_JS` 在页面加载后直接执行（默认显示直播带货tab），解析：

1. 基本信息：总销量, 跟买人数, 回头客
2. 品类占比：品类名 + 百分比对
3. 带货概览：带货销售额, 客单价, 粉丝数, 直播占比
4. 粉丝特征：性别, 年龄, 地域, 人群类别, 购物偏好, 购买力区间
5. 带货渠道
6. 直播带货：场均成交额, 场均观看人数, 总带货场次
7. 直播明细：行组解析(标题|日期|时长|观看数|商品数)

## 第二阶段: 短视频带货 (需点击tab)

在pass2中, 第一阶段evaluate完成后, 用 `page.mouse.click()` 点击短视频带货tab:

```python
sv_tab = await dp.evaluate("""() => {
    const sr = document.querySelector('micro-app')?.shadowRoot;
    if(!sr) return null;
    for(const e of sr.querySelectorAll('div')) {
        if(e.offsetParent === null) continue;
        if(e.textContent.trim() === '短视频带货') {
            const r = e.getBoundingClientRect();
            return {x: r.x + r.width/2, y: r.y + r.height/2};
        }
    }
    return null;
}""")
if sv_tab:
    await dp.mouse.click(sv_tab['x'], sv_tab['y'])
await asyncio.sleep(3)
sv_data = await dp.evaluate("""() => {
    // 解析: 视频销售额, 条均成交额, 条均点赞数, 总带货条数, 短视频明细
}""")
```

## tab点击说明

- dispatchEvent对Vue channel-tab组件不生效
- 必须用 `page.mouse.click()` + getBoundingClientRect坐标
- 直播带货和短视频带货tab使用同样的 `<div>` 标签, 通过 `textContent.trim()` 区分

## 明细字段格式

- **直播明细**: `标题|日期|时长|观看数|N件`
- **短视频明细**: `日期|赞[scan_text]|分享N|喜欢N`
