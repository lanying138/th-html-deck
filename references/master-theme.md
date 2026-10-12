# 母版主题（Master Theme）设计规范

第三主题：把《技术研发部PPT模版-20250121 打印版》的 slideMaster 版式移植为 HTML 生成链路的可选模版（与 dark 默认、light 白底并列）。**不替换任何现有主题**，仅作为 `assemble.py master [combo]` 的额外选项参与。

## 来源与画布换算

- 源：`技术研发部PPT模版-20250121 打印版（独立Logo）.pptx` / `（组合Logo）.pptx` 的 slideMaster + slideLayouts + theme1.xml + media。
- PPT 画布 26.667in × 15in；HTML stage 1600×900。换算系数 = 1600 / 26.667 ≈ **60 px/in**（EMU/914400 得英寸，再 ×60）。
- 所有下方坐标/尺寸均为 1600×900 舞台像素。

## 设计令牌（Design Tokens）

| 令牌 | 值 | 用途 |
|---|---|---|
| 品牌红 | `#B7002E` | chip、页脚方块、强调色、章节大数字 |
| 深红（压暗） | `#9B0027` | 红的次级态 |
| 画布底 | `#FFFFFF` | 内容页背景 |
| 条带灰 | `#F2F2F2` | 标题带、页脚带 |
| 页码/英文灰 | `#888888` | mnum、页脚英文行 |
| 正文灰 | `#656974` | 正文文字（微软雅黑） |
| 标题黑 | `#262626` | 标题带文字、页脚口号 |
| 正文字体 | Microsoft YaHei / PingFang SC | 内容页 |
| 衬线（封面/章节/结尾 h1） | Georgia / Songti SC / SimSun | 大字标题 |

MASTER_SWAP 在 light remap 之上做单色红/灰替换：`#0b7f8e→#b7002e`、`#0e8fa0→#b7002e`、`#0a7c8b→#9b0027`、`#a2761a→#b7002e`、`#b08428→#9b0027`、`rgba(11,127,142,→rgba(183,0,46,`、`rgba(162,118,26,→rgba(183,0,46,`、`#5b6d80→#656974`、`#1e2d3d→#262626`、`rgba(30,60,90,.16)→rgba(0,0,0,.10)`、`#7b8a99→#888888`。

## 版式几何（Chrome Geometry）

### 页眉 mhead（top:41px, h:67px, 全宽, z:6, pointer-events:none）
- `.mchip` 红色方块：left:37, top:0, 67×67, `#b7002e`, 白字斜体衬线 `italic 700 30px/67px Georgia`，居中 = 章节号（01/02/03/04，封面/章节前为空）。
- `.mband` 灰色标题带：left:104（与 chip 右缘 37+67=104 齐平，**不留白缝**，否则底层红色 kicker 会从缝里漏出）, right:214（独立Logo）/ right:330（组合Logo）, h:67, `#f2f2f2`, flex 居中, padding 0 30px；内 `<b>` = **章节标题**（非页标题）`32px 700 #262626 letter-spacing:1px`。
- `.mlogo` Logo：right:37；独立Logo top:7 h:53；组合Logo top:13 h:41。

### 页脚 mfoot（bottom:0, h:47px, `#f2f2f2`, flex 居中, padding 0 37px, z:6）
- `.msq` 红方块 23×23 `#b7002e` margin-right:14。
- `.mslogan` 稳健理财 值得信赖 `23px #262626 letter-spacing:3px weight:500`。
- `.men` TIAN HONG ASSET MANAGEMENT CO., LTD. `margin-left:auto 19px #888888 letter-spacing:1px`。

### 页码 mnum
- right:37, bottom:56（页脚带上方）, `#888888 20px`，两位补零。

### 内容页纵向版式（band 之下填满）
- 内容页（非 cover/chapter/closing）**隐藏 `.kicker`**：PPT 母版内容页没有英文眉题，灰带已承担章节标签；且 kicker 若保留会落在 band 区域（41..108）后面被遮挡/漏色。
- `.slide-header{top:116px}`：h1 紧贴 band 下缘（108）起排，含 subtitle 时到 ~207。
- `.slide-body{top:216px;height:560px}`（216..776）：正文整块在标题栏下方填充，下留 quote（801..843）与页脚带（853..900）。**不要压缩 body 高度**——多页内容实测需要满 560px，压到 530 会溢出。
- 校验脚本逐页断言：kicker 顶 ≥108、header 底 ≤ body 顶、body 底 ≤801、body 子元素不越界（见下"校验"）。

### 整版隐藏规则
封面(cover)/章节(chapter)/结尾(closing) 页为全出血版式，用 `#stage:has(.slide.X.active)` 隐藏 mhead/mfoot/mnum；这三类页 h1 用衬线字体。preview 模式（`?preview=N`）也隐藏 chrome，避免 iframe 内重复页眉页脚。

## 章节号/章节标题来源

assemble.py 从 shell.html 的 topnav `<button data-goto="N">01 夯基</button>` 解析章节起点与标签，`chapter_of(n)` 返回 `(chip, ctitle)` 写入每页 data.pages[n]；shell 的 go() 用 `data.pages[n].chip / .ctitle` 实时填充 mchip/mband，回退为 `[3,10,24,34]` 计数。**mband 必须显示章节标题**，与页 h1（页标题）区分，避免重复。

