# Fullfold / Quiet.md 写入偏好

适用于把已有 Markdown 写进 Fullfold 库（`fullfold-cli`），或在库内新建/改写笔记。规则按 0.1.4 实测；版本变化时以 `fullfold-cli capabilities --json` 和实际回读为准。

## 库与文件

- 库根下笔记是普通 `.md`，图片在库根 `assets/`，附件在 `assets/files/`；笔记内用相对路径引用，如 `../../../assets/<hash>.jpg`（深度按所在目录算）。
- 笔记标题就是文件名；正文不要再写与文件名同名的首个 `#` 标题，否则标题重复显示。
- 写入一律走 `fullfold-cli`，不直接编辑库内 `.md`、`.canvas`、`.quiet/**`；写前先读，带 `--expect sha256:…`。

## 图片与图注

- 图片行必须**独立成段**（前后各一个空行）。与图注挤在同一段（如 `![](...)` 后跟硬换行再接 `FIGURE 1.1`）时，解析器会整行丢弃图片。
- 图注要进图片块的 `caption` 字段，而不是正文普通段落。可直接写富 HTML：

```html
<div data-quiet-version="1" data-quiet-block="image" data-quiet-align="center" style="text-align:center" data-quiet-source-kind="src" data-quiet-caption="FIGURE 1.1 说明"><figure><img src="../../../assets/x.jpg" alt="FIGURE 1.1 说明"></figure></div>
```

- 子图、示意图、无图注的小图也要写成**同一个富图片块**，只是不带 `data-quiet-caption`：

```html
<div data-quiet-version="1" data-quiet-block="image" data-quiet-align="center" style="text-align:center" data-quiet-source-kind="src"><figure><img src="../../../assets/x.jpg" alt=""></figure></div>
```

  只写 `![](path)` 的图片会按普通正文左对齐，和带图注的居中图混在一起会一左一右，尽量全库统一。
- 多子图（(a)(b)(c)… 各自一张图）时，图注挂到**最近的一张子图**上即可；子图之间允许隔着 `(a)`/`(b)` 这类短标签，导入脚本应按“最近的前一张图”挂载。
- 图注挂上后，紧跟其后的孤立子图标签（`(d)` 独占一行）要一并删掉，否则会在图注下面多出一行 `(d)`。
- 图片居中、宽度、裁剪写进富块的 `data-quiet-align` / 属性；纯 Markdown 表达不了。

## 公式

- 一个公式块只能有一个 `\tag{…}`。`\tag{1}\tag{1.75}` 这类双标签会让解析器整块报“无效公式”，导入前扫描一遍：同一 `$$` 块里出现两个 `\tag` 的，只保留最终编号。

## 表格

- 0.1.4 会把正文里的 HTML `<table>` 当原始文本显示成代码块，不渲染成表格；先确认目标版本能力再决定是否保留 HTML。
- Markdown 管道表会被解析成真正的 `table` 块；代价是合并单元格（colspan/rowspan）被拉平。
- 需要合并单元格又要渲染正常时，只能按应用的富表格块格式写入，先小样验证再批量。

## 标题与编号

- 静态编号（`## 8.1 概述`）和自动编号（`seqAuto`）二选一，不要叠加，否则显示两套号。
- 启用自动编号：用 `doc patch` 的 `replace-block` 写入 `{kind:"heading", level, seqAuto:true, text:"去掉数字的标题"}`；`set` 不支持改 heading 的 `text`。
- 没有编号的标题（符号表、参考文献、前言、目录）保持 `seqAuto:false`，它们**不占号**，不影响后续编号。
- 自动编号按当前文档从 1 重算，不能指定起始章号，也不能跨文档连续编号；正文交叉引用与公式/图表编号不会跟着变。启用前和用户说明这一点。
- 写后用 `doc outline` 或 `doc read --format model` 检查 `seqAuto` 与标题文字，标题上看得见数字不等于启用了自动编号。

## 提示块、分栏与结构

- 提示块、分栏、富图片布局只有块 JSON 能写（`insert` / `replace-block`），普通 Markdown 不行。
- 改已有文档优先块级 `patch`，不要整篇覆盖；`doc write --replace` 会丢掉 callout、分栏、附件、图片裁剪等富内容。

## 验证

- 用 `doc read --format model` 取证：`heading.seqAuto`、`image.fields.caption`、图片 `src` 是否解析到库内文件。
- 不要靠点开正文手动翻看代替验证，也不要点击正文后再按键（会误输入内容）；需要看渲染时只滚动、不落光标。
- 批量写入后核对：笔记数、图片引用可解析数、图注数、标题层级数与来源一致。
- **还要做显示级抽查，计数一致不等于显示正确**：每批至少看首页、符号表、任意 2 处图表，确认表格成表（不是代码块或被拆散）、图注在图下、图片统一居中、公式不出现“无效公式”。发现一类问题先全库扫描再统一修。
- **图注完整性另查**：统计正文里仍是普通文字的 `FIGURE x.y` / `图 x.y` 行（大写 FIGURE、短句、无动词的更可能是图注；`图 x.y 所示…` 多为正文引用）。真孤儿应为 0；多子图中间夹短标签时，图注要挂到最近的前一张图。每次修改图注规则后，对已入库的旧笔记重新扫一遍，不能只修新导入的。
