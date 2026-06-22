# 三遍采集 + 联系方式筛选工作流

2026-06-21 验证：`FILTER_HAS_CONTACT = True` 时，pass3 10/10 全部提取到联系方式。

## 工作流

```
pass1: 列表页采集 (FILTER_HAS_CONTACT=True)
  ↓   只采集已公开联系方式的达人
pass2: 详情页 + roomId 捕获
  ↓   点击"联系"按钮 → ctx.on('page') 捕获 roomId
pass3: collab/im 页面提取联系方式
      点击左侧会话 → 查看联系方式 → contact-popover 提取
```

## 为什么必须开启筛选

| 配置 | pass1 采集 | pass2 捕获 roomId | pass3 结果 |
|------|-----------|-------------------|-----------|
| FILTER_HAS_CONTACT=True | 仅公开联系方式的达人 | 能点到"联系"按钮 | ✅ 100% 成功 |
| FILTER_HAS_CONTACT=False | 所有达人 | 大部分无"联系"按钮 | ❌ ~70% "暂无" |

## 关键里程碑

- **2026-06-21**: 用户指出 pass1 应该开筛选，验证 10/10 成功。默认值从 False 改为 True。
- PW 版本: playwright 1.50+
- Python 3.9 + Playwright 在 macOS 上约 8-10 个页面后 EPIPE 崩溃 → 必须增量保存
