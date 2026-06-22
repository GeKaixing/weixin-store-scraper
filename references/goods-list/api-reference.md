# 商品列表 API 参考

## API 接口

**URL:** `POST https://store.weixin.qq.com/shop-faas/mmchannelstradeproductcore/cgi/goods/scanProductPreview?token=&lang=zh_CN`

## 认证方式

需要以下请求头（从 Playwright storage_state 的 cookies 中提取）:

- `biz_magic` — 从 cookie 中的同名值获取，必填
- `potter-scene: weixinShop` — 固定值
- `Origin: https://store.weixin.qq.com`
- `Referer: https://store.weixin.qq.com/shop/goods/list`
- `Cookie` — 需要包含 `biz_token` 和 `biz_magic`

## 请求参数

```json
{
  "pageSize": 20,
  "productStatus": [-1],
  "productSource": "[1,16,32]",
  "searchSource": 1,
  "useNew": true,
  "fromProductManager": 1,
  "pageNum": 1,
  "status": [-1]
}
```

| 参数 | 说明 |
|------|------|
| pageSize | 每页数量（最大20） |
| pageNum | 页码（从1开始） |
| productStatus | [-1] = 全部, [1] = 销售中, [2] = 已下架, [5] = 待审核 |
| productSource | 商品来源 |

## 返回字段

商品对象包含约 80+ 个字段，核心字段:

| 字段 | 说明 |
|------|------|
| productId | 商品ID |
| spuCode | SPU编码 |
| title | 商品名称 |
| subTitle | 副标题 |
| price | 价格 |
| skuList[] | SKU列表（含price/stockNum/soldNum） |
| totalStockNum | 总库存 |
| totalSoldNum | 总销量 |
| totalOrderNum | 总订单数 |
| totalVisitNum | 总曝光量 |
| status | 状态码 (1=销售中, 2=已下架, 5=待审核, 11=审核未通过) |
| listingTime | 上架时间 |
| editTime | 编辑时间 |
| brand | 品牌 |
| headImg | 主图URL |
| category[] | 类目信息 |
| detail.detailImg[] | 详情图列表 |
| param[] | 商品参数/规格 |
| source | 销售渠道 |

## 状态码映射

| 状态码 | 含义 |
|--------|------|
| 1 | 销售中 |
| 2 | 已下架 |
| 5 | 待审核 |
| 11 | 审核未通过 |
| -1 | 全部 |

## 注意

- 不要用 `page.request.post()` 或 `fetch` 直接调用 — 需要附加 `biz_magic` 请求头
- 纯 requests 调用时从 storage_state 的 cookies 提取 `biz_magic` 值
- session 过期后需要重新生成 storage_state（重新扫码登录）
