<template>
	<!--
		页型模板 · 日志查询页（LogQueryPage）
		源：web/src/views/logAudit/log/index.vue 的单 tab 骨架（批 UX·2026-10-25 抽取；源页审单已 PASS）
		形态：时间范围 + 枚举下拉 + 关键字 → 分页表 → 详情弹窗；本模板只给**一个 tab**。
		  多 tab 扩展（源页做法，照抄即可）：每个 tab 用 `v-if="canXxx"` **整块**控制——
		  `v-perm` 只摘 DOM、拦不住 mounted 拉数，未授权 tab 必须既不渲染也不发请求。
		抄法：整文件复制为 web/src/views/<domain>/<entity>/index.vue，再按文件内 ⚠ 标注替换三处：
		  ① 数据源（pageDemoLog / getDemoLogDetail 示例函数 → `@/api/<domain>/<entity>'`）
		  ② i18n 命名空间（demo.* → **新页自建命名空间**，zh-CN / en-US 两文件同键）
		  ③ 实体（DemoLogRow / DemoLogDetail → 业务日志 DTO）、列定义、详情字段
		审单口径单源：docs/可用性审单_框架管理页.md。
	-->
	<div class="ba-page">
		<!-- 页头：日志页无新增；导出按 D1（后端已有导出端点才保留） -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('demo.title') }}</h3>
				<p class="ba-sub">{{ t('demo.sub') }}</p>
			</div>
			<!-- ⚠ 无导出端点时删掉本按钮与 onExport -->
			<el-button v-perm="'demo/export'" :loading="exporting" @click="onExport">
				<el-icon><Download /></el-icon>{{ t('common.export') }}
			</el-button>
		</div>

		<div class="ba-card">
			<!-- A 筛选区：A1 关键字 / A2 枚举下拉 / A3 时间范围（日志页必有）/ A4 重置 / A6 回车 -->
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
				<el-select v-model="query.level" class="search-select">
					<el-option :label="t('common.all')" :value="null" />
					<el-option v-for="lv in LEVELS" :key="lv" :label="lv" :value="lv" />
				</el-select>
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
				<el-button @click="doReset">{{ t('common.reset') }}</el-button>
			</div>

			<!-- B4 loading 遮罩 / B6 分页由 usePaged 提供 / C3 失败由 api/request.ts 拦截器统一透出 errCode -->
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
				<!-- B8 级别列 tag 色义（Error 红 / Warning 橙 / 其余灰蓝） -->
				<template #cell_level="{ row }">
					<el-tag :type="levelTagType(row.level)" disable-transitions size="small">{{ row.level ?? '—' }}</el-tag>
				</template>
				<template #row_ops="{ row }">
					<el-button v-perm="'demo/detail'" link type="primary" size="small" @click="openDetail(row)">
						{{ t('demo.btnDetail') }}
					</el-button>
				</template>
				<!-- B5 空态分态 -->
				<template #empty>
					<BaEmpty :state="loading ? 'loading' : 'empty'" />
				</template>
			</vxe-grid>
		</div>

		<!-- 详情弹窗骨架：meta 行 + 若干 <pre> 长文本块（D3 宽度 760px 与长文本匹配） -->
		<el-dialog v-model="detail.visible" :title="t('demo.dlgDetail')" width="760px" destroy-on-close>
			<p v-if="detail.data" class="dialog-meta">
				{{ detail.data.controllerName }}/{{ detail.data.actionName }} · {{ detail.data.account }} ·
				{{ formatDateTime(detail.data.createTime) }} · traceId={{ detail.data.traceId }}
			</p>
			<div v-loading="detail.loading">
				<h4 class="pre-title">{{ t('demo.labelRequestParam') }}</h4>
				<pre class="log-pre">{{ detail.data?.requestParam || t('demo.empty') }}</pre>
				<h4 class="pre-title">{{ t('demo.labelReturnResult') }}</h4>
				<pre class="log-pre">{{ detail.data?.returnResult || t('demo.empty') }}</pre>
				<h4 class="pre-title">{{ t('demo.labelException') }}</h4>
				<pre class="log-pre log-pre-ex">{{ detail.data?.exception || t('demo.empty') }}</pre>
			</div>
			<template #footer>
				<el-button @click="detail.visible = false">{{ t('common.close') }}</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'DemoLogQueryPage' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Download, Search } from '@element-plus/icons-vue'
import BaEmpty from '@/components/BaEmpty.vue'
import { usePaged } from '@/composables/usePaged'
import { formatDateTime } from '@/utils/format'
import type { PageResult } from '@/types/api'

const { t } = useI18n()

/* ══════════ ①⚠ 示例数据源（骨架自洽用，抄页时整块替换）══════════
 * 列表：pageDemoLog → `demoApi.pageXxx({...})`；详情：getDemoLogDetail → `demoApi.xxxDetail(id)`。
 * 范式：筛选项**显式**拼参（A1–A3）、pageIndex/pageSize 由 usePaged 注入、orderBy/desc 透传（B2）。 */
interface DemoLogRow {
	id: string
	controllerName: string
	actionName: string
	account: string
	level: string | null
	traceId: string
	createTime: string | null
}

