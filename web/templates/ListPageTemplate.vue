<template>
	<!--
		页型模板 · 列表页（ListPage）
		源：web/src/views/messageCenter/sysNotice/index.vue（批 UX·2026-10-25 抽取；源页审单已 PASS）
		抄法：整文件复制为 web/src/views/<domain>/<entity>/index.vue，再按文件内 ⚠ 标注替换三处：
		  ① 数据源（pageDemo 示例函数 → `import * as demoApi from '@/api/<domain>/<entity>'`）
		  ② i18n 命名空间（demo.* → **新页自建命名空间**，zh-CN / en-US 两文件同键）
		  ③ 实体（DemoRow → 业务输出 DTO）、列定义、表单字段
		审单口径单源：docs/可用性审单_框架管理页.md（A 筛选 / B 表格 / C 操作与反馈）。
	-->
	<div class="ba-page">
		<!-- 页头 + 工具栏：新增（D2 高频动作 ≤2 点击）/ 导出（D1 后端已有导出端点才保留） -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('demo.title') }}</h3>
				<p class="ba-sub">{{ t('demo.sub') }}</p>
			</div>
			<div class="toolbar">
				<el-button v-perm="'demo/add'" type="primary" @click="openAdd">
					<el-icon><Plus /></el-icon>{{ t('common.add') }}
				</el-button>
				<!-- ⚠ 无导出端点时：删掉本按钮与 onExport 函数（D1「存在才评」） -->
				<el-button v-perm="'demo/export'" :loading="exporting" @click="onExport">
					<el-icon><Download /></el-icon>{{ t('common.export') }}
				</el-button>
			</div>
		</div>

		<!-- 数据卡 -->
		<div class="ba-card">
			<!-- A 筛选区：A1 关键字 / A2 状态枚举下拉 / A3 时间范围 / A4 重置 / A6 回车触发 -->
			<div class="search-row">
				<el-input
					v-model="query.keyword"
					:placeholder="t('demo.phKeyword')"
					clearable
					class="search-input"
					@keyup.enter="reload"
					@clear="reload"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
				<!-- A2 枚举下拉：选项值 = 后端枚举值（禁硬编码中文，label 走 i18n） -->
				<el-select v-model="query.status" class="search-select">
					<el-option :label="t('common.all')" :value="null" />
					<el-option :label="t('demo.statusEnabled')" :value="0" />
					<el-option :label="t('demo.statusDisabled')" :value="1" />
				</el-select>
				<!-- A3 时间范围：起 00:00:00 / 止 23:59:59（后端闭区间） -->
				<el-date-picker
					v-model="query.range"
					type="daterange"
					value-format="YYYY-MM-DD HH:mm:ss"
					:default-time="defaultTime"
					:start-placeholder="t('demo.phStartDate')"
					:end-placeholder="t('demo.phEndDate')"
					clearable
					class="search-date"
				/>
				<el-button type="primary" @click="reload">{{ t('common.search') }}</el-button>
				<!-- A4 重置：清全部筛选并回第一页重查 -->
				<el-button @click="doReset">{{ t('common.reset') }}</el-button>
			</div>

			<!-- B4 loading 遮罩 / B6 分页总条数与 page-size（pager 由 usePaged 提供，已带 10/20/50/100）
			     / C3 请求失败由 api/request.ts 拦截器统一弹错并透出 errCode，页面不吞异常 -->
			<vxe-grid
				:loading="loading"
				:data="rows"
				:columns="columns"
				:pager-config="pager"
				:row-config="{ keyField: 'id' }"
				:sort-config="{ remote: true }"
				@page-change="onPageChange"
				@sort-change="onSortChange"
			>
				<!-- B8 状态列用 tag 色义（启用绿 / 停用灰 / 异常红），禁裸文本 -->
				<template #cell_status="{ row }">
					<el-tag :type="row.status === 0 ? 'success' : 'info'" disable-transitions size="small">
						{{ row.status === 0 ? t('demo.statusEnabled') : t('demo.statusDisabled') }}
					</el-tag>
				</template>
				<!-- B7 操作列：前 2 项直出、第 3 项起折「更多」（BaActionButtons 公共件） -->
				<template #row_ops="{ row }">
					<BaActionButtons :actions="rowActions(row)" @select="(i: number) => onRowAction(row, i)" />
				</template>
				<!-- B5 空态：与 loading 分态（禁「加载中」与「暂无数据」共用一个空态） -->
				<template #empty>
					<BaEmpty :state="loading ? 'loading' : 'empty'" />
				</template>
			</vxe-grid>
		</div>

		<!-- 新增/编辑对话框（C5 表单校验；D3 宽度与内容匹配） -->
		<el-dialog
			v-model="dialog.visible"
			:title="dialog.mode === 'add' ? t('demo.dlgAdd') : t('demo.dlgEdit')"
			width="480px"
			destroy-on-close
		>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="84px">
				<el-form-item :label="t('demo.colName')" prop="name">
					<el-input v-model="form.name" :placeholder="t('demo.phName')" />
				</el-form-item>
				<el-form-item :label="t('demo.colStatus')">
					<el-radio-group v-model="form.status">
						<el-radio :value="0">{{ t('demo.statusEnabled') }}</el-radio>
						<el-radio :value="1">{{ t('demo.statusDisabled') }}</el-radio>
					</el-radio-group>
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dialog.visible = false">{{ t('common.cancel') }}</el-button>
				<!-- C2 提交中按钮 loading（saving 在 finally 复位，防按钮卡死） -->
				<el-button type="primary" :loading="saving" @click="onSave">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'DemoListPage' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Download, Plus, Search } from '@element-plus/icons-vue'
