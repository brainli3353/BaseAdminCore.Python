<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysJob.title') }}</h3>
				<p class="ba-sub">{{ t('sysJob.sub') }}</p>
			</div>
			<div class="header-ops">
				<el-button v-perm="'sysJob/nodes'" @click="openCluster">
					<el-icon><Monitor /></el-icon>{{ t('sysJob.btnCluster') }}
				</el-button>
				<el-button v-perm="'sysJob/add'" type="primary" @click="openAdd">
					<el-icon><Plus /></el-icon>{{ t('sysJob.btnAdd') }}
				</el-button>
			</div>
		</div>

		<!-- 数据卡 -->
		<div class="ba-card">
			<div class="search-row">
				<el-input
					v-model="query.name"
					:placeholder="t('sysJob.phSearchName')"
					clearable
					class="search-input"
					@keyup.enter="reload"
					@clear="reload"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
				<el-select v-model="query.enabled" :placeholder="t('common.phEnabled')" class="search-status" @change="reload">
					<el-option :label="t('common.all')" :value="OPT_ALL" />
					<el-option :label="t('sysJob.statusEnabled')" :value="true" />
					<el-option :label="t('sysJob.statusDisabled')" :value="false" />
				</el-select>
				<el-button type="primary" @click="reload">{{ t('common.search') }}</el-button>
				<el-button @click="doReset">{{ t('common.reset') }}</el-button>
			</div>

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
				<template #cell_enabled="{ row }">
					<span class="st" :class="row.enabled ? 'st-ok' : 'st-off'">
						{{ row.enabled ? t('sysJob.statusEnabled') : t('sysJob.statusDisabled') }}
					</span>
				</template>
				<template #row_ops="{ row }">
					<el-button v-perm="'sysJob/update'" link type="primary" size="small" @click="openEdit(row)">
						{{ t('common.edit') }}
					</el-button>
					<el-button v-perm="'sysJob/logPage'" link type="primary" size="small" @click="openLog(row)">
						{{ t('sysJob.btnLog') }}
					</el-button>
					<!-- 启用/停用/立即执行折「更多」:三者权限任一命中才渲染下拉;逐项自带 v-perm 与确认逻辑不变 -->
					<el-dropdown
						v-perm="['sysJob/enable', 'sysJob/disable', 'sysJob/runNow']"
						trigger="click"
						@command="onRowCommand($event, row)"
					>
						<el-button link type="primary" size="small">{{ moreLabel }}</el-button>
						<template #dropdown>
							<el-dropdown-menu>
								<el-dropdown-item v-perm="'sysJob/enable'" command="enable">{{ t('sysJob.btnEnable') }}</el-dropdown-item>
								<el-dropdown-item v-perm="'sysJob/disable'" command="disable">{{ t('sysJob.btnDisable') }}</el-dropdown-item>
								<el-dropdown-item v-perm="'sysJob/runNow'" command="runNow">{{ t('sysJob.btnRunNow') }}</el-dropdown-item>
							</el-dropdown-menu>
						</template>
					</el-dropdown>
				</template>
			</vxe-grid>
		</div>

		<!-- 新增/编辑对话框 -->
		<el-dialog
			v-model="dialog.visible"
			:title="dialog.mode === 'add' ? t('sysJob.dlgAdd') : t('sysJob.dlgEdit')"
			width="460px"
			destroy-on-close
		>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="84px">
				<el-form-item v-if="dialog.mode === 'add'" :label="t('sysJob.labelJobName')" prop="jobName">
					<el-input v-model="form.jobName" :placeholder="t('sysJob.phJobName')" />
				</el-form-item>
				<el-form-item v-else :label="t('sysJob.labelJobName')">
					<el-input :model-value="dialog.jobNameLabel" disabled />
				</el-form-item>
				<el-form-item :label="t('sysJob.labelInterval')" prop="interval">
					<el-input-number v-model="form.interval" :min="1" :max="86400" />
				</el-form-item>
				<el-form-item v-if="dialog.mode === 'edit'" :label="t('sysJob.labelEnabled')">
					<el-switch v-model="form.enabled" />
				</el-form-item>
				<el-form-item :label="t('common.remark')">
					<el-input v-model="form.remark" :placeholder="t('sysJob.phRemark')" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSave">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>

		<!-- 集群节点(只读:实例节点 + 运行中任务;打开即拉一次数据,失败交全局拦截器) -->
		<el-drawer v-model="cluster.visible" :title="t('sysJob.drawerCluster')" size="640px" destroy-on-close>
			<el-alert
				class="cluster-alert"
				type="info"
				:closable="false"
				show-icon
				:title="t('sysJob.clusterAlert')"
			/>

			<!-- ① 实例节点 -->
			<div class="section-title">
				{{ t('sysJob.sectionNodes') }}
				<el-button link type="primary" size="small" :loading="cluster.loading" @click="loadCluster">{{ t('sysJob.btnRefresh') }}</el-button>
			</div>
			<vxe-grid
				v-if="cluster.nodes.length"
				:loading="cluster.loading"
				:data="cluster.nodes"
				:columns="nodeColumns"
				:row-config="{ keyField: 'instanceId' }"
			>
				<template #node_self="{ row }: { row: JobNodeOutput }">
					<span v-if="row.isSelf" class="st st-self">{{ t('sysJob.tagSelf') }}</span>
					<span v-else>—</span>
				</template>
			</vxe-grid>
			<BaEmpty
				v-else-if="!cluster.loading"
				:message="t('sysJob.emptyNodes')"
			/>

			<!-- ② 运行中任务 -->
			<div class="section-title section-gap">
				{{ t('sysJob.sectionRunning') }}
				<span v-if="cluster.running.length" class="section-hint">{{ t('sysJob.runningCount', { n: cluster.running.length }) }}</span>
			</div>
			<vxe-grid
				v-if="cluster.running.length"
				:loading="cluster.loading"
				:data="cluster.running"
				:columns="runningColumns"
				:row-config="{ keyField: 'jobName' }"
			>
				<template #run_instance="{ row }: { row: JobRunningOutput }">
					{{ row.nodeTag ? `${row.nodeTag} · ` : '' }}{{ shortInstanceId(row.instanceId) }}
				</template>
				<template #run_trigger="{ row }: { row: JobRunningOutput }">{{ triggerText(row.trigger) }}</template>
			</vxe-grid>
			<BaEmpty v-else-if="!cluster.loading" :message="t('sysJob.emptyRunning')" />
		</el-drawer>

		<!-- 执行记录(2026-09-30;只读弹窗:按任务行打开,打开即拉第一页,翻页拉对应页) -->
		<el-dialog v-model="log.visible" :title="t('sysJob.dlgLog')" width="880px" destroy-on-close>
			<vxe-grid
				v-if="log.rows.length"
				:loading="log.loading"
				:data="log.rows"
				:columns="logColumns"
				:pager-config="logPager"
				:row-config="{ keyField: 'id' }"
				:sort-config="{ remote: true }"
				@page-change="onLogPageChange"
				@sort-change="onLogSortChange"
			>
				<template #log_trigger="{ row }: { row: JobLogOutput }">{{ triggerText(row.trigger) }}</template>
				<template #log_duration="{ row }: { row: JobLogOutput }">{{ t('sysJob.unitMs', { n: row.durationMs }) }}</template>
				<template #log_result="{ row }: { row: JobLogOutput }">
					<span class="st" :class="row.success ? 'st-ok' : 'st-off'">
						{{ row.success ? t('sysJob.logSuccess') : t('sysJob.logFailure') }}
					</span>
				</template>
			</vxe-grid>
			<BaEmpty v-else-if="!log.loading" :message="t('sysJob.emptyLog')" />
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
/** 「全部」哨兵：该查询条件为 null ＝ 不带此筛选（业务语义，运行时必须保持 null）。
 *  批 B6：EP 按需后 `el-option.value` 的 prop 类型不再含 null ⇒ 只收口类型、不改值（改成 '' 会让"全部"变成"按空串筛选"）。 */
