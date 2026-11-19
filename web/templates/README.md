# 页型模板（web/templates/）

> **约定口径：新页面从模板起，不从零手搓。** 新增/改造管理页按 `CLAUDE.md` 约定 14 立项时，
> 以 `docs/可用性审单_框架管理页.md` 的 A/B/C 清单为默认验收要求（P0/P1 必做、P2 按需）；
> 「能跑但粗糙」不算完成。三型模板取自 22 页审单的达标页（批 UX·2026-10-25），fork 后随快照继承。

## 受检与验证说明（先读）

`web/templates/` **不在** `web/tsconfig.json` 的 `include`（`src/**/*.vue`）内 ⇒ 本目录的 `.vue`
**不参与** `vue-tsc`。**复制进 `web/src/views/<domain>/<entity>/index.vue` 后即受检**
（`cd web && npx vue-tsc --noEmit`）；本批已按此以「复制试跑」方式验证三型均可通过 vue-tsc，试跑件已删除。

三型均为**自洽骨架**：不 import 任何不存在的 `@/api/...` 模块，示例数据源写成文件内本地函数
（`pageDemo` / `getDemoTree` / `pageDemoLog`），复制后能直接编译通过；接真实接口时按文件内
`⚠ 抄页替换` 标注整块替换即可（不替换 = 页面渲染空表，不报错）。

## 通用抄法（三型相同）

1. **复制**：`web/templates/<Xxx>Template.vue` → `web/src/views/<domain>/<entity>/index.vue`。
2. **替换三处**（文件头注释与 `⚠` 标注已标出）：
   - ① 数据源：示例函数 → `import * as xxxApi from '@/api/<domain>/<entity>'`，并把 `usePaged` 的 fetcher 换成真实 `xxxApi.pageXxx({...})`；
   - ② **i18n 命名空间自建**：模板里一律用 `demo.*` 占位；新页必须自建命名空间（如 `sysXxx.*`），
     并在 `web/src/i18n/zh-CN.ts` 与 `web/src/i18n/en-US.ts` **两文件同键**补齐（缺键 = 界面显示 key 原文）；
   - ③ 实体：`DemoRow` / `DemoTreeNode` / `DemoLogRow` → 业务输出 DTO（类型对齐后端 `Output`）。
3. **接线**：路由 + 菜单种子（目录/菜单/按钮权限键与 `[MenuPerm]` 一一对应，约定 14）。
4. **双门**：`cd web && npx vue-tsc --noEmit && npx vite build` 全绿。

> 模板内每个关键位都带**审单条目号注释**（如 `A5`、`B1`、`C2`）——抄的人看得见「为什么必须这么写」，
> 评审也按同一编号对号入座。**不要删这些注释**，它们是审单条目的可追溯锚点。

> 收纳口径澄清：操作列「前 2 直出 + 更多收纳」对应审单 **B7**（不是 C3）；审单 **C3** 是
> 「错误经 `errCode` 透出」，由 `web/src/api/request.ts` 响应拦截器全站统一承载（页面**不吞异常**
> 即合规，无需逐页写码）。

---

## 一、ListPageTemplate.vue —— 列表页

- **源**：`web/src/views/messageCenter/sysNotice/index.vue`（另有 sysConfig/sysEnum/sysNotice 同型可参照）。
- **何时用**：主数据 CRUD 列表 —— 一个平铺实体 + 分页表 + 查询筛选 + 新增/编辑/删除。
  典型：sysNotice、sysConfig、sysPos、sysTenant、sysSerial、sysPrint …… 凡「一页管一张主表」都选这型。
- **怎么抄**：搜索区（关键字 + 状态枚举 + 日期范围 + 查询/重置）→ `usePaged` 接线 → `vxe-grid`
  → 操作列；表单弹窗骨架已给（校验/保存 loading/成功刷新 toast）。导出按钮与 `onExport` 在
  **后端没有导出端点时删掉**（D1「存在才评」）。
