# API Endpoints for 微信小店 Agency Market

## List API

```
POST https://store.weixin.qq.com/shop-faas/mmeckolnode/square/getSearchSupplierAgencyList?lang=zh_CN
Content-Type: application/json
Credentials: include (cookies from Playwright session)

Request Body:
{
  "orderType": 1,    // 1=综合, 2=动销带货者数, 3=动销商品数, 4=热招品牌数
  "limit": 200,       // max=200 (1000 returns -202)
  "offset": 0         // pagination offset
}

Response:
{
  "code": 0,
  "data": {
    "code": 0,
    "itemList": [ ... ],
    "totalNum": 22463
  }
}
```

## Detail API

```
POST https://store.weixin.qq.com/shop-faas/mmeckolnode/square/getGetAgencySquareDetail?lang=zh_CN
Content-Type: application/json
Credentials: include

Request Body:
{
  "ilinkUserId": "d283f865-...@finderecmcn@im.ilinkapp_06000091c663bb"
}

Response:
{
  "code": 0,
  "data": {
    "detail": {
      "baseInfo": { ... },
      "coreData": { ... },
      "industryInfos": [ ... ],
      "coBrandInfo": { ... },
      "succCases": [ ... ]
    }
  }
}
```

⚠️ **Endpoint name**: Must be `getGetAgencySquareDetail` (double "get"). `getSupplierAgencyDetail` returns 404.

## Detail Page URL

```
https://store.weixin.qq.com/shop/ec-agency/market/detail?id={ilinkUserId}&type=SUPPLIER
```

## SSR Data Endpoint

```
GET https://store.weixin.qq.com/ec-agency/ssr/market/home/
```

This is the SSR HTML endpoint for the market home page.

## Session Auth

The session token is stored as a cookie from the Playwright `storage_state`. All API calls must use `credentials: 'include'` to pass the auth cookies automatically. The cookies file is at `/tmp/weixin_store_state.json`.

## Rate Limiting

- After ~100 pages of continuous calls, API may return `code: non-zero` with message `null`
- Fix: `time.sleep(0.3)` between pages, and `time.sleep(5)` on error before retry from same offset
