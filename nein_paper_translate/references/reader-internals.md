# 阅读器实现约定与验收清单

`assets/reader-template.html` 是成品模板，文档信息全部来自 `DATA.meta`。
修改模板时下面这些不变量必须保持，它们都是踩过的坑。

## 1. 三栏独立滚动

```css
body{height:100vh;overflow:hidden}
.grid{grid-template-columns:1.18fr 1fr .92fr;height:calc(100vh - var(--headh,80px))}
.col{height:100%;overflow-y:auto;overscroll-behavior:contain}
.colhead{position:sticky;top:-1px}                 /* 栏标题跟着本栏滚 */
@media (max-width:1080px){                          /* 窄屏退回整页滚动 */
  body{height:auto;overflow:auto}
  .col{height:auto;overflow:visible;padding-bottom:70vh}
  .colhead{top:var(--headh,80px)}
}
```

- `--headh` 由 JS 在载入和 `resize` 时写成顶部工具条的实际高度。
- **中栏必须有 class**：`<section class="col colZ" id="colZ">`。所有中栏规则都挂在
  `.colZ` 上；只给 id 会导致中栏样式全部失效（用截图才发现，DOM 检查看不出来）。
- 打开笔记面板时 `body.panel-on{padding-right:min(430px,92vw)}`，窄屏下必须重置为 0，
  否则整页被挤扁。

## 2. 定位滚动 scrollCol

```js
const cr = c.getBoundingClientRect();
const top = Math.max(cr.top, 0), bot = Math.min(cr.bottom, window.innerHeight);  // 栏矩形 ∩ 视口
if (r.height <= boxH - 2*pad && r.top >= top+pad && r.bottom <= bot-pad) return; // 已完整可见就别动
el.scrollIntoView({behavior: dist < boxH*0.8 ? 'smooth' : 'auto', block:'center'});
```

两个必须点：

- **可见区域要和窗口视口取交集。** 只按栏矩形判断，在窄屏回退（栏高几万 px、不可滚）时会误判
  「已可见」，页面完全不滚。
- **按距离选 behavior。** 跨几万像素的跳转用 `smooth` 时 Chrome 要滚很久，看起来像「点了没反应」，
  必须用 `auto`；短距离才用 `smooth`。

## 3. 点击路由（select(i, from)）

| 来源 | 行为 |
| --- | --- |
| `'en'` 点左栏原文 | 只让**中栏**滚到该句译文，左栏保持原位 |
| `'zh'` 点中栏译文 | 只让**左栏**滚到该句原文 |
| 无 `from`（导航按钮、章节标题、`j/k`/↑↓、搜索回车、笔记「跳到该句」） | 左栏和中栏都定位 |
| `false`（初始化、编辑笔记回填） | 都不滚 |

任何一次换句都把 `#colW`（逐词栏）`scrollTop = 0`，否则新句的词行停在上一句的滚动位置。

## 4. 逐词高亮

`renderWords()` 只重建第三栏，绝不重建左栏（重建会丢掉 `.active`/`.hit`/滚动位置）；
高亮用 `restoreSent(i)` / `markWord(j)` 直接改单条 `.sent` 的 `innerHTML`，
鼠标悬停即高亮、点击锁定，`Esc` 解锁。所有来自数据的文本一律过 `esc()`。

## 5. 读书笔记面板

- 存储：`localStorage['qoder.<slug>.notes.v1']` = `{notes:[{id,gi,si,quote,text,ts}], summary}`；
  读写全程 `try/catch`，失败时 `#pstore` 明确提示「本次会话有效，请用下载 .md 备份」
  （部分浏览器禁止 `file://` 写 localStorage）。
- 点评对象默认是当前句，也可先用鼠标选中左/中栏任意文字（`mouseup` 捕获 → `#selPop` 浮层 →
  「引用选中文字」），选区上限 400 字符且必须落在 `#enRoot, #zhRoot` 内。
- 快捷键：`n` 开关面板，`⌘/Ctrl+Enter` 保存，`Esc` 先关面板再取消锁定。
- 已有点评的句子在左栏加 `●`、中栏加橙色左边框（`.noted`）。
- 「生成读书感悟」拼 Markdown：标题 + `meta.cite` + 按节分组的逐条点评（原文/聚焦片段/译文/点评）
  + 整体感悟段；可复制或下载 `.md`。

## 6. 验收清单（改完必须跑）

1. `build_reader.py data.json --check` → `miss=0 backward=0 empty_gloss=0`。
2. 用 `node:vm` 的 `new Script()` 对内联脚本做语法检查（`node --check` 只能查文件，内联要抽出来）。
3. 浏览器里 `evaluate_script` 断言（截图工具在内置视图常报 `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE`，
   以 DOM/几何断言为主）：
   - `S.length`、`.sent`/`.zh` 数量与句子总数一致；
   - 全量重算 `spans`，不可定位词条数为 0；
   - 模拟 `new MouseEvent('click')` 点一句原文，验证中栏滚动、左栏 `scrollTop` 未变；
   - 点中栏反之；点导航按钮两栏都定位；
   - 笔记面板：写入一条 → `#plist` 计数 +1、`.noted` 出现、localStorage 键名正确 →
     生成 digest → **测完必须 `localStorage.clear()`**，别把测试笔记留给用户。
4. 注意：**模拟点击 `<a href="#">` 会触发 hash 跳转把页面滚回顶部**，即使 handler 里已
   `preventDefault`（合成事件照样跑默认动作）。测导航时先把 `href` 改成 `javascript:void(0)`，
   否则会误判成「滚动失效」。
