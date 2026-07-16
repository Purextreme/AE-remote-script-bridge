# AE Bridge 轻量生产级测试方案

状态：已实施并在 AE 2024 / Windows 完成生产验收（2026-07-16）。

## 1. 目标与结论

本方案用于团队分享前的发布验收。它不追求覆盖全部 AE API，而是验证一条常见的
小型生产链路：

> 建合成 → 放入图层/素材 → 修改文字与动画 → 添加效果 → 检查结果 → 预览 →
> 素材丢失后重链 → 输出 → 清理。

推荐保持两层边界：

- **稳定 operation API**：只放 Agent 高频调用、参数边界清楚、能够长期兼容的能力。
- **测试 harness**：负责构造 fixture、制造丢失素材、记录基线、清理和断言；这些
  辅助动作不自动成为公开 operation。

核心仍使用现有 `AfterFX.com` Bridge、工程保护、operation ID、日志、超时、预览和
raw JSX escape hatch，不引入 MCP server、CEP panel 或新 runtime。

## 2. 建议扩展的最小能力集

现有 `create_text`、`set_text`、`set_transform`、`set_keyframes`、`inspect_comp`、
`inspect_layer` 和 batch 保持不变。下一轮只增加以下高频能力。

| 领域 | 建议 operation | 最小职责 | 优先级 |
|---|---|---|---|
| Composition | `create_comp` | 创建指定尺寸、时长、帧率、像素宽高比和背景色的合成 | P0 |
| Composition | `set_comp` | 仅修改传入的 `name`、`width`、`height`、`duration`、`frameRate`、`pixelAspect`、`bgColor` | P0 |
| Layer | `create_solid` | 创建可测试效果和动画的纯色层 | P0 |
| Layer | `add_source_layer` | 通过唯一 project item ID 把素材放入目标合成 | P0 |
| Footage | `import_footage` | 导入一个已存在的文件，返回 project item ID 和媒体信息 | P0 |
| Footage | `inspect_footage` | 返回路径、类型、尺寸、时长和 `footageMissing` | P0 |
| Footage | `relink_footage` | 用新文件重链现有 FootageItem，并保持 project item 身份 | P0，需实机探测 |
| Effect | `add_effect` | 按 effect `matchName` 添加内置效果 | P0 |
| Effect | `set_effect_property` | 通过 effect selector 和 property match path 设置一个参数 | P0 |
| Effect | `remove_effect` | 通过 index 或唯一名称删除指定效果 | P1 |
| Output | `render_comp` | 隔离 Render Queue 后渲染指定合成并恢复原队列状态 | P1 |

`set_comp.bgColor` 只表示合成背景色，范围为 0..1 RGB；本轮不修改项目色彩管理、
working space、线性工作流或 OCIO 设置。后者影响面大，不适合并入轻量通用接口。

效果测试只使用 AE 内置且已有稳定 matchName 的：

- Fill：`ADBE Fill`
- Tint：`ADBE Tint`

参数 property matchName 不能猜测，实施前应在当前 AE 版本做一次探测并记录。第三方
插件、Preset、本地化 display name 和复杂效果链暂不纳入核心套件。

## 3. 测试分层

### S0：Preflight（只读，约 30 秒）

每次运行都执行：

1. 检查 AE 版本、工程路径、工程是否已保存、当前 Bridge 可通信。
2. 记录项目 item 数、Render Queue item 数及每项 render 状态、当前活动合成、位深。
3. 探测 Fill/Tint 是否可添加，以及可用 Render Settings/Output Module templates。
4. 检查测试输出目录可写；测试文件全部限制在当前 run 的 temp 目录。

Preflight 不满足时应返回 `SKIP` 或 `BLOCKED` 及明确原因，不能把环境缺失报成业务
operation 失败，也不能修改工程。

### S1：Core Smoke（每次改动，目标 3 分钟内）

覆盖稳定 operation 的一条完整正向链路，不执行正式视频渲染：

1. 创建 320×180、24 fps、2 秒的 namespaced 合成，设置背景色后改名。
2. 创建文字、替换文字、修改 position/scale/opacity，并设置两个 position keyframes。
3. 创建 Solid，添加 Fill，设置并 inspect 颜色参数。
4. 导入一个微型 PNG fixture，放入合成，添加 Tint 并设置 Amount。
5. 执行 `inspect_comp`、`inspect_layer`、`inspect_footage`，校验 AE 实际读回值。
6. 在 1 秒处执行现有无 Render Queue 的 PNG frame capture，校验文件存在、尺寸正确。
7. 清理本次 namespaced item，断言既有项目内容和 Render Queue 与基线一致。