- **必查审单条目**：
  - **A**：A1 关键字（`@keyup.enter` 触发，`@clear` 立即重查）、A2 状态/枚举下拉（值 = 后端枚举值，
    label 走 i18n，禁硬编码中文）、A3 时间范围（`default-time` 起 00:00:00 / 止 23:59:59）、
    A4 重置（清全部筛选）、**A5 筛选/排序后回第一页**（走 `usePaged.reload()`，内部 `currentPage = 1`）、A6 回车触发。
  - **B**：B1 长文本列 `showOverflow: 'tooltip'`、B2 时间列 `formatDateTime` + `sortable`（remote 排序）、
    B3 雪花 id 全展示（G33 后为 string，禁截断）、B4 `:loading`、B5 空态 `BaEmpty`（loading/empty 分态）、
    B6 分页总条数与 page-size（`usePaged` 的 pager 已带 `pageSizes: [10,20,50,100]`）、
    B7 操作列右 `fixed: 'right'` + `BaActionButtons`（前 2 直出、第 3 项起折「更多」）、B8 状态列 tag 色义。
  - **C**：C1 删除二次确认（`ElMessageBox.confirm`，文案指名对象）、C2 提交中 loading + 防重
    （`saving` / `pendingId` 均在 `finally` 复位——漏复位 = 按钮永久卡死）、C3 错误经 `errCode` 透出
    （拦截器统一，页面不吞异常）、C4 成功后 toast + 列表刷新、C5 表单必填校验（提交前前端拦一道）。
  - **D**：D1 导出入口（有端点才挂）、D2 新增/搜索 ≤2 次点击、D3 弹窗宽度 480px（与字段数匹配）。
- **权限写法**：直出按钮可用 `v-perm`；**收纳项够不到 `v-perm`**，故操作项权限一律走
  `actions[].hidden`（`hidden` 项不渲染但保留原下标），权限判定用 `can()`（超管 `accountType === 999` 直通）。

## 二、TreeTablePageTemplate.vue —— 树表页

- **源**：`web/src/views/sys/sysOrg/index.vue`（sysDict / menu 同族可参照）。
- **何时用**：层级数据（机构/菜单/分类/字典类型）—— 一棵树既当列表又当选择器，且需要「在某节点下新增子节点」。
- **形态说明**：源页取的是**树形表格**（`vxe-grid` + `tree-config` + `radio-config` + 选中反馈条）。
  若目标页要**左树右表**：左侧换 `el-tree`（`:data` 同一棵树）、右侧 grid 去掉 `tree-config`，
  并把 `onRowClick` 改挂 `el-tree` 的 `@node-click`；**选中反馈条与「新增子节点父级语义」照抄不变**。
- **怎么抄**：树**一次全量加载**（不分页，这是前端递归过滤的前提）→ 关键字前端递归过滤 → 树表渲染
  → 行点击选中反馈条 → 新增/编辑弹窗（父级只读回显）。
- **必查审单条目**：
  - **A**：A1 关键字 —— 后端无对应参数，**在前端递归过滤**（审单边界：记「前端过滤」而非「需后端件」）；
    命中自身**保留整棵子树**，仅子命中时收窄为命中的子树。A2/A3/A6 不适用（树无状态筛选/时间范围，过滤即时生效）；
    「清空关键字」由 `<el-input clearable>` 承载。
  - **B**：B1 名称/编码/备注列 `showOverflow: 'tooltip'`、B4 `:loading`、B5 空态 `BaEmpty`（分态）、
    B7 操作列右 sticky + `BaActionButtons`（新增子节点/编辑直出、删除收纳）、B8 状态列 tag 色义
    （**必须用插槽**：`formatter` 返回串在 vxe v4 按纯文本渲染，标签会被显示成尖括号）。
  - **C**：C1 删除二次确认、C2 `pendingId` per-row 防重（`finally` 复位）、C3 拦截器统一、C4 成功 toast + 树刷新、
    C5 名称必填。另：删除当行若正是选中行，须清空 `selected` 反馈条（不留悬空选中）。
  - **D**：D2 新增顶级（页头）+ 行内新增子节点、D3 弹窗 460px。
  - **额外必查（源页经验）**：父级回显找不到时**回落 `#id`**（不静默空）；编辑时**回传 pid**
    （增量更新口径，勿默认 pid=0 把节点挪到顶级）；行内按钮 `@click.stop` 防触发选中。

## 三、LogQueryPageTemplate.vue —— 日志查询页