const OPT_ALL = null as unknown as string | number
	defineOptions({ name: 'SysJob' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Monitor, Search } from '@element-plus/icons-vue'
import BaEmpty from '@/components/BaEmpty.vue'
import * as jobApi from '@/api/sys/job'
import type { JobDetailOutput, JobLogOutput, JobNodeOutput, JobRunningOutput } from '@/api/sys/job'
import { usePaged } from '@/composables/usePaged'

const { t, te } = useI18n()

/** 操作列「更多」文案:i18n 键 `common.more` 未登记时回退中文(同 F0 公共件口径,键补齐后自动跟随)。 */
const moreLabel = computed(() => (te('common.more') ? t('common.more') : '更多'))

const query = reactive({ name: '', enabled: null as boolean | null, orderBy: '' as string, desc: false as boolean })
const { loading, rows, pager, fetchPage, reload, onPageChange } = usePaged<JobDetailOutput>(q =>
	jobApi.pageJob({
		name: query.name || null,
		enabled: query.enabled,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: query.orderBy || undefined,
		desc: query.orderBy ? query.desc : undefined
	})
)

const saving = ref(false)

function doReset(): void {
	query.name = ''
	query.enabled = null
	query.orderBy = ''
	query.desc = false
	reload()
}

function onSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	query.orderBy = order ? property : ''
	query.desc = order === 'desc'
	reload()
}