### S2：Release Acceptance（分享/发布前，目标 10 分钟内）

在 S1 基础上增加素材丢失、真实输出、错误路径、批量和恢复测试。连续运行三次，确认
不存在残留命名、旧 result 误读或第二次运行失败。

### S3：兼容性抽检（AE/Bridge 版本变化时）

只在升级 AE、Python 或 Bridge transport 后执行。至少覆盖团队实际使用的最低和最高
AE 大版本；不要求每次代码提交都运行。

## 4. 用例矩阵

所有测试对象使用前缀 `AE_BRIDGE_PROD_<runId>_`，目标优先使用 AE item/layer ID；
名称选择器仅用于专门验证唯一性错误。

| ID | 等级 | 场景 | 核心断言 |
|---|---|---|---|
| PF-01 | S0 | Bridge/AE 能力探测 | 返回版本和能力；工程零修改 |
| CP-01 | S1 | 创建、改名合成 | 名称、320×180、24 fps、2 秒、pixel aspect、背景色读回一致 |
| CP-02 | S2 | 修改合成配置 | 只改变显式字段；未传字段保持不变 |
| TX-01 | S1 | 创建和替换文字 | source text、字体大小、颜色、层名读回一致 |
| TR-01 | S1 | Transform 与 keyframe | 0 秒/1 秒值和 keyframe 数一致；预览位置符合预期 |
| FX-01 | S1 | Solid + Fill | effect matchName 和颜色参数读回一致 |
| FX-02 | S1 | Footage + Tint | Tint 成功添加，Amount 读回一致，frame capture 可见变化 |
| FT-01 | S1 | 导入 PNG 并加到合成 | file path、item ID、layer source ID、尺寸一致 |
| FT-02 | S2 | 制造丢失并重链 | 丢失状态可 inspect；重链后恢复；item ID 和图层引用不变 |
| FT-03 | S2 | 重链路径不存在 | 明确失败；原 FootageItem 未改变；不新增 project item |
| OUT-01 | S1 | 无 RQ 单帧预览 | PNG 非空、尺寸正确；RQ 前后完全一致 |
| OUT-02 | S2 | 0.5 秒真实输出 | 输出存在且非空；只渲染测试项；既有 RQ 状态恢复 |
| NEG-01 | S2 | comp/layer 不存在 | 错误含 selector、operation、JSX line；零修改 |
| NEG-02 | S2 | 同名 comp/layer | 拒绝歧义；提示改用 ID/index；零修改 |
| NEG-03 | S2 | 参数错误 | 负尺寸、非法 RGB、错误 fps 在 Python 侧拒绝，AE 不启动 |
| NEG-04 | S2 | effect/参数不存在 | 返回具体 match path；不留下半添加 effect |
| BAT-01 | S2 | 连续批量 8 项 | 一次往返；顺序与 `completedCount` 正确；inspect 值一致 |
| BAT-02 | S2 | batch 中途失败 | fail-fast；报告已完成项；后续项未执行；状态可 inspect |
| REC-01 | S2 | timeout/中断 | 报告 state unknown；不自动重试 mutation；随后 inspect 可恢复 |
| REG-01 | S2 | 旧 operation 回归 | 现有 6 个 operation 与 raw JSX 入口继续工作 |
| CLEAN-01 | S1/S2 | 清理与不变量 | 无 namespaced item、无测试 RQ item、无 temp 外输出 |

## 5. 素材丢失与替换的确定性流程

素材丢失测试不能搜索整块硬盘，也不能依赖同事机器上的真实素材。建议提供两个极小、
可再分发的 PNG fixture：`source_a.png` 和 `source_b.png`，图案和颜色明显不同。

测试流程：

1. Harness 将 `source_a.png` 复制到 run temp 并导入。
2. 将其添加为图层，记录 FootageItem ID、layer source ID 和首次截图。
3. 由 host harness 把临时文件改名为 `.missing`，再调用 `inspect_footage`。
4. 把 `source_b.png` 复制到新的确定路径，调用 `relink_footage`。
5. 验证 `footageMissing=false`、FootageItem ID 未变、所有引用该 item 的层仍有效，并
   截图确认图案已更新。