import BaActionButtons from '@/components/BaActionButtons.vue'
import BaEmpty from '@/components/BaEmpty.vue'
import { usePaged } from '@/composables/usePaged'
import { useMenuStore } from '@/stores/menu'
import { useUserStore } from '@/stores/user'
import { formatDateTime } from '@/utils/format'
import type { PageResult } from '@/types/api'

const { t } = useI18n()
const menuStore = useMenuStore()
const userStore = useUserStore()

/* ══════════ ①⚠ 示例数据源（骨架自洽用，抄页时整块替换）══════════
 * 替换法：删掉 DemoRow / DemoPageInput / pageDemo 三件，改成
 *   `import * as demoApi from '@/api/<domain>/<entity>'`
 *   `import type { XxxOutput } from '@/api/<domain>/<entity>'`
 * 并把下方 usePaged 的 fetcher 换成 `demoApi.pageXxx({ ... })`。
 * 范式不可变：fetcher 形参 q 已由 usePaged 注入 pageIndex/pageSize，
 * 其余筛选项必须**显式**拼进请求体（A1–A3），排序 orderBy/desc 透传（B2）。 */
interface DemoRow {
	id: string
	name: string
	status: number
	createTime: string | null
}

interface DemoPageInput {
	keyword: string | null
	status: number | null
	startTime: string | null
	endTime: string | null
	pageIndex: number
	pageSize: number
	orderBy?: string
	desc?: boolean
}

async function pageDemo(_input: DemoPageInput): Promise<PageResult<DemoRow>> {
	return { total: 0, list: [] }
}

type DateRange = [string, string] | null
/** 范围选择默认时刻：起 00:00:00、止 23:59:59（后端闭区间） */
const defaultTime: [Date, Date] = [new Date(2000, 0, 1, 0, 0, 0), new Date(2000, 0, 1, 23, 59, 59)]

const query = reactive({
	keyword: '',
	status: null as number | null,
	range: null as DateRange,
	orderBy: '' as string,
	desc: false as boolean
})

/* usePaged 接线：fetchPage/reload/onPageChange 三件全接（A5 reload 内部回第一页） */
const { loading, rows, pager, fetchPage, reload, onPageChange } = usePaged<DemoRow>(q =>
	pageDemo({
		keyword: query.keyword || null,
		status: query.status,
		startTime: query.range?.[0] ?? null,
		endTime: query.range?.[1] ?? null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: query.orderBy || undefined,
		desc: query.orderBy ? query.desc : undefined
	})
)

/** A4 重置：清空全部筛选字段后走 reload（reload 内部 currentPage = 1，A5） */
function doReset(): void {
	Object.assign(query, { keyword: '', status: null, range: null, orderBy: '', desc: false })
	reload()
}

/** 排序（B2 可排序）：remote 排序语义，改完回第一页（A5） */
function onSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	query.orderBy = order ? property : ''
	query.desc = order === 'desc'
	reload()
}