const columns = computed(() => [
	{ field: 'id', title: 'Id', width: 130, sortable: true },
	{ field: 'jobName', title: t('sysJob.colJobName'), minWidth: 160, sortable: true, showOverflow: 'tooltip' as const },
	{
		field: 'interval',
		title: t('sysJob.colInterval'),
		width: 100,
		sortable: true,
		formatter: ({ cellValue }: { cellValue: number }) => t('sysJob.unitSeconds', { n: cellValue })
	} as object,
	// WHY 用插槽而非 formatter:formatter 返回的字符串在 vxe-table v4 按纯文本渲染,
	// 返回 HTML 会原样显示尖括号(2026-09-24 测试版实证)
	{ field: 'enabled', title: t('sysJob.colEnabled'), width: 90, sortable: true, slots: { default: 'cell_enabled' } } as object,
	{ field: 'lastRunTime', title: t('sysJob.colLastRunTime'), width: 170, sortable: true },
	{ field: 'remark', title: t('common.remark'), minWidth: 140, sortable: true, showOverflow: 'tooltip' as const },
	{ title: t('common.operations'), minWidth: 230, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

const dialog = reactive({ visible: false, mode: 'add' as 'add' | 'edit', id: 0 as number | string, jobNameLabel: '' })
const formRef = ref<FormInstance>()
const form = reactive({ id: 0 as number | string, jobName: '', interval: 3600, enabled: true, remark: '' })
const rules = computed<FormRules>(() => ({
	jobName: [{ required: true, message: t('sysJob.ruleJobNameRequired'), trigger: 'blur' }],
	interval: [{ required: true, message: t('sysJob.ruleIntervalRequired'), trigger: 'blur' }]
}))

function openAdd(): void {
	dialog.mode = 'add'
	dialog.visible = true
	Object.assign(form, { id: 0, jobName: '', interval: 3600, enabled: true, remark: '' })
}

function openEdit(row: JobDetailOutput): void {
	dialog.mode = 'edit'
	dialog.id = row.id
	dialog.jobNameLabel = row.jobName ?? ''
	dialog.visible = true
	Object.assign(form, {
		id: row.id,
		jobName: '',
		interval: row.interval,
		enabled: row.enabled,
		remark: row.remark ?? ''
	})
}

async function onSave(): Promise<void> {
	await formRef.value?.validate()
	saving.value = true
	try {
		if (dialog.mode === 'add') {
			await jobApi.addJob({ jobName: form.jobName, interval: form.interval, remark: form.remark || undefined })
		} else {
			await jobApi.updateJob({
				id: form.id,
				interval: form.interval,
				enabled: form.enabled,
				remark: form.remark || undefined
			})
		}
		ElMessage.success(t('sysJob.msgSaved'))
		dialog.visible = false
		void fetchPage()
	} finally {
		saving.value = false
	}
}

async function onEnable(row: JobDetailOutput): Promise<void> {
	await jobApi.enableJob(row.id)
	ElMessage.success(t('sysJob.msgEnabled'))
	void fetchPage()
}

async function onDisable(row: JobDetailOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('sysJob.msgDisableConfirm', { name: row.jobName }), t('sysJob.msgDisableTitle'), {
			type: 'warning'
		})
	} catch {
		return
	}
	await jobApi.disableJob(row.id)
	ElMessage.success(t('sysJob.msgDisabled'))
	void fetchPage()
}

async function onRunNow(row: JobDetailOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('sysJob.msgRunNowConfirm', { name: row.jobName }), t('sysJob.msgRunNowTitle'), {
			type: 'warning'
		})
	} catch {
		return
	}
	await jobApi.runJobNow(row.id)
	ElMessage.success(t('sysJob.msgRunNowSubmitted'))
}

