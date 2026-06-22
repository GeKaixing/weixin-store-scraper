# Industry ID Mapping for 微信小店 Agency Market

## 14 Industry Categories

| ID | Chinese Name | English |
|----|-------------|---------|
| 1 | 服饰家居 | Fashion & Home |
| 2 | 玉翠文玩 | Jade & Antiques |
| 3 | 食品生鲜 | Food & Fresh |
| 4 | 个护美妆 | Personal Care & Beauty |
| 5 | 图书课程 | Books & Courses |
| 6 | 数码家电 | Digital & Appliances |
| 7 | 家清日用 | Home Cleaning & Daily |
| 8 | 家装建材 | Home Renovation & Building Materials |
| 9 | 宠物绿植 | Pets & Plants |
| 10 | 母婴玩具 | Maternity & Toys |
| 11 | 本地生活 | Local Life Services |
| 12 | 会员充值 | Membership Top-up |
| 13 | 教育培训 | Education & Training |
| 14 | 汽摩电动 | Auto & Electric Vehicles |

## Notes

- IDs map to the `value` attribute of the industry checkbox input on the page
- In the list API response, `industryInfos` contains `[{id: number, ...}]`
- In the detail API response, `industryInfos` also contains `gmvRate` (GMV占比, 0-1)
- An agency can have 1-3 industries typically
- Some agencies have `占位` (placeholder) instead of real industries — these may have empty `industryInfos`