- **源**：`web/src/views/logAudit/log/index.vue` 的单 tab 骨架（源页有多 tab / 多详情弹窗，本模板只取一个 tab）。
- **何时用**：只读、按时间范围为主轴的查询页 —— 操作日志/登录日志/异常日志/HTTP 出站日志/差异日志，
  以及任何「时间窗 + 枚举 + 关键字 → 列表 → 详情弹窗」的审计面。
- **怎么抄**：时间范围 + 枚举下拉 + 关键字 → `usePaged` → `vxe-grid` → 详情弹窗（meta 行 + 多个 `<pre>` 长文本块）。
  无新增/编辑/删除，故表单与危险确认不涉及。
- **多 tab 扩展**（源页做法，直接照抄）：每个 tab 用 `v-if="canXxx"` **整块**控制 —— `v-perm` 只摘 DOM、
  拦不住 `onMounted` 拉数；未授权 tab 必须**既不渲染也不发请求**（源页 `hasPerm()` + `onMounted` 分条件 fetch）。
- **必查审单条目**：
  - **A**：A1 关键字、A2 枚举下拉（值为后端枚举字面量如 `Error`/`Warning`）、A3 时间范围（日志页必有）、
    A4 重置、A5 回第一页、A6 回车触发。
  - **B**：B1 tooltip（controllerName / traceId / 长文本）、B2 `formatDateTime` + 可排序、B4 `:loading`、
    B5 空态 `BaEmpty`、B6 分页、B7 详情列右 sticky、B8 级别 tag 色义（Error/Critical 红、Warning 橙、其余灰蓝）。
  - **C**：C2 详情弹窗 `v-loading`（先开弹窗显 loading，`finally` 复位）、C3 拦截器统一。
    **C1/C4/C5 不适用**（纯查询页无写操作、无表单）。
  - **D**：D1 导出入口（有端点才挂）、D3 弹窗 760px（`<pre>` 长文本需宽度匹配）。

---

## 审单条目覆盖矩阵

| 审单条目 | ListPageTemplate | TreeTablePageTemplate | LogQueryPageTemplate |
|---|---|---|---|
| A1 关键字 | ✅ 回车/清空重查 | ✅ 前端递归过滤（保子树） | ✅ |
| A2 枚举下拉 | ✅ 状态 | — 不适用 | ✅ 日志级别 |
| A3 时间范围 | ✅ daterange | — 不适用 | ✅ daterange |
| A4 重置 | ✅ | — 不适用 | ✅ |
| A5 筛选回第一页 | ✅ `usePaged.reload` | — 不适用（前端过滤） | ✅ `usePaged.reload` |
| A6 回车触发 | ✅ | — 不适用（即时过滤） | ✅ |
| B1 tooltip | ✅ | ✅ | ✅ |
| B2 时间格式+排序 | ✅ | —（树无时间列） | ✅ |
| B3 id 全展示 | ✅ | —（树不展示 id 列） | —（列表不展示 id 列） |
| B4 loading | ✅ | ✅ | ✅ |
| B5 空态 | ✅ `BaEmpty` 分态 | ✅ `BaEmpty` 分态 | ✅ `BaEmpty` 分态 |
| B6 分页 | ✅ `usePaged` pager | —（树全量加载） | ✅ `usePaged` pager |
| B7 操作列右 sticky + >3 收纳 | ✅ `BaActionButtons` | ✅ `BaActionButtons` | ✅ 详情列右 sticky（单动作，无需收纳） |
| B8 状态 tag 色义 | ✅ | ✅（插槽） | ✅（级别色义） |
| C1 危险二次确认 | ✅ 删除 | ✅ 删除 | — 不适用 |
| C2 提交 loading/防重 | ✅ saving + pendingId | ✅ pendingId | ✅ 详情 v-loading |
| C3 errCode 透出 | ✅ 拦截器统一 | ✅ 拦截器统一 | ✅ 拦截器统一 |
| C4 成功 toast+刷新 | ✅ | ✅ | — 不适用 |
| C5 表单校验 | ✅ | ✅ | — 不适用 |
| D1 导出入口 | ✅（无端点则删） | — | ✅（无端点则删） |
| D2 高频动作 ≤2 点击 | ✅ | ✅ | —（只读页） |
| D3 弹窗宽度匹配 | ✅ 480px | ✅ 460px | ✅ 760px（长文本块） |

清单指针（逐项判据原文）：`docs/可用性审单_框架管理页.md`。