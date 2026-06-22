# 合作管理导出流程

## 页面URL
`https://store.weixin.qq.com/shop/shopleague/coop-manage`

## 导出流程

1. 打开页面 → 关通知弹窗（点"我知道了"）
2. 如果需要机构导出 → 点"机构管理"tab
3. 点击 `span` 包含"导出带货者信息"或"导出机构信息"（dispatchEvent可生效）
4. 弹出确认对话框 → 找到"导出"按钮
5. **必须用 page.mouse.click()** 点确认按钮（dispatchEvent对dialog不生效）
6. 等待~4秒 → ZIP自动下载（Playwright download事件捕获）

## 对话框文本流

```
共导出N条信息，预计需要时间：4秒。取消导出  导出
→ (等待4秒)
带货者信息已导出。如未自动下载，可点击 下载数据  关闭
```

## 文件命名

- 带货者: `带货者列表_YYYY年MM月DD日HH时MM分SS秒.zip`
- 机构: `机构列表_YYYY年MM月DD日HH时MM分SS秒.zip`

## 注意事项

- dispatchEvent对dialog内的"导出"按钮无效 → 必须用mouse.click
- 文件在导出流程完成后自动下载, 不需要点"下载数据"
- 文件名带中文和日期, 保存到Desktop
