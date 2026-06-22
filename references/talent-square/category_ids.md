# 微信小店达人广场分类ID + label nth-child 索引对照表

所有 34 个类目在筛选下拉中的 label 位置（nth-child 索引，从 1 开始）。

| # | 分类名称 | topCatId | label nth-child |
|---|---------|----------|-----------------|
| 1 | 文玩文创 | 10000405 | 1 |
| 2 | 珠宝首饰 | 10000331 | 2 |
| 3 | 家纺 | 10000066 | 3 |
| 4 | 运动户外 | 10000183 | 4 |
| 5 | 母婴 | 10000116 | 5 |
| 6 | 家用电器 | 10000057 | 6 |
| 7 | 数码 | 10000104 | 7 |
| 8 | 鞋靴 | 10000212 | 8 |
| 9 | 家庭清洁/纸品 | 10000050 | 9 |
| 10 | 箱包皮具 | 10000173 | 10 |
| 11 | 个人护理 | 10000001 | 11 |
| 12 | **食品饮料** | **10000215** | **12** |
| 13 | 生鲜 | 10000155 | 13 |
| 14 | 家居日用 | 10000046 | 14 |
| 15 | 家具 | 10000033 | 15 |
| 16 | 酒类 | 10000201 | 16 |
| 17 | 钟表 | 10000208 | 17 |
| 18 | 图书 | 10000257 | 18 |
| 19 | **保健食品/膳食营养补充食品** | **10000508** | **19** |
| 20 | 服饰内衣 | 10000111 | 20 |
| 21 | 家装建材 | 10000069 | 21 |
| 22 | 美妆护肤 | 10000178 | 22 |
| 23 | 汽摩电动 | 10000126 | 23 |
| 24 | 玩具乐器 | 10000132 | 24 |
| 25 | 教育培训 | 10000349 | 25 |
| 26 | 农资园艺 | 10000007 | 26 |
| 27 | 宠物生活 | 10000026 | 27 |
| 28 | 成人用品 | 10000575 | 28 |
| 29 | 酒旅 | 545228 | 29 |
| 30 | 餐饮 | 545203 | 30 |
| 31 | 电脑、办公 | 10000164 | 31 |
| 32 | 手机通讯 | 10000099 | 32 |
| 33 | 厨具 | 10000018 | 33 |
| 34 | 其他 | 10000358 | 34 |

## CSS Selector 构建

label 的 nth-child 位置对应筛选下拉中的顺序：
```javascript
const label_index = 19;  // 保健食品
const selector = `div:nth-child(1) > div:nth-child(1) > div:nth-child(4) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > form > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > label:nth-child(${label_index}) > span`;
```

## API Endpoint Details

**getAllFilter** — GET request that returns all filter options including categories:
```
/shop-faas/mmchannelstradeleague/finderSquare/cgi/getAllFilter?token=***&lang=zh_CN
```

**getSquareTalentList** — POST with filter body:
```json
{
  "filter": {
    "topCatId": "10000508",
    "limit": 200,
    "offset": 0,
    "isLiveFinder": 0,
    "isVideoFinder": 0,
    "isMpPromoter": 0,
    "sortKey": 0,
    "sortDirection": 1
  }
}
```
