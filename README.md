# Nein's laboratory

把自己反复用到的工作流沉淀成 Qoder Skills，一个子目录一个 skill。

## 已收录

| Skill | 说明 |
| --- | --- |
| [`nein_paper_translate`](nein_paper_translate/) | 外文 PDF / 长文章 → 单文件 HTML「三栏对照阅读器」：原文 / 逐句译文 / 逐词释义，点原文定位译文、三栏独立滚动、内置读书笔记与「读书感悟」Markdown 汇总 |

每个 skill 目录里都有自己的 `README.md`，写清了它的功能、数据格式与维护要点。

## 安装

```bash
git clone https://github.com/AZZZZ-P/Nein-s-laboratory.git /tmp/nein-lab
cp -R /tmp/nein-lab/nein_paper_translate ~/.qoder-cn/skills/
```

或点 `Code → Download ZIP`，解压后把想要的 skill 文件夹整个放进 `~/.qoder-cn/skills/`
（只想对单个项目生效就放进项目里的 `.qoder/skills/`）。

放好后重启会话或执行 `/skills reload`，用 `/skills list` 确认。**目录名必须与该 skill
`SKILL.md` frontmatter 里的 `name` 一致**，否则加载器不认。

## 使用

```
/nein_paper_translate /path/to/paper.pdf
```

范围（正文逐词、参考文献从略）、中文标题、输出文件名都按 skill 内置默认自决，不会中途追问。

## License

MIT —— 见 [`LICENSE`](LICENSE)。
