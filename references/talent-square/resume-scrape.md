# 网络断连补爬机制

当第二趟详情爬取因网络中断（`ERR_INTERNET_DISCONNECTED`）未完成时，可以补爬缺失条目。

## 数据来源

`/tmp/weixin_pass1_data.json` 保存了全部列表数据 + 已爬详情数据。每次保存间隔 10 条（pass2 中每 10 个详情页自动保存）。

## 补爬判断

缺失的条目特征是：有 `达人详情链接` 字段，但 `总销量` 字段为空或不存在。

```python
missing = [(i, t['达人详情链接'], t['昵称']) 
           for i, t in enumerate(all_talents) 
           if t.get('达人详情链接') and not t.get('总销量')]
```

## 补爬流程

1. 读取 `/tmp/weixin_pass1_data.json`
2. 找出缺失详情的条目
3. 用 Playwright + storage_state 逐个 `page.goto` 爬详情
4. 每 20 条保存一次进度
5. 补爬完成后用 `gen_final_excel.py` 生成最终 Excel

## 速度

~4 秒/条（打开标签 + 3 秒等待渲染 + 解析），2000 条 ≈ 2.2 小时

## 补爬脚本

见 `../templates/resume_detail_scrape.py`