本轮不封装自动搜索。Bridge 只报告素材原路径、`fileExists`、AE 的
`footageMissing` 和合并后的 `missing`。用户或 Agent 明确选择一个替换文件后，才调用
`relink_footage`。不扫描盘符、不自动选择候选、不自动重链，也不在错误后尝试其他路径。

## 6. 输出测试策略

输出分为两类，避免每个 smoke test 都污染 Render Queue 或等待渲染：

- **预览**：继续使用现有 `saveFrameToPng` 路径，不创建 Render Queue item。
- **正式输出**：只在 S2 执行 320×180、0.5 秒合成。模板名必须来自 Preflight 的
  实际可用列表或团队配置，不能硬编码英文/中文默认名。

`render_comp` 应执行完整隔离生命周期：

1. 快照所有既有 Render Queue item 的 render 状态和输出路径。
2. 禁用既有 item，创建唯一测试 item，设置 run temp 下的输出路径。
3. 渲染并验证产物存在、非空；可解析格式时再验证宽高/帧数。
4. 在 `finally` 中删除测试 item 并恢复所有既有状态。
5. 超时或进程中断后把状态标为 unknown；下一步只能先 inspect RQ，不自动重渲。

若机器没有满足要求的模板，OUT-02 应明确 `SKIP: no compatible output template`；
团队正式发布门禁则应安装并配置一个统一测试模板，使该项成为 required。

## 7. 数据、清理与工程保护

测试默认在一次性、已保存的测试工程中运行。即使工程可随意修改，也必须证明它不会
误伤真实工程，因此保留以下不变量：

- 所有 mutation 复用一个本次 run 的 `operation-id`，只创建一次保护备份。
- 运行前后比较既有 project item ID、名称和数量；只删除当前 run 创建的对象。
- 运行前后比较既有 Render Queue item 数、render flag、status 和 output path。
- 所有输出、fixture 副本、截图和结果都位于 run temp；禁止写入素材原目录。
- 清理从最高 layer/item index 向下执行；失败时保留诊断记录，但仍尝试独立清理。
- 不依赖 Undo 作为唯一清理方式。Undo 只用于人工恢复；自动清理按记录的 ID 执行。
- 原始 fixture 只读，测试通过复制件制造缺失和替换。

## 8. 结果格式与验收门槛

每个 case 输出结构化记录：

```json
{
  "caseId": "FT-02",
  "status": "passed",
  "durationMs": 1530,
  "operationId": "prod-20260716-001",
  "assertions": [],
  "artifacts": [],
  "cleanup": "passed"
}
```

发布门槛：

- S0、S1 和所有 required S2 用例 100% 通过；optional 只能因记录在案的环境能力缺失
  而 skip。
- 连续三次 Release Acceptance 均通过。
- 既有 project item 和 Render Queue 的前后差异为零。
- 所有错误都有 operation、target、原因；JSX 错误还应包含 line。
- 不出现 modal dialog，不读取过期 result，不在 timeout 后自动重复 mutation。
- batch 相比逐项调用的主要指标是减少 Bridge round trip；不设脆弱的机器绝对耗时
  门槛，只记录单次、batch 和总耗时用于回归比较。

严重级别：

- **P0**：误改既有工程/RQ、输出到错误路径、保护备份失败、静默选错目标。
- **P1**：operation 结果错误、残留测试对象、错误不可定位、timeout 后重复 mutation。
- **P2**：可选模板缺失、预览差异或耗时回退但功能结果正确。

P0/P1 任一出现均阻止分享发布。

## 9. 建议目录与模块边界

实施时保持 stdlib-only host，并将领域代码与测试代码分开：

```text
assets/bridge/
├─ client/
│  ├─ run_operation.py
│  ├─ run_production_tests.py       # suite orchestration/report only
│  └─ test_*.py                     # host unit tests
├─ operations/
│  ├─ ae_operations.jsx             # dispatcher/public contract
│  └─ modules/                      # comp/layer/footage/effects/output handlers
├─ tests/production/
│  ├─ README.md
│  ├─ manifest.json                 # suites, ordering, required/optional
│  ├─ cases/                        # request and expected assertions
│  └─ fixtures/                     # tiny redistributable media only
└─ scripts/
   └─ ...                           # raw JSX escape hatch/integration probes
```

