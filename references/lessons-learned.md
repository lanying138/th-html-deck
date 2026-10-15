# lessons-learned（th-html-deck 增强版踩坑记录）

> 只记录坑与边界，不改 SKILL.md 主文档。功能说明见 enhancements-v3.md。

## preview 模式（?preview=N）不能 remove() dialog
- 现象：演讲者弹窗里 CURRENT/NEXT 预览 iframe 全黑，只剩深色背景。
- 根因：preview 初始化早期执行 `document.querySelectorAll('dialog').forEach(d=>d.remove())`，
  但后续顶层 UI 接线（如 `$('#overview-search').addEventListener(...)`、`#zoom-in`、`#source-image-tab` 等）
  依赖 dialog 内部节点；节点被移除后取到 null 抛 TypeError，导致脚本中断，
  位于更后面的 preview 初始化分支（设置唯一 active slide、监听 preview-goto）永远不执行 → 无 active 页 → 黑屏。
- 修复：preview 模式只加 `body.preview-mode` class，不 remove dialog；用 CSS
  `body.preview-mode dialog{display:none!important}` 隐藏（closed dialog 本就 display:none）。
- 教训：单文件 shell 里"为干净而删 DOM"要警惕顶层接线顺序；隐藏优于删除。

## 演讲者弹窗同步在 file:// 下不能只靠 BroadcastChannel
- file:// 属 opaque origin，BroadcastChannel 在部分浏览器/场景不可靠。
- 修复：双通道 —— BroadcastChannel + `window.opener.postMessage` / `presenterWin.postMessage` 兜底；
   audience 侧与 presenter 侧都同时监听两种消息。

## 演讲者弹窗卡片布局禁用 localStorage
- audit_html.py 断言禁止 localStorage/sessionStorage（storage_apis 必须为 0）。
- 因此卡片拖拽/缩放布局只能内存态：`readLayout(){return defaultLayout()}`、`saveLayout(){}`；
  "重置布局"按钮直接 `applyLayout(defaultLayout())`。

## headless 截图取证注意
- `window.presentation.go(n)` 的 n 是 1-based（内部 go(n-1)），抓第 N 页要传 N，传 N-1 会整体错位一页。
- 抓"动画进行中"帧：先 go(1) 复位、再 go(N)、wait 指定毫秒后截图；stagger-list 约 300ms、path-draw 约 350ms 效果最明显。
- 抓演讲者弹窗：`openPresenter()` 后等 ~1.5s，用 Target.getTargets 找 title 含"演讲者"的 page target，
  attach 后 Page.captureScreenshot；弹窗内 iframe 需 preview 模式正常渲染才有画面。

## 白底原生 fragment 出 dark 版：DARK_SWAP + comp_dark.css 双轨
- fragment body 是白底原生内联色（#b7002e/#fff/#262626/rgba(183,0,46,.05)…有限集合）时，
  不要改 fragment，而是在 assembler 里加有序 DARK_SWAP（specific→catch-all）做字符串替换，
  另写一份 comp_dark.css 复用同一套 class 语法换 token；EXTRA_CSS 按 dark 选文件。
- 顺序很重要：先换带 context 的长串（如 'background:#b7002e;color:#fff'），最后才换裸 hex，
  否则裸 #b7002e 会先吃掉长串里的子串。
- Logo：dark 需要白色透明标；若源只有红/黑标，用 PIL 取 alpha 通道把 RGB 强制 255 生成 logo_white.png，
  并 pre-register assets['brand_logo.png']/['s40_001.png']/['logo_fund.png'] 覆盖磁盘文件。

## dark 版嵌入位图去眩光：HSV recolor + 容器底色对齐
- 白底线稿/表格位图在 dark 画布上眩光刺眼；按 SKILL 的 HSV 配方 recolor 成深色（灰度反相+冷青 tint）。
- 坑1：light fill（V>0.80,S<0.45）若按配方 S=0.55 会得到饱和泥棕；降到 S≈0.38/V≈0.15 才是高级的暗金 tint。
- 坑2：recolor 后位图底色≈#0a0b0e，与 .shot 容器底色不一致会在 contain letterbox 处露出矩形缝；
  把 .shot 的 background 改成与 recolor 底色同值（#0a0c0e）即消缝。UI 截图/照片不 recolor，仅换容器底色。
- 分类先行：用 PIL 把候选位图拼 4 列 contact sheet 一次 Read 判定 线稿(recolor)/UI截图(保留)/照片(保留)。

## master 注入 </body> 命中 presenter 字符串 → 全 deck JS 死
- 现象：master 版只渲染出 mhead/mfoot chrome，所有 slide 全空白（无 .active），mchip/mband 空 → deck 主脚本没跑。
- 根因：shell.html 里有两处 `</body>`，第一处在 presenter-window 的 document JS 字符串内部。
  `final.replace('</body>', '<script>…</script></body>', 1)` 注入的 `</script>` 提前闭合了主 `<script>`，
  后续所有 JS 变成非法文本被丢弃。
