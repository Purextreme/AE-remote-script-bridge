# AE Agent/MCP 开源方案评估（2026-07-16）

## 决策

选择路线 **3：保留现有 `AfterFX.com` Bridge，选择性吸收 operations**。

不直接采用或 Fork 任一候选。理由不是“必须自研”，而是三套候选的核心
价值已经被拆成两类：

- 高频 typed operation、严格参数、结构化 inspect、截图和错误返回值得复用；
- MCP server、常驻 panel、内嵌聊天、provider 管理和跨平台产品层会显著增加
  当前 Windows skill 的依赖、部署面和故障点，且不会替代现有备份、Run ID、
  独立日志、`AfterFX.com` escape hatch 与无 Render Queue 预览能力。

因此本次只移植最小 operation contract，不引入 MCP SDK、CEP、Express、React、
Node server、`uv` runtime 或后台端口。MCP 若以后需要，只应作为 JSON contract
的可选 adapter。

## 候选评估

### Dakkshin/after-effects-mcp

- 仓库：[Dakkshin/after-effects-mcp](https://github.com/Dakkshin/after-effects-mcp)，
  评估 commit `88d5fbf`，MIT。
- 能力：composition、text/shape/solid、layer properties、keyframe、expression、
  effect/template；主分支实际注册约 10 个 MCP tools，部分 panel handler 没有
  一一暴露成 typed tool。
- 架构：Node MCP stdio server + ScriptUI panel + `Documents/ae-mcp-bridge` 两个
  JSON 文件轮询。需要常驻 server 和保持 panel 打开。
- inspect/验证：有 project/layer info 与 result file；没有成熟的视觉 preview、
  checkpoint、run 隔离或工程备份。旧实现以 command name/mtime 判断新结果，
  并存在英文 display name 与 OneDrive 路径风险。
- 质量：`npm ci`/build 在 Node 22 上通过；没有自动测试套件；`npm audit` 报
  7 个漏洞（1 low、4 moderate、2 high）。历史 issue 曾记录 merge marker 导致
  安装失败，当前分支已经修复。
- 结论：作为能力原型有价值，但不宜直接采用或 Fork。

### a-y-ibrahim/after-effects-mcp

- 仓库：[a-y-ibrahim/after-effects-mcp](https://github.com/a-y-ibrahim/after-effects-mcp)，
  评估 commit `8d78eab`、v1.7.4，MIT；源自 Dakkshin/TheLlamainator。
- 能力：约 40 个 tools，覆盖 typed layer/effect/preset/audio/marker、
  `inspect-comp`/`inspect-layer`、arbitrary `execute-script`、`see-frame`、
  contact sheet、Render Queue 和 `aerender`。
- 架构：Node 18+ MCP server + 常驻 ScriptUI panel，Windows 使用
  `%LOCALAPPDATA%` 文件桥，750 ms 轮询；command ID、原子写、mutex、bridge
  version handshake 和错误 `isError` 明显优于原项目。
- inspect/验证：三者中轻量路径最完整；支持深层 transform/effect/mask/keyframe
  inspect 与真实帧预览。但没有现有 Bridge 的 `.aep` 保护/operation backup 和
  per-run artifact 隔离。
- 质量：build、typecheck、lint、format 全通过；81 tests 全通过；`npm audit`
  报 4 个漏洞（2 moderate、2 high）。`src/index.ts` 与 panel JSX 仍是 3000+ 行
  单体文件，后续裁剪成本高。
- 结论：最适合吸收 handler 思路；不值得为了 MCP transport 替换现有 Bridge。

### JUNKDOGE-JOE/after-effects-mcp（仓库名修正）

- 用户给出的 `JUNKDOGE-JOE/ae-mcp` URL 不存在；实际仓库是
  [JUNKDOGE-JOE/after-effects-mcp](https://github.com/JUNKDOGE-JOE/after-effects-mcp)。
  评估 commit `5261cea`、v0.9.2 candidate，MIT。
- 能力：代码注册 52 个 schemas（文档部分位置仍写 49），包括 typed property
  discovery/read/write、expression validation、preview/snapshot、checkpoint/revert、
  search、rig、approval gate、diagnostics、tool library，以及 arbitrary JSX。
- 架构：Python MCP → `httpx` → localhost HTTP → Express/CEP host →
  `CSInterface.evalScript` → ExtendScript；另有 React panel、sidecar、截图 backend
  和正在开发的 AEGP native host。
- inspect/验证：能力最强，schema、分页/遍历预算、错误提示、审批和 checkpoint
  都成熟；preview 使用 `saveFrameToPng`，snapshot 使用 `mss`。
- 依赖/规模：核心要求 Python 3.10+、`mcp`、Pydantic、jsonschema、Pillow；bridge
  需要 `httpx`；CEP host 需要 Express，panel 需要 React。当前 checkout 约 374 个
  Python/JS/JSX/TS 文件、127,941 行。普通用户 release 目标为签名 ZXP/DMG 和
  bundled runtime，但 v0.9.2 文档明确仍是未发布 candidate，RuntimeManager/
  release guard 尚未完成。
- 质量：在隔离 venv 中收集 813 tests；780 passed、8 skipped、25 live tests
  deselected，仅有 1 个 `mss` deprecation warning。维护活跃，最新 commit 为
  2026-07-15。
- 结论：它适合需要完整 panel 产品、审批和多 agent backend 的独立部署；对本
  skill 的“轻量、可靠”目标过重，不 Fork。

## 实际吸收

来源和完整 MIT notice 见
`assets/bridge/operations/THIRD_PARTY_NOTICES.md`。本次吸收：

- JUNKDOGE 的 typed JSON→JSX、`matchName` property path、structured inspect/
  keyframe result 模式；
- a-y-ibrahim 的 transform `matchName`、TextDocument、bounded inspect 与精确错误
  返回模式；
- 现有 Bridge 保持 transport、安全、backup、operation ID、run logging、timeout、
  preview 和 raw JSX escape hatch 的所有权。

新增 operation：

- `create_text`
- `set_text`
- `set_transform`
- `set_keyframes`
- `inspect_comp`
- `inspect_layer`
- 顶层 `operations` batch（最多 50 项、一次往返、一个 Undo Group）

目标可以用 comp/layer ID、layer index 或唯一 exact name。名称不唯一时明确失败，
不再静默取第一个。Python 标准库先拒绝错误字段、类型和范围；AE 返回结构化
`result.json.payload`。没有新增 runtime dependency。

## 放弃或暂缓

- MCP/CEP/内嵌聊天/Provider Manager：不是当前 Bridge 的核心问题，依赖与故障
  面远大于收益。
- effects/presets/audio/markers/rig/tool library：有价值但低于本轮文字、Transform、
  keyframe 和 inspect 的频率；一次性移植会扩大测试面。
- 第三方 render/aerender：现有 preview 与 Render Queue isolation 更符合当前
  agent 验证场景；正式渲染仍保留 raw JSX/task card。
- 第三方 checkpoint/revert：JUNKDOGE 的实现成熟，但现有 Bridge 已有保存检查、
  `.aep` backup 和 operation ID；暂不叠加第二套状态系统。
- AEGP native host：能力强但平台/SDK/签名成本高，与轻量目标不匹配。

## 实机测试结果（AE 2024 / Windows）

| 场景 | 结果 |
|---|---|
| Python tests | 22 passed |
| 6 个 operation 正常路径 | 全部成功；inspect 读回实际 AE 值 |
| 5-operation batch | target stage 1547 ms；一个往返完成 create/set/transform/keyframe/inspect |
| 等价手写 JSX | target stage 同为 1547 ms；transport 没有神奇加速 |
| 调用体积 | typed JSON 1013 bytes；手写 JSX 1052 bytes；typed request 额外包含 inspect |
| 参数错误 | 拼写错误在 397 ms 内被 Python 拒绝，AE 未启动 |
| 目标不存在 | 明确返回 comp/layer、JSX line、`completedCount: 0` |
| 同名 layer | 2 个 exact matches 时失败；提示改用 ID/index |
| 部分 batch 失败 | 前 2 项完成后第 3 项歧义失败，返回 `completedCount: 2` |
| 原始 JSX 错误 | `ReferenceError` 和 line 1 正确返回 |
| timeout | 250 ms 超时给出“state unknown”；随后只读 inspect 恢复成功 |
| 视觉验证 | `saveFrameToPng8Bpc` 成功；截图 stage 1594 ms |
| Render Queue 污染 | 截图前后均为同一个既有 item，数量/状态/输出路径不变 |
| protection | 首次 mutation 创建 `.aep` backup；同 operation ID 的下一次调用复用 |
| 旧 create/modify/error | create、modify 成功；error 按预期失败并带行号 |
| 旧 integration | 稳定工程路径下 9/9 checks 成功，stage 10125 ms，生成 MP4 和 `.aep` |

结论：typed operations 与单个精心编写的 batch JSX 执行时间相同；真正收益是避免
每次重写定位/校验/错误/inspect 代码，并把多次独立 Bridge 往返合并。按当前约
1.5 秒/次的 target stage，5 次独立调用约需 7.5 秒，而本次 batch 为 1.55 秒。

## 当前模块边界

```text
assets/bridge/
├─ client/
│  ├─ send_to_ae.py          # transport/protection/run/capture
│  ├─ operation_request.py    # stdlib schema validation + launcher
│  ├─ run_operation.py        # thin CLI adapter
│  └─ test_*.py
├─ operations/
│  ├─ ae_operations.jsx       # AE handlers only
│  ├─ README.md               # contract/examples/failure semantics
│  └─ THIRD_PARTY_NOTICES.md  # upstream lineage + MIT notices
├─ examples/operations/       # stable JSON examples
└─ scripts/                   # raw JSX escape hatch and integration checks
```

## 后续值得封装

按价值排序：

1. 通用 `set_property`/`inspect_property`（先解决 separated dimensions 与稳定
   match path）；
2. expression set + machine validation；
3. effect add/remove/property set（按 `matchName`，避免本地化 display name）；
4. layer create/duplicate/delete/move/precompose；
5. marker 批量写入；
6. footage import/replace。

## 已知风险与限制

- batch 是 fail-fast 的单 Undo Group，但不会自动 rollback；失败 payload 会报告已
  完成项，必要时用户/agent 可执行一次 Undo。
- layer index 会随排序变化；优先使用 AE layer ID。较老 AE 版本可能没有 layer ID。
- 当前 keyframe 只覆盖 Transform 五项与 AE 默认插值；separated dimensions、
  spatial tangent、ease graph 仍用 raw JSX。
- 第三方项目只运行了其非 live tests；没有安装它们的 panel 来做本机 AE roundtrip，
  因为最终路线不采用其 transport，安装会引入额外状态并要求重启 AE。
- `ae_test_integration_ops.jsx` 会把当前工程保存到 run 的 `temp`。run 目录以后会被
  轮转删除；如果长期保持该测试工程打开，AE Auto-Save 可能弹出“无法创建文件夹”
  模态框并阻塞脚本。本次实际遇到一次。测试后应立刻另存到稳定路径或关闭工程；
  不要把该脚本用于工作工程。
- 默认 8-bpc frame capture 不碰 Render Queue，但临时切换位深仍可能把工程标记
  dirty；HDR/linear/32-bit 色彩应使用现有 Render Queue capture 做最终核对。