interface DemoLogDetail {
	controllerName: string
	actionName: string
	account: string
	createTime: string | null
	traceId: string
	requestParam: string | null
	returnResult: string | null
	exception: string | null
}

interface DemoLogPageInput {
	keyword: string | null
	level: string | null
	startTime: string | null
	endTime: string | null
	pageIndex: number
	pageSize: number
	orderBy?: string
	desc?: boolean
}

async function pageDemoLog(_input: DemoLogPageInput): Promise<PageResult<DemoLogRow>> {
	return { total: 0, list: [] }
}

async function getDemoLogDetail(_id: string): Promise<DemoLogDetail> {
	return {
		controllerName: '',
		actionName: '',
		account: '',
		createTime: null,
		traceId: '',
		requestParam: null,
		returnResult: null,
		exception: null
	}
}

/** A2 枚举下拉候选项：值 = 后端枚举字面量（禁硬编码中文展示，label 原样即可） */
const LEVELS = ['Trace', 'Information', 'Warning', 'Error', 'Critical'] as const

type DateRange = [string, string] | null
/** A3 日志时间范围默认时刻：起 00:00:00 / 止 23:59:59（后端闭区间） */
const defaultTime: [Date, Date] = [new Date(2000, 0, 1, 0, 0, 0), new Date(2000, 0, 1, 23, 59, 59)]

const query = reactive({
	keyword: '',
	level: null as string | null,
	range: null as DateRange,
	orderBy: '' as string,
	desc: false as boolean
})

const { loading, rows, pager, fetchPage, reload, onPageChange } = usePaged<DemoLogRow>(q =>
	pageDemoLog({
		keyword: query.keyword || null,
		level: query.level,
		startTime: query.range?.[0] ?? null,
		endTime: query.range?.[1] ?? null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: query.orderBy || undefined,
		desc: query.orderBy ? query.desc : undefined
	})
)

/** A4 重置 + A5（reload 内部回第一页） */
function doReset(): void {
	Object.assign(query, { keyword: '', level: null, range: null, orderBy: '', desc: false })
	reload()
}

function onSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	query.orderBy = order ? property : ''
	query.desc = order === 'desc'
	reload()
}

/** B8 级别色义 */
function levelTagType(level: string | null): 'danger' | 'warning' | 'info' {
	if (level === 'Error' || level === 'Critical') {
		return 'danger'
	}
	if (level === 'Warning') {
		return 'warning'
	}
	return 'info'
}

const columns = computed(() => [
	// B1 长文本列 tooltip：controllerName / traceId / exception 类字段必标
	{ field: 'controllerName', title: t('demo.colController'), minWidth: 140, sortable: true, showOverflow: 'tooltip' },
	{ field: 'actionName', title: t('demo.colAction'), minWidth: 120, sortable: true, showOverflow: 'tooltip' },
	{ field: 'account', title: t('demo.colAccount'), width: 120, sortable: true },
	{ field: 'level', title: t('demo.colLevel'), width: 110, sortable: true, slots: { default: 'cell_level' } } as object,
	{ field: 'traceId', title: 'TraceId', minWidth: 170, sortable: true, showOverflow: 'tooltip' },
	// B2 时间列 formatDateTime 统一 + 可排序
	{
		field: 'createTime',
		title: t('demo.colTime'),
		width: 170,
		sortable: true,
		formatter: ({ cellValue }: { cellValue: string | null }) => formatDateTime(cellValue)
	} as object,
	// B7 操作列右 sticky
	{ title: t('common.operations'), width: 100, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

/* ── 详情弹窗：先开弹窗显 loading（长文本加载期间不空白），finally 复位 ── */
const detail = reactive({
	visible: false,
	loading: false,
	data: null as DemoLogDetail | null
})

async function openDetail(row: DemoLogRow): Promise<void> {
	detail.data = null
	detail.visible = true
	detail.loading = true
	try {
		detail.data = await getDemoLogDetail(row.id)
	} finally {
		detail.loading = false
	}
}

/* ── 导出（D1：存在才评；无端点删按钮 + 本函数）──────────────────── */
const exporting = ref(false)

async function onExport(): Promise<void> {
	exporting.value = true
	try {
		// ⚠ 抄页替换：await demoApi.exportDemoLog({ ...query })（大文件走 utils/download.ts）
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
.search-row {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 14px;
	flex-wrap: wrap;
}
.search-input {
	width: 200px;
}
.search-select {
	width: 130px;
}
.search-date {
	width: 300px;
}

.dialog-meta {
	font-size: 12px;
	color: var(--ba-text-tertiary);
	margin: 0 0 10px;
	word-break: break-all;
}
.pre-title {
	margin: 12px 0 6px;
	font-size: 13px;
}
.log-pre {
	max-height: 200px;
	overflow: auto;
	background: rgb(0 0 0 / 4%);
	border-radius: 6px;
	padding: 10px 12px;
	font-size: 12px;
	line-height: 1.6;
	white-space: pre-wrap;
	word-break: break-all;
	margin: 0;
}
.log-pre-ex {
	max-height: 280px;
	color: #dc2626;
}
</style>