- 修复：用 rfind 拼到真正的文档末尾——
  `_idx = final.rfind('</body>'); final = final[:_idx] + '<script>…</script>' + final[_idx:]`。
- 教训：单文件 shell 内含 presenter/preview 子文档字符串时，任何 `</body>`/`</html>` 的 replace(...,1)
  都可能命中字符串内的假标签；结构性注入一律 rfind 或按明确锚点（progress-track、#stage）定位。
  `grep -c '</body>' shell.html` 应＝2，确认有内嵌副本。

## 白底/master 面板泥灰 = family 前缀替换后 alpha 残留
- 现象：master 版 arch 面板在白底上是脏板岩灰（rgba(44,76,108,.55)），非预期的淡 tint。
- 根因：INLINE_FAM 只换 rgba 前缀三元组、保留原 alpha；深色 .55 面板底被前缀替换后仍是 .55，白底上发闷。
  另外 arch_lib.css（EXTRA_CSS）里是 rgba 字面量，canonical 只 remap fragment body，未 remap 组件库 → 漏改。
- 修复：①`if white: arch_css = remap_inline(arch_css)`（组件库也过 remap）；
  ②remap_inline 里加 background-only alpha 塌缩——
  `re.sub(r'background:rgba\(44,76,108,(\.\d+|\d(?:\.\d+)?)\)', λ: α≥.3→'.06' else 原样)`，border 保留 alpha；
  ③补 INLINE_HEX 库内字面量：#64e1e8→#0e8fa0、#dbf4f7→#0a7c8b、#e8d6b0/#ecd9b4→#a2761a、
  #cfe9ee→#28405a、#06202a/#04202a→#ffffff、#99adbd→#5b6d80 等。
- 连带：.slide-quote 白底看不清 = 移植 SHELL_LIGHT 表漏了 canonical 的
  `('gap:16px;color:#b7cbd4;','gap:16px;color:#41546a;')`，补回。
- 教训：换白底主题时，remap 覆盖面＝fragment body + shell + 组件库(EXTRA_CSS) + alpha 语义；
  前缀替换保 alpha 是暗色残留的主因，background 与 border 要区别处理。

## 图文并茂改版（p17/p19/p22）：截图板配方与字号坑
- 截图板配方（master 白底）：外层 `background:#fff;border:1px solid #c3d0da;border-radius:10px;
  box-shadow:0 10px 26px rgba(23,48,77,.08),0 2px 6px rgba(23,48,77,.05);overflow:hidden;
  display:flex;flex-direction:column;min-height:0`＋22px 浏览器 chrome 条（#eef1f4＋三圆点＋11px 标题）
  ＋`img.zoomable` 用 `flex:1;min-height:0;width:100%;object-fit:contain;border:none;background:#fff;cursor:zoom-in`
  （必须 border:none 覆盖 .zoomable 默认边框）；figcaption 放板外下方、12px muted 居中。
- 坑：`.mini`＝17px，在 88px chips／模型描述／KPI 标签里会折行溢出固定高面板；
  紧凑区一律字面 12.5–13px＋line-height 1.5–1.6，别复用 .mini。
- 超宽看板（aspect≥3:1，如五周期KDI 2553×840）做整行底板：plate 内 flex 行＝左文字栏 288＋
  img flex:1 contain＋右文字栏 288，图在 278 高下渲染 ≈844 宽、两侧余量被文字栏吃掉。
- 红线：绝不把从截图里读出的数字单独做成大数字 KPI panel——用户会视为幻觉（即使数字确在
  表格里，脱离行列上下文即不可验证）。侧栏只放转录的结构/标签文字（章节名、口径说明、
  fragment 原文），全页零提炼数值；数字只留在原图里，靠 zoomable 放大验证。
- caption/footnote 落到 776..801 的 body–quote 间空白带可接受（p8 的 616 body 同例），
  只要不碰 quote 顶 801；shot.mjs 对贴边元素的 overflow 报警是误报，以截图目检为准。
- 流程：PIL 1600×900 wire（master chrome＋真图 paste）→ present_files → AskUserQuestion 逐页确认
  → 才写 fragment；wire 坐标即 HTML grid 规格（rows/cols 直接抄），返工率最低。
- 竖排连接件：`writing-mode:vertical-rl;text-orientation:upright` 红底 badge＋绝对定位虚线
  `border-left:1px dashed rgba(183,0,46,.4)`＋上下 ⇅；长竖排文字会溢出面板，禁用。
