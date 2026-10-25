# nein_paper_translate · 三栏对照阅读器 Skill

> 本仓库的其它 skill 见[根 README](../README.md)。

把一篇外文 PDF / 长文章变成**单个不依赖网络的 HTML 精读页面**：左栏原文、中栏逐句译文、
右栏每个单词的单独释义；点原文即定位译文，三栏各自独立滚动，并内置读书笔记与「读书感悟」汇总导出。

这是一个 [Qoder](https://qoder.com) Skill：装好之后，用自然语言让 Agent 替你完成
「抽文本 → 切句 → 逐词注释 → 校验 → 生成 → 浏览器验收」的整条流水线。

## 功能

| 能力 | 说明 |
| --- | --- |
| 三栏对照 | 原文 / 逐句译文 / 逐词释义，按逻辑句子切分，脚注与题录信息单独排版 |
| 点击定位 | 点左栏某句 → 中栏滚到该句译文；点中栏 → 左栏定位原文；键盘 `j/k`、导航、搜索则两栏都跟 |
| 逐词高亮 | 第三栏每条释义悬停即在原文中高亮对应片段，点击锁定，`Esc` 解锁 |
| 三栏独立滚动 | 宽屏（≥1081px）下每栏在自己的容器里滚，栏标题 sticky；窄屏自动退回整页滚动 |
| 读书笔记 | 逐条点评（可只点评选中的一段文字），自动存 `localStorage`，句子旁标 `●` |
| 感悟汇总 | 一键生成 Markdown 读书感悟（按节分组：原文 / 聚焦片段 / 译文 / 点评 + 整体感悟），可复制或下载 `.md` |
| 搜索 | 输入英文词回车逐句跳转，命中句两栏同时高亮 |
| 深色模式 | 跟随系统 `prefers-color-scheme` |

生成的 HTML 不含任何外部依赖，直接双击打开即可。

## 安装

```bash
git clone https://github.com/AZZZZ-P/Nein-s-laboratory.git /tmp/nein-lab
cp -R /tmp/nein-lab/nein_paper_translate ~/.qoder-cn/skills/
```

重启会话或执行 `/skills reload`，用 `/skills list` 确认能看到 `nein_paper_translate`。
也可以放到项目里的 `.qoder/skills/nein_paper_translate/` 只对单个项目生效。

## 用法

### 让 Agent 来做

```
/nein_paper_translate /path/to/paper.pdf 只做正文和摘要，参考文献从略
```

或者直接描述需求（「这篇英文 PDF 帮我做逐词对照翻译」）。

**不会来回追问**：逐词范围（正文逐词、参考文献从略）、中文标题、输出文件名都有内置默认，
给出路径就一路做到底——逐节写 `data.json` → 校验修到 `miss=0 backward=0 empty_gloss=0`
→ 生成 HTML → 浏览器验收 → 交付。想改范围或标题，说一声即可重跑。

### 手动跑（已经有 data.json 时）

```bash
python3 scripts/build_reader.py _work/data.json --check          # 只校验并分类报告问题词条
python3 scripts/build_reader.py _work/data.json -o 三栏对照阅读.html
```

生成器只做一件事：把紧凑 JSON 注入 `assets/reader-template.html` 里唯一的 `__DATA__` 占位符。

## 数据格式

```json
{
  "meta": {
    "titleEn": "Paper title", "titleZh": "中文标题",
    "slug": "paper-slug",
    "byline": "作者 · 期刊/年份 · 说明",
    "cite": ["汇总 Markdown 里的原文引用行"]
  },
  "sections": [
    { "id": "1. Introduction", "head": { "zh": "1. 引言", "en": "1. Introduction" },
      "paras": [
        { "key": "p1", "kind": "para",
          "sents": [
            { "en": "The firm maps stakeholders.",
              "zh": "这家公司把利益相关者一一 mapped 出来。",
              "t": [["The", "冠词"], ["firm", "公司"], ["maps", "绘制…的图谱"], ["stakeholders", "利益相关者"]] }
          ] }
      ] }
  ]
}
```

`meta.slug` 决定笔记的存储键与导出文件名，同一篇文章换 slug 会读不到旧笔记。
`paras[].kind` 取 `para`（正文）/ `footnote`（脚注）/ `meta`（题录信息）。

逐词数组 `t` 的三条硬规则（详见 `references/data-format.md`）：

1. 顺序严格从左到右 —— 乱序会导致高亮游标错乱，校验报 `BACKWARD`；
2. 词面必须能在句中找到 —— 定位用「压缩索引」，只保留 Unicode 字母数字，
   所以 `so-called`、`vis-à-vis`、`and/or`、全角括号都能正常命中；
3. 一条只对应一个连续片段 —— 别把后面的单词塞进上一条的词面或释义里。

## 目录

```
SKILL.md                        Agent 的工作流（7 步）与功能底线
assets/reader-template.html     阅读器模板，唯一占位符 __DATA__
scripts/build_reader.py         校验逐词定位 + 注入生成单文件 HTML
scripts/extract_pdf.py          PDF 抽文本（PyMuPDF → pdfplumber → pdftotext）
references/data-format.md       data.json 字段、t 的硬规则、噪声修复对照表
references/reader-internals.md  布局/滚动/点击路由/笔记的实现不变量与验收清单
```

## 已知限制

- 三栏独立滚动只在 ≥1081px 宽度生效，更窄的窗口退回整页滚动（三栏纵向堆叠）。
- 部分浏览器禁止 `file://` 页面写 `localStorage`，此时笔记只在本会话有效，
  页面会在面板底部明确提示，请用「下载 .md」备份。
- `scripts/extract_pdf.py` 依赖三种抽取器之一，都没装时它会提示改用 Agent 的 Read 工具读 PDF（不会崩）。
- 逐词覆盖度越高，翻译成本越高；参考文献通常不做逐词，只在正文里标注。

## License

MIT —— 见仓库根 `LICENSE`。