/** 操作列「更多」分发(启用/停用/立即执行)——复用原处理函数,确认逻辑不变。 */
function onRowCommand(command: string | number | object, row: JobDetailOutput): void {
	const cmd = String(command)
	if (cmd === 'enable') void onEnable(row)
	else if (cmd === 'disable') void onDisable(row)
	else if (cmd === 'runNow') void onRunNow(row)
}

/* ── 集群节点(只读抽屉:实例节点 + 运行中任务) ─────────────────────────────── */
const cluster = reactive({
	visible: false,
	loading: false,
	nodes: [] as JobNodeOutput[],
	running: [] as JobRunningOutput[]
})

/** 拉集群视图(打开抽屉与「刷新」共用;失败由全局拦截器提示,此处不 catch)。 */
async function loadCluster(): Promise<void> {
	cluster.loading = true
	try {
		const data = await jobApi.getJobNodes()
		cluster.nodes = data.nodes ?? []
		cluster.running = data.running ?? []
	} finally {
		cluster.loading = false
	}
}

/** 打开即拉一次数据(destroy-on-close:每次打开都是干净状态,不留上次残留)。 */
function openCluster(): void {
	cluster.nodes = []
	cluster.running = []
	cluster.visible = true
	void loadCluster()
}

/** 实例Id 为长串:表格里只显示简写,全文靠列的 showOverflow=tooltip 悬停查看。 */
function shortInstanceId(id: string): string {
	return id.length > 12 ? `${id.slice(0, 12)}…` : id
}

/** 触发方式中文映射(后端 trigger=scheduled/manual);未知值原样兜底,不吞信息。 */
const triggerLabels = computed<Record<string, string>>(() => ({
	scheduled: t('sysJob.triggerScheduled'),
	manual: t('sysJob.triggerManual')
}))

function triggerText(trigger: string | null): string {
	if (trigger && triggerLabels.value[trigger]) return triggerLabels.value[trigger]
	return trigger || '—'
}

const nodeColumns = computed(() => [
	// WHY 实例Id 长串:showOverflow=tooltip 悬停看全文(vxe 列的溢出提示口径)
	{ field: 'instanceId', title: t('sysJob.colInstanceId'), minWidth: 200, showOverflow: 'tooltip' } as object,
	{ field: 'nodeTag', title: t('sysJob.colNodeTag'), width: 120 },
	{ field: 'startedAt', title: t('sysJob.colStartedAt'), width: 170 },
	{ field: 'lastBeat', title: t('sysJob.colLastBeat'), width: 170 },
	{ field: 'isSelf', title: t('sysJob.colIsSelf'), width: 90, slots: { default: 'node_self' } } as object
])

