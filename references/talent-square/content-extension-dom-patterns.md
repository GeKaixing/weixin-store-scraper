# Chrome 扩展 DOM 提取模式 & 字段添加工作流

本文档记录微信小店达人信息采集助手 Chrome 扩展的 DOM 提取模式，以及添加新字段的标准工作流。与 Playwright 爬虫共享相同的数据源（微信小店达人详情页），但提取方式不同。

## 通用规则

- **不修改现有功能** — 新字段使用增量添加，不改变现有提取逻辑、表单顺序、表格列排序
- **每个字段需要 6 处对称修改**（见下方工作流）
- **跨域数据共享** — `chrome.storage.local` 是扩展级别存储，在 `store.weixin.qq.com` 写入、在 `doc.weixin.qq.com` 读取，天然跨域

## 详情页字段提取方式

### 方式 A: 文本标签提取（`findByLabels`）

适用于页面文本中有显式标签+值的情况。在 `labels` 对象中添加标签名列表，然后在 `extractCreatorInfo()` 中调用。

### 方式 B: DOM 元素选择器提取

适用于页面有特定 CSS class 的元素。使用 `querySelectorAllDeep()` 配合 class 属性选择器，过滤可见性和排除扩展自身的根元素。

**示例 — 合作方式：**
```javascript
function findCooperationMethods() {
    const nodes = querySelectorAllDeep('[class*="whitespace-nowrap"][class*="text-[14px]"]');
    const methods = nodes
      .filter((node) => isVisible(node) && !node.closest(`#${ROOT_ID}`))
      .map((node) => cleanValue(node.textContent || ""))
      .filter((text) => text && text.length <= 10 && /^[\u4e00-\u9fa5]+$/.test(text));
    const unique = [...new Set(methods)];
    return unique.join("、");
}
```

**关键 class 模式：** `whitespace-nowrap text-[14px] text-[rgba(0,0,0,0.9)]` — 达人详情页的合作方式标签（直播、短视频等）

### 方式 C: 粉丝特征子字段提取（`findFanProfileField`）

粉丝特征区域包含 6 个子字段，各自有标签/值/百分比的三行结构：

```
性别 ← label (i)
女   ← value (i+1)
占   ← placeholder (i+2)
94.1% ← percentage (i+3)
```

```javascript
function findFanProfileField(text, labelName) {
    const lines = getTextLines(text);
    const start = lines.findIndex((line) => line.includes("粉丝特征"));
    if (start < 0) return "";
    const index = lines.findIndex((line, lineIndex) => lineIndex > start && line === labelName);
    if (index < 0) return "";
    const value = lines[index + 1] || "";
    const percent = lines[index + 2] && /^(?:占\s*)?[\d.]+%$/.test(lines[index + 2]) ? lines[index + 2] : "";
    return value ? `${value}${percent ? ` ${percent}` : ""}` : "";
}
```

**6 个子字段及其 labels：**

| 字段名 | label | 示例值 |
|--------|-------|--------|
| `fanProfileGender` | 性别 | 女 94.1% |
| `fanProfileAge` | 年龄 | 40岁-49岁 39.7% |
| `fanProfileRegion` | 地域 | 三线城市 22.4% |
| `fanProfileDemographic` | 人群类别 | 小镇女 39% |
| `fanProfileShopping` | 购物偏好 | 教育培训 90% |
| `fanProfilePurchasing` | 购买力区间 | ￥50以下 95.3% |

### 方式 D: URL 参数提取

从 `location.href` 提取 finderId/authorId 等参数。

## 添加新字段的标准工作流

每个新字段需要 6 处修改，按此顺序执行：

1. **labels 或提取函数** — 添加提取逻辑（`findByLabels` + `labels` 条目，或独立的 `findXxx()` 函数）
2. **`extractCreatorInfo()`** — 在 return 对象中添加新字段
3. **`copyFormData()`** — 添加表单值读取
4. **`createSheetRow()`** — 添加表格行值
5. **`togglePanel()`** — 添加表单填充行
6. **`mount()` — form.append()** — 添加 UI 输入框

### 表单字段命名约定

- HTML id: `cia-{kebab-case-field-name}`
- 字段键: camelCase（如 `cooperationMethod`）

### 手动编辑表单后的数据流向

当用户在表单中手动修改了字段值（如微信号、手机号），必须将表单值合入自动提取的结果，否则保存到 storage 的是重新从页面提取的旧值。

```javascript
// 在 addCurrentCreatorToSheet() 中：
const extracted = extractCreatorInfo();
const formValues = readFormInfo();    // ← 读取表单所有字段
const info = { ...extracted, ...formValues };  // ← 表单值覆盖自动提取
```

**`readFormInfo()` 的实现：** 遍历所有 `#cia-*` input 元素的 `.value`，返回完整的 info 对象。`...formValues` 放在展开运算符的最后，确保用户手动修改的字段覆盖自动提取值，未修改的保留自动提取结果。

## 自动填入表格（跨域流程）

```
[store.weixin.qq.com]                     [doc.weixin.qq.com]
        |                                        |
  用户点击 "添加到达人跟进表"                         |
        |                                        |
  1. revealContactInfo()                          |
  2. extractCreatorInfo()                         |
  3. readFormInfo() + merge                        |
  4. storageSet(storageKey, payload)  ──────────>  |
  5. storageSet(_autoFill, true)   ──────────>  |
  6. window.open(followSheetUrl)                  |
        |                                        |
        |                                    7. mountSheetAssistant()
        |                                       └─检测 autoFill=true
        |                                         └─等"添加一行"按钮出现(60×300ms)
        |                                         └─等 storage 数据到达(30×200ms)
        |                                         └─fillSheet(status)
```

### 关键点

- **先存数据再开窗口** — `storageSet` 必须 `await` 完成后再 `window.open`
- **等待 DOM 就绪** — 轮询"添加一行"按钮（最长 60×300ms=18s），不等固定时间
- **等待数据同步** — 轮询 storage（最长 30×200ms=6s）
- **`dispatchPaste`** — 通过 `ClipboardEvent("paste")` 模拟粘贴，把 tab 分隔的表格行数据贴入 Canvas 表格

## 表头动态映射（已废弃 — Canvas 渲染限制）

**⚠️ 此方法不可行：企业微信智能表格使用 Canvas 渲染，DOM 中不存在表头文本元素。**

曾尝试实现按表头扫描 → 动态排列数据的方式：
1. 定义 `HEADER_FIELD_MAP` 映射表头标签到数据字段名
2. 用 `querySelectorAllDeep` + `isVisible` 在页面中查找匹配标签的 DOM 元素
3. 按 `getBoundingClientRect().left` 排序，构建 tab 分隔行

**失败原因：** 用户在 DevTools 控制台验证确认 `document.querySelectorAll("button,[role='button'],div,span")` 中没有任何包含"粉丝"等表头文本且 `isVisible` 为 true 的元素。表格头是 Canvas 绘制的像素，不是 DOM 文本节点。

**当前方案：** 依赖固定列顺序的 `createSheetRow()` + `dispatchPaste` 粘贴。如果表格列增减，手动修改 `createSheetRow()` 中的数组顺序。

## manifest.json 限制

内容脚本只注入到两个域名：
```json
"matches": ["https://store.weixin.qq.com/*", "https://doc.weixin.qq.com/*"]
```