const columns = computed(() => [
	// B3 雪花 id 全展示：G33 后后端出口为 string，禁 slice/toString 截断（截断=误导）
	{ field: 'id', title: 'Id', width: 190, sortable: true },
	// B1 长文本列：showOverflow 'tooltip'，防撑破布局
	{ field: 'name', title: t('demo.colName'), minWidth: 180, sortable: true, showOverflow: 'tooltip' },
	// B8 状态列走插槽（tag 色义）
	{ field: 'status', title: t('demo.colStatus'), width: 100, slots: { default: 'cell_status' } },
	// B2 时间列：formatDateTime 统一 YYYY-MM-DD HH:mm:ss + 可排序
	{
		field: 'createTime',
		title: t('demo.colCreateTime'),
		width: 170,
		sortable: true,
		formatter: ({ cellValue }: { cellValue: string | null }) => formatDateTime(cellValue)
	} as object,
	// B7 操作列右 sticky
	{ title: t('common.operations'), width: 150, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

/* ── 权限：与 v-perm 同口径（超管 accountType=999 直通）──────────────
 * WHY 不用 v-perm：v-perm 只摘 DOM，够不到 ElDropdown 内的收纳项；
 * 收纳项权限一律走 actions[].hidden（BaActionButtons 对 hidden 项不渲染但保留原下标）。 */
function can(key: string): boolean {
	return userStore.user?.accountType === 999 || menuStore.permissions.includes(key)
}

/** B7 操作列定义：前 2 项直出、第 3 项起收纳；hidden 项不渲染但 index 不变 */
function rowActions(row: DemoRow): { label: string; danger?: boolean; hidden?: boolean; disabled?: boolean }[] {
	return [
		{ label: t('common.edit'), hidden: !can('demo/update') },
		{ label: t('demo.btnDetail'), hidden: !can('demo/detail') },
		{ label: t('common.delete'), danger: true, hidden: !can('demo/delete'), disabled: rowBusy(row) }
	]
}

/** 按 BaActionButtons 回传的原下标映射动作 */
function onRowAction(row: DemoRow, index: number): void {
	if (index === 0) {
		openEdit(row)
	} else if (index === 1) {
		openDetail(row)
	} else if (index === 2) {
		void onDelete(row)
	}
}

/* ── C1 危险确认 / C2 per-row 防重 ─────────────────────────── */
const pendingId = ref<string | null>(null)

function rowBusy(row: DemoRow): boolean {
	return pendingId.value === row.id
}

async function onDelete(row: DemoRow): Promise<void> {
	if (rowBusy(row)) {
		return
	}
	// C1 删除必须二次确认（文案指名对象名，防误点整行）
	try {
		await ElMessageBox.confirm(t('demo.msgDeleteConfirm', { name: row.name }), t('demo.msgDeleteTitle'), {
			type: 'warning'
		})
	} catch {
		return
	}
	pendingId.value = row.id
	try {
		// ⚠ 抄页替换：await demoApi.deleteDemo(row.id)
		ElMessage.success(t('demo.msgDeleted'))
		void fetchPage()
	} finally {
		// C2 finally 复位（漏复位=按钮永久卡死）
		pendingId.value = null
	}
}

/* ── 新增/编辑（C5 校验 / C2 saving / C4 成功刷新+toast）──────────── */
const dialog = reactive({ visible: false, mode: 'add' as 'add' | 'edit' })
const formRef = ref<FormInstance>()
const form = reactive({ id: '' as string, name: '', status: 0 })
const rules = computed<FormRules>(() => ({
	name: [{ required: true, message: t('demo.ruleNameRequired'), trigger: 'blur' }]
}))

function openAdd(): void {
	dialog.mode = 'add'
	dialog.visible = true
	Object.assign(form, { id: '', name: '', status: 0 })
}

function openEdit(row: DemoRow): void {
	dialog.mode = 'edit'
	dialog.visible = true
	Object.assign(form, { id: row.id, name: row.name, status: row.status })
}

function openDetail(row: DemoRow): void {
	// ⚠ 抄页替换：详情弹窗拉 detail 端点，或路由跳详情页
	void ElMessageBox.alert(String(row.id), t('demo.dlgDetail'), { type: 'info' })
}

const saving = ref(false)

async function onSave(): Promise<void> {
	await formRef.value?.validate()
	saving.value = true
	try {
		if (dialog.mode === 'add') {
			// ⚠ 抄页替换：await demoApi.addDemo({ name: form.name, status: form.status })
		} else {
			// ⚠ 抄页替换：await demoApi.updateDemo({ id: form.id, name: form.name, status: form.status })
		}
		// C4 成功后 toast + 列表刷新
		ElMessage.success(t('demo.msgSaved'))
		dialog.visible = false
		void fetchPage()
	} finally {
		saving.value = false
	}
}

/* ── 导出（D1：存在才评；无端点删按钮 + 本函数）──────────────────── */
const exporting = ref(false)

async function onExport(): Promise<void> {
	exporting.value = true
	try {
		// ⚠ 抄页替换：await demoApi.exportDemo({ ...query })（大文件走 utils/download.ts）
		ElMessage.info(t('demo.msgExportTodo'))
	} finally {
		exporting.value = false
	}
}

onMounted(() => {
	void fetchPage()
})
</script>

<style scoped>
.toolbar {
	display: inline-flex;
	align-items: center;
	gap: 8px;
}
.search-row {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 14px;
	flex-wrap: wrap;
}
.search-input {
	max-width: 260px;
}
.search-select {
	width: 130px;
}
.search-date {
	width: 300px;
}
</style>