const runningColumns = computed(() => [
	{ field: 'jobName', title: t('sysJob.colJobName'), minWidth: 150 },
	{ field: 'instanceId', title: t('sysJob.colRunInstance'), minWidth: 190, slots: { default: 'run_instance' } } as object,
	{ field: 'startedAt', title: t('sysJob.colRunStartedAt'), width: 170 },
	{ field: 'trigger', title: t('sysJob.colTrigger'), width: 100, slots: { default: 'run_trigger' } } as object
])

/* ── 执行记录(只读弹窗:sys_job_log 分页,最新在前;2026-09-30) ──────────────────── */
const log = reactive({
	visible: false,
	loading: false,
	jobName: '',
	orderBy: '' as string,
	desc: false as boolean,
	rows: [] as JobLogOutput[]
})
const logPager = reactive({ total: 0, currentPage: 1, pageSize: 10, pageSizes: [10, 20, 50, 100] })

/** 拉当前页(打开弹窗与翻页共用;失败交全局拦截器提示)。 */
async function loadLog(): Promise<void> {
	log.loading = true
	try {
		const res = await jobApi.pageJobLog({
			jobName: log.jobName || null,
			pageIndex: logPager.currentPage,
			pageSize: logPager.pageSize,
			orderBy: log.orderBy || undefined,
			desc: log.orderBy ? log.desc : undefined
		})
		log.rows = res.list ?? []
		logPager.total = Number(res.total)
	} finally {
		log.loading = false
	}
}

/** 按任务行打开(destroy-on-close:每次打开都是干净状态,回到第一页)。 */
function openLog(row: JobDetailOutput): void {
	log.jobName = row.jobName ?? ''
	log.orderBy = ''
	log.desc = false
	log.rows = []
	logPager.total = 0
	logPager.currentPage = 1
	log.visible = true
	void loadLog()
}

function onLogPageChange(p: { currentPage: number; pageSize: number }): void {
	logPager.currentPage = p.currentPage
	logPager.pageSize = p.pageSize
	void loadLog()
}

function onLogSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	log.orderBy = order ? property : ''
	log.desc = order === 'desc'
	logPager.currentPage = 1
	void loadLog()
}

const logColumns = computed(() => [
	{ field: 'triggeredAt', title: t('sysJob.colLogTriggeredAt'), width: 170, sortable: true },
	{ field: 'trigger', title: t('sysJob.colTrigger'), width: 90, sortable: true, slots: { default: 'log_trigger' } } as object,
	{ field: 'durationMs', title: t('sysJob.colDurationMs'), width: 100, sortable: true, slots: { default: 'log_duration' } } as object,
	{ field: 'success', title: t('sysJob.colResult'), width: 90, sortable: true, slots: { default: 'log_result' } } as object,
	{ field: 'errorMsg', title: t('sysJob.colErrorMsg'), minWidth: 200, sortable: true, showOverflow: 'tooltip' } as object,
	{ field: 'nodeTag', title: t('sysJob.colNodeTag'), width: 120, sortable: true, showOverflow: 'tooltip' } as object
])

onMounted(() => {
	void fetchPage()
})
</script>

<style scoped>
.header-ops {
	display: flex;
	align-items: center;
	gap: 10px;
}

.search-row {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 14px;
}
.search-input {
	max-width: 280px;
}
.search-status {
	width: 130px;
}

:deep(.st) {
	display: inline-block;
	padding: 2px 8px;
	border-radius: 10px;
	font-size: 12px;
}
:deep(.st-ok) {
	background: rgb(16 185 129 / 12%);
	color: #059669;
}
:deep(.st-off) {
	background: rgb(239 68 68 / 10%);
	color: #dc2626;
}

/* 抽屉内小节标题(与 sysDatabase 页同口径) */
.section-title {
	font-size: 14px;
	font-weight: 600;
	margin-bottom: 12px;
}
.section-hint {
	font-size: 12px;
	color: var(--ba-text-tertiary);
	font-weight: 400;
	margin-left: 8px;
}
.section-gap {
	margin-top: 18px;
}
.cluster-alert {
	margin-bottom: 14px;
}
:deep(.st-self) {
	background: var(--ba-brand-soft);
	color: var(--ba-brand);
}
</style>