- 高度紧时图注可融入 chrome 条（11px 灰字标题），省板外 caption 的 ~20px（p20 双板 262px 行即靠此塞下）。
- 两张 3:1 超宽看板并排：row 262px＋grid 1fr 1fr（板各 720 宽、图 704×232 contain）；
  上方文字区压成 44px 量化 band＋230px 四 panel（tag 11px 2/3 列 grid、panel justify-content:center），
  全页 560 刚好（p20 配方）。
- 全盘冗余审计（领导嫌"累赘"时）：扫全部 fragment json——asset 跨页复用表（{{asset:}} 正则＋
  页号列表）＋关键词/≥11字句子跨页重复表。奖状/证书图只留一个 canonical 出处（总结页 plate＋
  zoom），叙事页只留时间线文字里程碑；总览页撤奖项 chip 留规模数据。
  有意回声要保留：case 页出点＋总结页收点（220万+/约400万/+80% 的 p2·p42·p46 式呼应）不算冗余。
- builder 脚本必须幂等（先检查标记是否已改再 assert/替换）：重复执行会在 assert 前就把
  .bak 备份覆盖成改后态，丢失回滚点；改前另存整份 HTML（backup-prededup.html 式）兜底。
- 坑：`.layer` 类自带 `padding:15px;gap:14px;align-items:center;font-size:20px`——拿它当 grid band
  容器时必须 inline 覆盖 `padding:0;gap:0;align-items:stretch`，否则内容盒被压到 band 边框外
  （p42 数据带标签越界即此因）；`.panel` 同理自带 padding:24px，紧凑卡要 inline 覆盖。
- 坑：PIL＋PingFang.ttc 在多个字号下不渲染个别字形（如"稳"成空白gap，wire 页脚/治理band 都中过）；
  wireframe 统一改用 Hiragino Sans GB.ttc（index 0 常规 / 1 粗体），HTML 浏览器渲染不受影响。
- p8 架构图匀称化配方：芯片格改 `display:grid;grid-template-columns:repeat(C,1fr);gap:4px;align-content:center`，
  芯片 `padding:1px 3px;font-size:10.5px;text-align:center;white-space:nowrap;overflow:hidden`（等宽、格内居中）；
   subgroup 行容器 `repeat(n,1fr)` 拉伸使各行等高；中心盒标题 pinned 顶部＋`flex:1` 包裹层居中芯片
  （整组居中会让兄弟盒标题高低错位=用户眼中的"不对称"）；4 字行标签用 `<br>` 2+2 断行（自然折行会 3+1）；
  列数按最长文案可行性逐格选定（p8_data.py 存 verbatim 数据＋列数）。audit 对 776..801 带内元素的
  overflow 报警为已知误报（竖 band/合规条），以截图为准。
- 坑：shot.mjs 页码参数是数字（`node shot.mjs x.html tag 8`），传 "p8" 会 go('p8') 报 TypeError；
  失败的 shot 会留下持有 chrome_shot/SingletonLock 的 Chrome 进程→按 pid kill 后 rm SingletonLock 再跑。
- p20/p21 式"按原素材拓扑重绘"配方：先用 PIL 把素材图裁放大逐边读拓扑（节点/边/箭头方向/合并点），
  wireframe 1:1 复现后再换母版语言；交换箭头用 clip-path 块箭（红=正向推送、金=反馈回流），gutter 56px
  flex 列居中；重建含截图 plate 的页面时用 regex 从旧 body 抽 alt='...' 原文复用，保证 verbatim 审计过。
- p20 版式：stats band 44px → hero 300px（两侧盒装工作台 2×4 粉芯片＋中间开放列红标签+3×2 金芯片＋双 gutter 箭）
  → 底行 1fr 1fr 400px（双 zoomable plate＋AI智能体面板，末芯片 span 2 补底行）。
- p22 左右分栏重绘配方：左 960px = 三工作台列（6 列 grid 单元 span2/span3 芯片，行 repeat(4,1fr) 居中）
  ＋业务应用流（clip-path 块箭 w34/h14）＋平台服务带，gap 10px 行里放 dashed 竖tick 连三层；
  右 480px = 五周期面板（disc 椭圆夹在上下层红框之间 y344..420 防露边、torus 双椭圆、金三角 clip-path）
  ＋映射区（虚线分组框＋机构/居民灰扇线 svg＋金块箭→预判/应对）＋信号说明 3 行 grid 1fr。
