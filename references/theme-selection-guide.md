# 模版选择指南（Theme Selection Guide）

本技能的所有模版均为**构建期参数**：同一套 fragment JSON 内容，用 `assemble.py` 不同参数构建出不同主题的单文件 HTML。每个产物只含一个主题（保证单文件、0 外部依赖、audit 干净），HTML 内**没有**运行时主题切换按钮。

共 **3 个主题族、4 种产物**。SKILL.md Step 0 规定：默认出 dark；light 按需或为打印而出；master 为第三主题族（"作为其中一种模版参与"，不取代任何默认值）。

## 一览表

| 模版 | 构建命令 | 输出文件 | 底色/主色 | 页眉页脚 | 适用场景 |
|---|---|---|---|---|---|
| dark 默认版 | `python3 assemble.py` | …金融科技演示.html | 深蓝 `#060e1b`，青 `#64e1e8`/金 `#d8b77d` | 顶部品牌条；控制栏默认隐藏 | 大屏投影、科技感展示、奖项材料 |
| light 白底版 | `python3 assemble.py light` | …白底版.html | 白底，冷蓝 `#0b7f8e`/金棕 `#a2761a` | 同 dark 结构 | 打印、白天明亮会场、分发阅读 |
| master 母版版（独立Logo） | `python3 assemble.py master` | …母版版.html | 白底，品牌红 `#B7002E`/条带灰 `#F2F2F2` | 红章节块+灰章节标题带+独立Logo；红块页脚带 | 对齐公司 PPT 模版的正式对外/汇报材料 |
| master 母版版（组合Logo） | `python3 assemble.py master combo` | …母版版-组合Logo.html | 同上 | 同上，Logo 换组合标、标题带避让加宽 | 需要部门+公司组合标识的场合 |

## 逐模版解读

### dark 默认版
技能的 house style：深蓝底、青金双色、环境星野与网格、HUD 角框（`.diagram-frame`）、字距拉开的 kicker。视觉最炫，适合暗场投影。shell.html 的 CSS 默认变量即 dark，它是所有主题的基底。

### light 白底版
通过 `SHELL_LIGHT` 精确字符串对 remap 生成（assemble 断言每对 old 串在 shell 中恰好出现一次；改 shell 时必须同步补 remap 对，否则 assert 失败）。青/金换冷蓝/金棕、面板转白渐变、网格overlay 关闭。存在意义：打印与明亮环境——深色底打印费墨且发灰。

### master 母版版
把《技术研发部PPT模版-20250121 打印版》的 slideMaster 移植成的第三主题。实现分层：
1. 复用 light 白底管线（`white = light or master` 共享白底分支与 Logo 换标）；
2. 叠 `MASTER_SWAP` 把冷蓝/金棕单色化为品牌红/灰；
3. 注入 `MASTER_CSS` 母版 chrome + base64 内联 Logo（`templates/master/logo_solo.png` / `logo_combo.png`）+ mhead/mfoot 标记。

版式语言与 dark/light 完全不同：
- 页眉 = 红色斜体章节号方块（67×67，`#b7002e`）+ 灰色章节标题带（显示**章节标题**"夯基/投研/财富/智能"，非页标题）+ 右侧 Logo；
- 页脚 = 红方块 + "稳健理财 值得信赖" + 英文公司名灰带；页码灰字在页脚带上方；
- 封面/章节/结尾页隐藏整套 chrome 走全出血版式，h1 换衬线；
- 内容页隐藏 kicker 眉题（PPT 母版内容页无眉题，灰带已承担章节标签），h1 紧贴标题带下缘（top:116），正文占满 216–776 的 560px 全高。

完整几何/令牌见 `references/master-theme.md`。

### master 组合Logo 变体
对应第二个模版文件（组合Logo）：Logo 换 `logo_combo.png`（1200×176），标题带右缘从 214 收到 330 避让，Logo 改 top:13/h:41。两个 PPT 模版文件（独立Logo/组合Logo）与两个变体一一对应。

## 所有主题共享的行为

选哪个模版都不影响：入场动画与 `data-anim`、演讲者模式（P 键）、逐字稿 notes、Overview（O 键）、触摸滑动、预览模式 `?preview=N`；以及分发约定——底部控制栏默认隐藏、`?ctrl=1` 恢复（见 enhancements-v3.md §6）。

审计约定统一：每次改 shell/assemble 后 **dark+light+master(+combo) 同构建**、逐份 `python3 audit_html.py <真实文件名>`（传主题关键字会 FileNotFoundError），断言 external_dependencies=0、storage_apis=0、valid_embedded_images=true。

## 选择决策

1. 未指定 → **dark**（Step 0 默认）。
2. 要打印 / 白天明亮会场 / 纯阅读分发 → 加出 **light**。
3. 场合需与公司 PPT 模版视觉一致（正式汇报、对外印发、评奖材料用公司统一版式）→ **master**；按该场合用独立标还是组合标选 `master` 或 `master combo`。
4. 内容片段共享，同一次内容更新可多条命令并行出齐多版本，按场景分发；切勿用某主题输出覆盖另一主题文件。

## 坑

- master 内容页**不要压缩 body 高度**：多页实测需要满 560px，压到 530 会溢出（逐页断言脚本见 master-theme.md"校验"）。
- master 灰带 left 必须 104（与红块右缘齐平）：留白缝会让底层红色 kicker 从缝里漏出。
- light/master 下白色透明 Logo 会消失，topbar 与结尾页已换红黑标。
- 改 shell 中按主题区分的 CSS 时，同步补 `SHELL_LIGHT` remap 对；master 专属样式只进 `MASTER_CSS`，不进 shell。