`modules/` 可在实施新增领域时再拆；不为了目录美观预先重构现有工作代码。公开 operation
只返回 JSON 数据，不负责测试断言。Harness 不持有业务逻辑，只编排、制造 fixture 状态、
比较基线和清理。

## 10. 推荐实施顺序

1. **Comp + Solid + Effects**：先实现 `create_comp`、`set_comp`、`create_solid`、
   `add_effect`、`set_effect_property`，完成 CP/FX 正负用例。
2. **Footage**：实现 import/add/inspect/relink，用微型 PNG 完成确定性丢失素材测试。
3. **Output**：先复用 frame capture，再实现隔离的短 Render Queue 输出。
4. **Suite runner**：最后串联 S0/S1/S2，生成 JSON + 简短 Markdown 汇总，并跑三次。

这样每一步都有独立价值，也能在某个 AE API 不稳定时停止扩面，而不影响已经稳定的
文字、Transform、keyframe、inspect 和 raw JSX 能力。

## 11. 暂不纳入核心套件

- 第三方插件、Preset、MOGRT、Dynamic Link、Cinema 4D、3D Model Layer。
- 项目色彩管理、OCIO、复杂 HDR/32-bpc 输出。
- image sequence 范围、代理、解释素材帧率/alpha 等版本敏感选项。
- spatial tangent、复杂 ease graph、表达式、mask/shape 深层构造。
- 自动全盘搜索和无确认批量重链。
- 长视频、多格式编码和性能 benchmark。

后续仍值得按频率评估的操作是：layer duplicate/delete/reorder、layer timing、parenting、
precompose、marker、expression set/validate，以及通用 property inspect/set。它们不应在
第一版生产验收中扩大测试面。

## 12. 实际测试结果

环境：After Effects 2024 `24.2.1x2`、`en_US`、Windows，输入为两个只读的
200×200 RGBA PNG fixture。fixture 原文件未修改，测试只使用 run temp 中的副本。

- Python：30 tests passed，`py_compile` 通过。
- 最终 Release Acceptance 连续三轮通过；每轮 15 个编排 case，case 累计
  45.3–46.0 秒，wall time 46.5–47.3 秒。
- 正向 batch 一次执行 21 个 operation，覆盖 comp create/update、Solid、文字替换、
  Transform、3 个 position keyframe、素材 import/add、Fill/Tint、effect remove 和 inspect。
- 负向覆盖目标不存在、同名 layer、错误 effect property、错误重链路径；同名 batch
  在前两项完成后返回 `completedCount: 2`。
- 素材文件被移动后，AE 的 `footageMissing` 可能暂时不刷新；新增实时 `fileExists` 和
  合并 `missing` 后可稳定检测。显式重链保持 FootageItem ID 和 layer source 引用不变。
- Fill Color=`ADBE Fill-0002`、Tint Amount=`ADBE Tint-0003` 均由本机 probe 确认，
  没有按显示名猜测。
- 正向帧显示红色电话素材，重链帧显示 cyan 素材；Render Queue 截图和 9 帧动画
  contact sheet 已人工视觉检查，背景、标题、透明度、颜色和水平运动均正确。
- 正式输出为 H.264、384×216、24 fps、2.000 秒、137,976 bytes；抽帧视觉结果与
  Render Queue 截图一致。
- `render_comp` 最初在 Undo Group 中触发 AE warning，现已强制 standalone 且不进入
  Undo Group；后续连续运行无弹窗。
- `saveFrameToPng` 在 32→8 bpc 且刚重链后出现过一次不完整帧，因此重链视觉验收改用
  隔离的 Render Queue capture。既有 Render Queue 在每轮结束后均为 0。
- 250 ms timeout 按预期返回 state unknown，随后只读 inspect 恢复；原始 JSX 错误继续
  返回 `ReferenceError` 和 line 1。
- 最终每轮完整 project item 列表和 Render Queue 都与运行前基线一致，不仅检查测试
  前缀；AE 自动创建的空 `Solids` folder 也会在确认不是基线对象后删除。视觉证据会
  立即复制到 suite 的 `artifacts/`，避免被 Bridge 的最近 10 个 run 轮转删除。
- 同名 layer 负向用例最初创建了顶层灰色 Solid 并遮挡后续画面；现已移到所有视觉和
  输出验收之后，避免测试自身污染视觉证据。