fragment 页可用可选字段 `"chip"` / `"ctitle"` 覆盖默认章节值（assemble 中 `'chip' in d` 优先）。用于章前页：第 2 页设 `"chip":"序"`、`"ctitle":"一条主线：关于科技与AI的四个问题"`（原 PPT 该页 band 原文），否则 ctitle 为空时 shell 回退到页标题，band 会与 h1 重复。

## Logo 资源

- `templates/master/logo_solo.png`（独立Logo，472×152）与 `logo_combo.png`（组合Logo，1200×176），base64 内联进 `.mlogo`。
- `combo` 参数切换组合Logo并加宽 mband right 到 330。

## 调用方式

```bash
python3 assemble.py master          # 母版版（独立Logo）
python3 assemble.py master combo    # 母版版（组合Logo）
python3 assemble.py                 # dark 默认（回归）
python3 assemble.py light           # light 白底（回归）
```

输出：`outputs/天弘基金-科技创造价值-金融科技演示-母版版[-组合Logo].html`。

## 校验

- 每个输出跑 `audit_html.py <真实文件名>`（传主题关键字如 light/master 会 FileNotFoundError），断言 external_dependencies=0、storage_apis=0、valid_embedded_images=true。
- shell/assemble 改动后 dark+light+master 三版同 build 回归并各 audit。
- 截图用 headless Chrome `--window-size=1600,900 --force-device-scale-factor=1`，逐页 `window.presentation.go(n)`（1-based）+ `setMotion(false)` 后 captureScreenshot；重点核对 mband=章节标题、mchip=章节号、封面/章节页 chrome 隐藏。

## 坑

- mband 若误填页标题会与 h1 重复（曾现 p4 双"业务差异化，技术通用化"）；务必用 ctitle。
- 白底/母版下白色透明 Logo 会消失，topbar 与结尾页已换红黑标；mlogo 用独立/组合红标 PNG。
- `#stage:has(...)` 依赖 :has()，现代 Chrome/Safari 支持；旧浏览器降级为 chrome 常显（可接受）。
- MASTER_SWAP 作用于 final（含 remap 后 shell），顺序在 light remap 之后，勿颠倒。

## 移植到 lean/项目专属 assembler（2026-09-26 · 农银理财 32p deck）

当项目用的是精简版 assemble.py（非 canonical 45p 骨架）时，把 master 主题移过来按下面顺序接线，
每一步都易踩坑，逐项核对：

### 注入顺序（严格）
1. `shell = remap_shell(shell)` — 白底 shell token 替换。
2. 在 arch EXTRA_CSS 标记处注入项目组件 CSS（如 arch_lib.css）；`if white: arch_css = remap_inline(arch_css)`
   —— arch_lib 里是 rgba 字面量（rgba(12,34,53,.55) 面板底、rgba(100,225,232,*) 青、rgba(216,183,125,*) 金、
   hex #cfe9ee/#e8d6b0/#dbf4f7/#06202a），canonical 只 remap fragment body，不移植就会漏改这些库内色。
3. splice `__SLIDES__` / `__DATA__`。
4. `final = MASTER_SWAP(final)` — 红灰单色化，作用于含 remap 后 shell 的 final。
5. `MASTER_CSS` 插到第一个 `</style>` 前。
6. body 加 class `theme-master`；mhead 插到第一个 `<div id="stage">` 后；mfoot 插到第一个
   `<div class="progress-track"` 前。
7. ctrl-script 用 `final.rfind('</body>')` splice（见坑）。

### 关键坑
- **`</body>` 用 rfind 不要用 replace(...,1)**：shell.html 里第一个 `</body>` 位于 presenter-window 的
  JS 字符串内部；`replace('</body>', '<script>…</script></body>', 1)` 注入的 `</script>` 会截断主脚本，
  全 deck JS 死（无 slide .active → 全空白、mchip/mband 空）。症状＝只渲染 chrome、正文全无。
  修复＝`_idx = final.rfind('</body>'); final = final[:_idx] + script + final[_idx:]`。
- **面板泥灰**：INLINE_FAM 前缀替换保留 alpha，白底上 rgba(44,76,108,.55) 会成脏板岩。remap_inline 里加
  background-only 塌缩：`re.sub(r'background:rgba\(44,76,108,(\.\d+|…)\)', λ α≥.3→.06)`；border 保留 alpha。
- **.slide-quote 白底看不清**：移植 SHELL_LIGHT 表常漏 canonical 的
  `('gap:16px;color:#b7cbd4;','gap:16px;color:#41546a;')`，补回。
- **语义色不要单调化**：表格红✗/琥珀△/绿✓保留（可读性），MASTER_SWAP 只碰品牌青金与中性灰。
- **控制栏**：`.footer,.progress-track{display:none!important}` 入默认；`?ctrl=1` → body.show-ctrl 恢复。
- **打印 chrome 逐页重复**：#stage 级绝对定位 mhead/mfoot 不会逐页重复；每个 content section 内嵌
  print-only `.pmhead/.pmfoot`（screen:none, print:block, 全局隐藏），@media print 切换。

### lean 移植的验证清单
- mchip 零填充 '01'…'04'，空 chip 传 '\u00a0'（否则 go() 回退 canonical 章节号显红字数字）。
- mband = 章节标题（ctitle）非页标题；封面/章节/结尾页 chrome 隐藏（`:has()`）。
- 面板为淡 tint 非泥灰；.slide-quote 白底可读。
- dark 回归：assembler 重写后 diff 若只在 deck-data（chip 零填充、ctitle 新增），slide markup 不变即安全；
  截图 dark p3 目检确认。
- 每个交付 build 各跑一次 audit_html.py（传真实文件名）。
