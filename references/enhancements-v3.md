# v3 增强特性：动画系统 · 演讲者模式 · 逐字稿

本文档记录从 html-ppt 技能融合进 tianhong-html-deck 的三项增强。所有改动**向后兼容**：
不含 `notes` 字段的旧 fragment JSON、不加 `data-anim` 的旧 body，构建结果与 v2 完全一致。

## 1. CSS 入场动画系统（data-anim）

在 fragment body 的任意元素上加 `data-anim="<name>"` 即可。动画在 slide 变为 `.active` 时自动触发，
离开再回来会重新播放（纯 CSS 选择器 `.slide.active [data-anim=...]` 实现，无需 JS 重触发）。

| name | 效果 | 适用 |
|---|---|---|
| `fade-up` | 从 +32px 上浮淡入 | 段落、卡片入场（默认首选） |
| `rise-in` | +60px 上浮 + blur 消散 | 大标题、hero 文案 |
| `zoom-pop` | 0.6→1.04→1 弹性缩放 | 数字、按钮、CTA |
| `blur-in` | 18px 模糊渐清 | 封面 reveal |
| `fade-left` / `fade-right` | 左右滑入 | 双栏布局的左/右列 |
| `stagger-list` | 子元素逐个上浮（间隔 .1s） | 加在 `<ul>` 或 `.cols` 网格上 |
| `path-draw` | SVG 描边自绘 | 流程图、架构图连线 |

延迟控制：元素上加内联 `style="--delay:.15s"`（或 `.2s/.3s…`）错开节奏。

规则：
- 每页最多 1-2 种动画类型，混 5 种会显得杂乱。
- `stagger-list` 加在**父容器**上，子元素自动按 nth-child 排队。
- 动效开关（M 键 / `no-motion`）和 `prefers-reduced-motion` 会自动禁用全部 data-anim。
- 不要给已经带 `.reveal` 的元素再加 data-anim（shell 的 `.reveal` 是旧的自动入场，二者会叠加）。

示例：
```html
<div class="cols three" data-anim="stagger-list">
  <div class="panel"><h3>权益投研</h3><p>…</p></div>
  <div class="panel"><h3>指数量化</h3><p>…</p></div>
  <div class="panel"><h3>固收+</h3><p>…</p></div>
</div>
<h2 data-anim="rise-in">核心结论</h2>
```

## 2. 演讲者模式（P 键 / footer「演讲者」按钮）

按 **P** 打开一个独立 popup 窗口，内含 4 张磁吸卡片（拖标题移动、拖右下角缩放）：

- **CURRENT** — 当前页 iframe 像素级预览（`?preview=N` 模式加载同一文件，只渲染该页、隐藏 chrome）
- **NEXT** — 下一页预览
- **逐字稿** — 读取当前页 `<aside class="notes">` 的 HTML 内容，大字号可滚动
- **TIMER** — 计时 + 页码 + 上一页/下一页/重置按钮

同步机制：
- 观众窗口 ↔ 演讲者窗口通过 `BroadcastChannel` 双向同步翻页。
- 预览 iframe 加载后发 `preview-ready`，之后翻页走 `postMessage({type:'preview-goto'})`，**不重载、不闪屏**。
- 演讲者窗口内 `← →` 翻页会同步观众窗口；`R` 重置计时；`Esc` 关闭。

注意：卡片布局**仅存内存**（每次打开恢复默认四宫格）。技能审计禁止 localStorage，故不做持久化。

## 3. Fragment JSON 新增 `notes` 字段（逐字稿）

assemble.py 现在读取每个 fragment 的可选 `notes` 字段，输出为 `<aside class="notes">…</aside>`
（放在 slide section 内、footer 之后）。该 aside 在观众页 `display:none`，仅演讲者窗口可见。

```json
{
  "3": {
    "title": "投研科技体系",
    "kicker": "RESEARCH TECH",
    "subtitle": "…",
    "body": "<div …>…</div>",
    "quote": "…",
    "notes": "<p>投研这一块，我们覆盖了<strong>权益、指数量化、固收和固收+</strong>四条线。</p><p>每条线都有对应的科技支撑平台。</p>"
  }
}
```

逐字稿写作三原则（沿用 html-ppt 的 presenter-mode 规范）：
1. **不是讲稿，是提示信号** — 加粗核心词（`<strong>` 渲染为金色），过渡句独立成段。
2. **每页 150–300 字** — 2–3 分钟/页的节奏。
3. **用口语，不用书面语** — "因此"→"所以"，"该方案"→"这个方案"。

notes 是**原始 HTML**（不转义），可含 `<p>/<strong>/<em>`；不要放 `<script>`。

## 4. 图片容器 .img-frame（新增通用组件）

替代裸 `<img>`，由 frame 控制裁切与宽高比：

```html
<figure class="img-frame"><img src="shot.png" alt=""></figure>
<figure class="img-frame contain" style="--img-ratio:4/3"><img src="diagram.svg" alt=""></figure>
```

- `.img-frame` 默认 `object-fit:cover`（裁切填满）；**截图/架构图/logo 一律加 `.contain`**（letterbox 不裁切）。
- `--img-ratio`（默认 16/10）调宽高比；`--img-pos` 调裁切焦点。
- 子元素 `.img-scrim`（底部渐变压暗）、`.img-cap`（图注）、`.img-tag`（角标 pill）。
- 白底版自动 remap：frame 底色 `#0a1520`→`#eef2f5`，角标文字转白。

## 5. 预览模式（?preview=N）

URL 带 `?preview=N` 时 shell 进入预览模式：`body.preview-mode` 隐藏 footer/topbar/progress/ambient，
只渲染第 N 页，且监听 `preview-goto` postMessage 切换页。这是演讲者 iframe 的实现基础，
也可用于外部工具单独截取某一页（无 chrome 干扰）。

## 6. 控制栏默认隐藏（?ctrl=1 恢复）

分发版默认不带底部控制栏：shell 顶层 CSS `.footer,.progress-track{display:none!important}`，
进度条一并隐藏，画面只留内容。URL 带 `?ctrl=1` 时 body 加 `show-ctrl` 类恢复控制栏
（`body.show-ctrl:not(.preview-mode) .footer{display:flex!important}`），供现场交互/调试用。
键盘快捷键（←→/O/S/P/M/F/H）不受影响，仍全部可用。
验证方式：headless 截图后取底部 50px 条带统计亮像素，默认应为 0、`?ctrl=1` 应显著大于 0。

## 兼容性清单

- 旧 fragment（无 notes）→ 正常构建，无 aside 输出。
- 旧 body（无 data-anim）→ 仅保留原有 `.reveal` 自动入场，视觉不变。
- SHELL_LIGHT 已补两条 remap（`.img-frame` 底色、`.img-tag` 文字色），双主题构建均过 audit。
- 审计约束：全程无 localStorage/sessionStorage；单文件、0 外部依赖不变。