- 写 builder 脚本坑：clip-path 字符串里 % 与 %-formatting 冲突 → 用字符串拼接而非 % 格式化。
- 删位图 plate 后 assemble 的 assets 数会下降（30→26），属预期；audit pages 41/slides 47 为正常口径。
- 3D 圆环（torus）SVG 配方（p22 用户嫌扁平双椭圆"别扭"后改）：底椭圆(#b7854f) + 侧壁 rect(同色, y=顶心..底心)
  + 顶面椭圆 linearGradient(#e6c79a→#c89b63) + 孔椭圆 linearGradient(#8f6a3e→#b7854f) + 孔沿 1px 亮描边；
  金三角锥底边藏进环顶 2px 即得原弹窗的陀螺感。
- 带状容器内末盒宽度要留右 margin：p22 平台服务带 pw=214/pitch=224（原 216/229 末盒贴到面板边框=红线违规）。
- 用户不喜页面自带"原始架构与…原生重绘"类注释标签 → stats band 右端 tag 删除。
- p22e 左栏"严格按用户原图"重绘配方：先 2x 裁放大逐格抄录（组带=灰底 round6 内含 68px 标签列+3列芯片 grid；
  粉色组带=粉底+粉描边如"投研互动-外部"；内嵌盒=粉描边白底+标题行如"交易管理"；灰芯片红字、IBOR 灰底黑字）；
  列内组间用 space-between 撑满列高（原图每列填到底）；左 gutter 36px 红带（业务应用/中台服务/数据服务）。
  坑：芯片宽公式别把标签列宽扣两次（(w-68-6-2*gap)/3），否则第三列溢出面板。
- 用户说"用附件原图重绘"时，附件可能与 source_assets 旧图(s17_011)不同源——以最新附件为准逐格抄录，勿复用旧拓扑。

## 位图内嵌齿轮/机件做旋转动效（p35）
- 齿轮烘在 jpg 里时不能改图，只能叠矢量覆盖层：先色掩码(白齿 lum 高 / 金色 r>200,g120-200,b<110)在±24px 窗内量每轮 bbox 中心与外径，再 6x 裁剪目检复核。
- 显示几何：object-fit:contain 且舞台固定 → scale=min(CW/IW,CH/IH)、ox=(CW-IW*S)/2；覆盖层 svg 用 px 绝对定位在 position:relative _wrapper 内（舞台固定尺寸所以 px 安全），wrapper 加 pointer-events:none 保住 img.zoomable 点击放大。
- 覆盖规则：旋转齿轮背后垫不透明 backing disc，半径=原轮外径+1.5src px；齿顶半径=disc 半径（disc 永不露晕圈）、齿谷=disc-4.2、内环=齿谷-1.2；任何旋转相位都盖死原静态轮。
- 旋转加在 <svg> 根元素上（CSS transform-origin 默认 50% 50% 生效）；不要加在内层 <g>（SVG 内 transform-origin 默认 0 0 会绕角转）。啮合邻轮用 animation-direction:reverse + 同 duration 保证线速度一致。
- QA：shot.mjs 的 presentation.setMotion(false) 会冻结 CSS 动画 → 静态位 QA 用 shot.mjs；验证真转用 live35.mjs 式 CDP 脚本（不 setMotion，隔 1.25s 双帧截图 + 读 getComputedStyle(svg).transform 矩阵变化），双帧叠图目检齿相位变了而轮心不动。
- fragment 替换坑：p35 两张 zoomable 图共用同一段结尾 style 字符串，replace 会命中 2 处 → 先 index('{{asset:xxx.jpg}}') 再 index(结尾串, anchor) 定点 splice。
- p35 二轮（用户嫌方向乱+要履带联动）：全部齿轮统一反向(reverse=CCW)与履带上表面同逻辑啮合（履带向右=工艺流向左→右）；履带动效=从 jpg 切一个周期(自相关量得 14src px)的板条带 tile(y376..392, 干净段 x460)做 repeat-x data-URI 背景，background-position-x 0→P 循环；时长= P_display / 齿轮 rim 速度(2π·tip/DUR) 保证齿与板条啮合不滑移；点状灯带周期≠14 保持烘焙静态。验证：双帧间隔取 0.3s（≈半周期）再对履带带区做 lag 互相关，峰值 lag≈-P/2 即向右移动；间隔 1.25s 会因整周期别名看不出位移。
- p35 三轮（配色不搭→浅色1:1原生重绘）：用户"一比一重绘+浅色板"指令优先于我的再诠释深色稿；1:1=逐件保留原bitmap拓扑（双箭汇聚萃取、八角机身+机间连轴、机械臂/活塞、橙尾轮、梯形底座、双向闭环弧箭+绶带、虚线内框、图片物料橙框高亮）。
- 浅色板 token：红=管控chevron/闭环弧箭/绶带/产品箱；钢#44546a齿轮+橙#e87917尾轮；金chip=底座/渠道/未来能力；板岩chip=素材/物料；dashed内框# c6ccd2。
- 三重联动公式：v=2π·r_tip/DUR；履带=repeating-linear-gradient(115deg) 水平周期=stop周期/sin115°，background-position-x 0→P、T=P/v；产品箱 translateX run、T=run/v、负delay+base offset 错开（否则 print/animation:none 时四箱叠起点）+两端opacity淡入淡出藏wrap跳变。
- clip-path 形状没有 border → 嵌套 inset:1px 同 clip-path 双层假描边（chevron/八角/梯形同法）。
- 动效验证别只靠双帧互相关：间隔≈周期会别名（lag0 假阴性）；用 probe35.mjs 直接读两时点 getComputedStyle 的 backgroundPositionX / transform 矩阵才确定。
- %-格式化串里字面 width:100% 须写 100%%（又一次踩）。
- 下线 jpg 后 embedded_assets 26→25 属预期；zoom 弹窗随 img 一并移除，右栏 icp_home_v2 仍 zoomable。

## p35b 冰蓝玻璃质重绘（2026-10-09，附件1:1）
- splice 坑：fragment body 的 MARK 在 index 0、外层 `height:560px;grid-template-columns:880px 1fr` wrapper 开标签在其后；从 MARK 切到右列锚点会吞掉 wrapper 开标签→左板撑满全宽+右列坠底（shot overflow 列出右列全部芯片即此症状）。改前必先 dump bak body 的 `</style>`→panel 区间，把 wrapper 开标签并入新 PANEL。
- 带 border 的面板在固定 880px 列内必须 box-sizing:border-box，否则 882px 推挤右列 2px→右列整体报 overflow。
- %-format 坑再现：含 CSS 渐变百分号的 PANEL 串禁止 % 格式化（TypeError: not enough arguments），用 + 拼接；未格式化的 inner 串写单个 %。absdiv 返回 None 不能链 .replace()，加 cls 形参。
- 动效探针随设计更新：p35cart 已不存在→probe35.mjs 改读 svg.p35g transform + p35dots backgroundPositionX；probe 崩后 chrome 留持 SingletonLock 挡下次启动→pkill -f "chrome_sho[t]"（方括号防自匹配）。
- 冰蓝玻璃质配方：底 linear-gradient(#eef4ff,#e7effe)；强边 #96b4e8/软边 #c9d8f5；蓝渐变 tab/箭 #4d8dff→#1e50e0；紫 #9a7bff→#7a5cff；胶囊机=2px #96b4e8 + r16 + 白→#e6efff 渐变 + inset 高光 + 内衬 r12；金属履带三段渐变(#e8edf3/#cdd5dd→#98a3ae/#8d98a4→#7b8692)+slats repeating-gradient 12px+蓝点 radial 14px；轮=svg 圈+辐条 p35spin，v=20px/s→端轮 r10 D3.1416s/支轮 r7 D2.199s/slates .6s/dots .7s 同向联动。
- 线稿坐标即实施坐标（wire35b.py 与 write_p35b.py 共用同一套 880×512 常量），先稿后实施一轮过。

## p35d 附件位图直嵌 + 履带/齿轮右向转动 overlay（2026-10-09）
- 用户终版指令：停止原生重绘，p35 左板直接用附件位图（1672×941 冰蓝 3D 流水线），并让履带与齿轮统一向右转。做法=位图 contain 直嵌 + 不透明动效 overlay 覆盖静态履带/轮。
- 位图→plate 映射：panel 内框 878×558；S=878/1672=0.52512；渲染高 941*S=494.14；OY=(558-494.14)/2=31.93；plate_x=img_x*S、plate_y=OY+img_y*S。overlay 全部按此换算，勿手填。
- 轮心测量法：灰度模板匹配（左轮面 54×54 作模板，固定 y=578 滑 x，取间距>50 的 6 个极小）得 (325/511/683/935/1117/1288, 605)、R_IMG=27；暗hub/蓝hub 聚类法会被履带蓝光污染，不可靠。
- 履带暗带（LED 点行）实际范围 img x300..1302、y586..608；初版误用 182..1500 导致暗条伸出履带两端悬在浅色背景上（截图目检发现）。带范围必须用 full-row crop 目检核定，不能只信行扫描。
- 动效物理统一 V=20 plate px/s：轮 dur=2πr_pl/V=4.4542s（CW=rightward）；点行 dur=period_pl/V，period_pl=60*S=31.507→1.5754s；keyframes p35spin/p35dots，.p35banim print 冻结。轮 overlay 用不透明 svg 圆盘(金属环+灰环+白环+蓝hub+4辐条)整颗替换位图轮面，辐条显旋转。
- 资产：附件 cp 到 source_assets/icp_line.png 并在 assemble.py 预注册 base64 无损 PNG（仿 closing_red.png），绕开 encode() webp。
- 验证链：probe35 查 svg.p35g 数与 transform + p35dots bgX；live35 双帧 PIL diff bbox 非空 + 目检点行右移/轮辐转角；shot overflow []。probe 里 p35beltL 查询已无对应元素返回 NOBELT 属正常。

## 深色炫酷版转换：light-native 页 DARK_INLINE 反染 + 位图 neon 重着色（2026-10-09）
- 背景：打磨期各页是在 master/白底语言里重写的（8,17,19,20,21,22,35,42），fragment 因此变成"38 页 dark-native + 9 页 light-native"混血；无参 assemble（深色）会把 light-native 页渲染成白底红卡浮在 neon shell 上。解法=深色构建里仅对 DARK_REMAP_PAGES 施加 remap_inline_dark()（light→neon），dark-native 页不动。
- 检测/清单：先按页 census light vs dark 标记 token 定清单（L>=5 且 L>D 判 light）；p35 左板是 light 但右列 dark，census 判不出（L=1<D=9），须显式并入清单。清单硬编码+注释，后续新打磨页要记得加。
- 反染表要点：①实心红 chip（background:#b7002e 配白字，白字常被 border-radius 隔开不在相邻位置）必须用 style-attr 级 regex 同时把 color:#ffffff→#06111b，仅换底色会白字压青底；②#ffffff 只能带 background: 前缀换（color:#ffffff 是暗底白字要保留）；③#262626 既作 ink 又作 chip 底，background:#262626 前缀先换 #1b3a4a 再让裸 #262626→#edf4f5；④金/粉/灰系整族映射到 neon 金(cyan 邻)与 cyan tint；⑤hex 按长度降序替换防前缀误伤。
- 位图 neon 重着色（recolor_icp.py）：HSV 分治——S<0.14 的白底/灰阴影→深navy 且 V 反转保留 3D 体积；饱和蓝线稿→hue 拉向 0.5 的亮 cyan 发光；V<0.45 的深蓝墨线→全亮 neon。产出 icp_line_dark.png，assemble 里 dark 用暗版、white/master 用原冰蓝版。UI 截图仍不 recolor。
- p8 溢出是 fragment 级内容高度 bug（外 wrapper height:616+margin-top:-30=净586>560 body），所有主题都越界；改 590/rows 396+182 后内层 fr grid 吸收，dark+master 均 overflow []。修 fragment 会同时改三主题，须三版同 rebuild+同交付。
- 验证：无参 assemble→audit→shot 全 47 页→PIL 拼 2×4 contact sheet 逐板目检一致性（白页/杂色页一眼可见）；chapter/cover/closing 的 overflow 报空串文本属装饰性设计元素，非回归。

## shell count() 序数跳变修复（2026-10-09）
- .big-stat 进入页面会跑 850ms count-up；p27 的 01–04 是阶段序数不是指标，count-up 会 0→4 跳变且中途丢前导零（"01"闪成"1"），观感"数字加载奇怪"。修复=shell count() 里 /^0\d/ 前导零直接 el.textContent=text 返回（序数静态直出）；真指标（80%/2亿+）不受影响仍平滑计数。验证=probe27.mjs 在 go() 后 0/60/150/300/600/1000ms 采样 textContent 全为 01–04；p29 采样 20%→49%→77%→80% 确认指标仍动画。改 shell 须三主题同 rebuild。
- probe 崩后 chrome_shot/SingletonLock 残留挡下次启动→pkill -f "chrome_sho[t]" 再跑。

## Faithful tree/map redraw (弘研智享 p1, 2026-10)
- When the owner says "用原稿的结构重绘", replicate the connector grammar too: one CSS grid with dedicated connector columns (3px trunk cols + 20px stub cols) between content columns; rows = tree rows + legend row.
- Vertical trunk lines: `.vl` cell with `::before{left:50%;width:2px}` and top/bottom % variants — `v-down`(50%→100%) for a trunk starting at a spanned box center, `v-up`(0→50%) for the tail cell, `v-mid`(12.5%→87.5%) for a trunk spanning 4 equal rows edge-to-edge of first/last row centers.
- Horizontal stubs: draw them as `::before/::after` on the box WRAPPER (`right:100%`/`left:100%;width:<stubcol>`) so they always sit at the box's vertical center; never as separate grid items (row-center ≠ box-center once spans differ).
- Fixed-height grid children (`.mbox`, nested dash grids) stick to row START by default → misalign with flex-centered siblings; add `align-self:center`.
- Class-name collisions with arch_lib.css bite: `.tag` there draws a bordered chip → tagline got an unwanted box; rename project classes (`.tg`) and scope link underline to a dedicated class (`.u`), not `b`.
- Corner badges (NEW/flame) as one absolute `.corner` span (top:-11px;right:-8px;flex) reproduces the source's overlapping corner tags; flame = inline SVG path fill #ff5a3c + drop-shadow glow (no emoji).
- GRID GAP TRAP (p1 v3): `gap:10px` on the map grid also inserts 10px between COLUMNS, so 20px pseudo-element stubs floated 10px short of trunks/boxes ("线条没连接住"). Fix: `row-gap:10px;column-gap:0` and let dedicated spacer columns (14/20px) provide all horizontal breathing room.
- New-content insertion on a full stage: stack it as a right rail (intro panel + shortened arrow zone) in the last grid column instead of squeezing tree rows; widen that column and recompute 1fr (node boxes tolerate ~160px).
- Connector junctions must be verified at 2× zoom (PIL crop of the shot), not at full-page scale: hairline breaks hide at 1×. Three break classes found on p1: (a) row-gap splits multi-cell vertical trunks → use ONE cell spanning all rows with % top/bottom computed from row math (rows1-4 center in rows1-5 block = 39.8%/9.18%); (b) stub percent tops must be exact row centers (11.53% not 12.5%) or T-junctions misalign ~4px; (c) stubs must OVERLAP the trunk column (left:-24px;width:24px across a 20px stub col + 3px trunk col) and horizontal runs crossing an empty trunk column need the neighbouring stubs extended, else a 3px hole remains.
- Owner veto on "floating panel" intros: new side text belongs in ONE continuous full-height sidebar (intro → divider → axis → divider → QR), type ≥13px, gold two-tone heading; keep a dedicated gutter column (26px) between tree and sidebar so node boxes never kiss the sidebar border.

## p35 深色版架构图：位图换色不够，必须原生重绘（2026-10-09）
- 用户反馈深色版 p35 内容平台架构图"不清晰"：HSV 换色位图(icp_line_dark.png)在 878px 板宽下 3D 履带糊成青色块、小字发毛。结论：换色位图只适合线稿，含 3D 渐变/阴影的渲染图一律原生 HTML/CSS 重绘。
- 做法：write_p35e.py 以原图 1672×941 坐标×S(=878/1672)绝对定位复刻全部节点；fragment 内用 `<!-- p35bmp -->…<!-- /p35bmp -->` 与 `<!-- p35nat -->…<!-- /p35nat -->` 双标记块共存；assemble.py 按主题剥离（white 剥 nat、dark 剥 bmp），且 dark 的 remap_inline_dark 用 \x00 占位符保护 nat 块不被二次换色。
- 复刻要点：所有文字 white-space:nowrap（板宽小，flex 居中盒极易折行）；clip-path 八角chip用"外层border色+内层inset:1px同clip"双层法才有真描边；标题压容器边框时用与容器内底同色的渐变mask断线；齿轮复用 p35spin/p35dots/p35banim 与 .p35g 类（live35.mjs 依赖 svg.p35g）。
- 校验链：write_p35e.py preview → qa/p35n_preview.html 单独 chrome 截图迭代（比整deck rebuild 快一个量级）→ PIL 原图resize(878,494)与预览crop(361,203,1239,697)上下拼对比图目检 → apply 后三主题 rebuild+audit+shot+live35。

## Connector stub geometry & suppression (p1-style grid trees)
- Horizontal stubs that bridge a 20px gap + 3px trunk column must be width 21.5px (gap + half trunk), NOT gap+4: a 24px stub crosses the 3px trunk and leaves a 1px tick protruding on the far side — visible at 2x zoom as the classic "line sticks out past the junction" defect. Stubs ending at trunk center overlap the 2px trunk line by 1px (joined) and can never overshoot.
- Stubs into a box border: width = gap + 1px so the tip hides inside the 1px border; works for both opaque and near-transparent (dashed) boxes.
- Last-in-row suppression class (.end) must match the connector rule's specificity: `.map1 .mbox.end::after{content:none}` placed AFTER `.map1 .mbox.node::after` / `.map1 .dashgrid .mbox::after` (3-class selectors); a 2-class `.end::after` silently loses and trailing stubs remain.
- When adding wrap-level ::before/::after stubs, also audit node-to-node gaps (14px) and inner-grid gaps (10px): they may have had NO connectors at all while 1x screenshots looked fine. Always zoom each junction class (trunk T, trunk corner, chain links, dashed runs, row-end) at >=2x before delivery.
- Add transform:translateY(-50%) to every top:50% stub so it is truly centered (missing it puts the line 1px low against centered verticals).

## Master-theme port to the 弘研智享 5p lean assembler (2026-10-11)
- shell.html's go() already fills #m-chip/#m-title/#m-num when present — no JS patch needed; just ship per-page `chip` ('01'..'04', zero-padded) and `ctitle` (chapter title, e.g. 能力全景/五周期框架/观点与路演/接入指引; video page reuses previous chapter) in deck-data. Adding them is dark-safe (hooks no-op without mhead).
- Swap table for this deck's palette on top of the white canvas: cyan family rgba(100,225,232,→rgba(183,0,46, and #64e1e8→#b7002e; gold family rgba(216,183,125,→rgba(155,0,39, and #d8b77d/#e8cd96/#c9a35f→#9b0027/#b7002e/#9b0027; red chips #d3002f/#a3002a→#b7002e/#9b0027; bronze pedestal→greys; gold arrows→red; neutral lines rgba(149,186,201,→rgba(105,110,118,; panel borders rgba(154,181,204,→rgba(0,0,0,; dark panel fills rgba(12,34,53,α) collapsed globally to rgba(0,0,0,.045) via regex (gradients flatten acceptably).
- Keep semantic signal colors (看多 pink / 中性 blue / 看空 green) but darken their TEXT hexes for white bg (#f2a9b4→#c22843 etc.); light tints survive as-is.
- Kill dark-only glows on white: body.theme-master .map1 .wm span{text-shadow:none}; hide #ambient + #stage:after grid.
- Injection order that worked: regex collapse → hex/rgba swaps → MASTER_CSS before first </style> → body class → mhead after <div id="stage"> → mfoot before .progress-track. First </style> is the main block (presenter-window styles live later in JS strings).
- Verify: dark rebuild must diff ONLY in deck-data (chip/ctitle); audit both outputs; contact-sheet all master pages (chrome band = chapter title, mnum present, videoslot/quotes readable on white).
- PITFALL (footer drift, user-spotted): never add a catch-all re-show rule like `body.theme-master .mhead,body.theme-master .mfoot,body.theme-master .mnum{display:block}`. Chrome nodes are injected only in master mode so nothing needs re-showing, and `display:block` on `.mfoot` out-specifies `.mfoot{display:flex}` (0,2,1 vs 0,1,0): the `.msq` span loses flex blockification (23×23 red square vanishes) and `.men{margin-left:auto}` stops right-aligning, gluing the EN company name onto the slogan. Fix = delete the rule; QA = PIL-crop bottom 52px of every page at 2× and compare with the reference footer (square left:37, slogan, EN right:37).

## 大视频内嵌单文件 + 点击全屏播放（弘研智享 p4, 2026-10-11）
- 107MB mp4 走 base64 data-URI 内嵌（单文件原则优先于体积）：assets['x.mp4']='data:video/mp4;base64,…' 原样注册（不过 encode_webp），body 里 `<video data-asset="x.mp4" preload="metadata" controls playsinline>`——shell 初始化对全部 [data-asset] 统一赋 src，video 同样适用；最终 HTML ≈ 视频×1.35（144.5MB），Chrome 解析+解码 readyState=4 约 10–12s，可接受。
- 点击全屏：.vstage 单击 → element.requestFullscreen(video)＋play()；三个必守细节：①已在 fullscreen 时 early-return（全屏内原生控制条的点击会冒泡回 .vstage）；②inline 时点原生控制条区域（e.target===video 且 e.offsetY>clientHeight-54）不触发全屏，否则点 inline 播放键会误入全屏；③window capture 阶段 keydown 屏蔽 deck 导航键（space/arrows/f/m/o/s/p/h）当 fullscreenElement 存在时，Esc 放行（浏览器原生退出）。play/pause 事件同步 .playing 类隐藏中央播放徽章与提示 pill。
- VIDEO_JS 注入必须用 final.rfind('</body>')：shell 的 presenter-window JS 模板串里先出现 `</body>`，replace(...,1) 会把 script 插进模板串毁掉 shell。
- audit 适配 144MB 文件：lxml 默认丢超大 text node → `html.fromstring(s, parser=html.HTMLParser(huge_tree=True))`；PIL verify 循环跳过非 data:image 资产（mp4 不是图）。
- 全屏验证探针（probe4.mjs）：CDP Input.dispatchMouseEvent 在 .vstage 中心做可信点击 → 断言 document.fullscreenElement.tagName==='VIDEO' && !paused && deck page 不变；headless 里 dispatchKeyEvent 的 Escape 不退全屏（浏览器进程级拦截不存在），退出路径改用 document.exitFullscreen() 验证；fullscreen 态 Page.captureScreenshot 可拍到铺满帧。
- 崩溃残留：probe 崩后 chrome_shot/SingletonLock 挡下次启动 → pkill -f "chrome_sho[t]" + rm SingletonLock（再现一次）。
- 主题双写：播放器深色默认样式放 EXTRA_CSS（cyan 描边/徽章），MASTER_SWAP 自动把 cyan 族换红；MASTER_CSS 只补 .vplayer 白卡底/灰发丝边与 .vbar 文字色（视频黑面上的徽章/提示 pill 两主题共用深色样式，不动）。
- 轻量版（novideo flag）：跳过 mp4 注册（144MB→1.4MB）；body 手术＝删 <video> 标签、.vstage 加 .vposter（深色 radial 海报底＋::before 光晕＋.vdur 时长 pill 右上＋.vhint 落底 18px 因无原生控制条）、提示/说明文字改"轻量版 · 视频未内嵌 / 播放请用含视频版"；VIDEO_JS 无 video 分支点击调 shell 全局 tell() 弹 toast；文件名后缀 -无视频（与 -母版版 可叠加）。审计 MUST 的"视频"字靠 vbar 标题保住。
