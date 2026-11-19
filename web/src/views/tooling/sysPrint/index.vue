<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysPrint.title') }}</h3>
				<p class="ba-sub">{{ t('sysPrint.sub') }}</p>
			</div>
			<el-button v-perm="'sysPrint/add'" type="primary" @click="openAdd">
				<el-icon><Plus /></el-icon>{{ t('sysPrint.btnAdd') }}
			</el-button>
		</div>

		<!-- 数据卡 -->
		<div class="ba-card">
			<div class="search-row">
				<el-input
					v-model="query.name"
					:placeholder="t('sysPrint.searchPlaceholder')"
					clearable
					class="search-input"
					@keyup.enter="reload"
					@clear="reload"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
				<el-date-picker
					v-model="query.range"
					type="daterange"
					value-format="YYYY-MM-DD HH:mm:ss"
					:default-time="defaultTime"
					:start-placeholder="t('common.phStartDate')"
					:end-placeholder="t('common.phEndDate')"
					clearable
					class="search-date"
					@change="reload"
					@clear="reload"
				/>
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
				<template #cell_printType="{ row }">
					<span class="st st-info">{{ printTypeLabel(row.printType) }}</span>
				</template>
				<template #cell_status="{ row }">
					<span class="st" :class="row.status === 1 ? 'st-ok' : 'st-off'">
						{{ statusLabel(row.status) }}
					</span>
				</template>
				<template #row_ops="{ row }">
					<el-button v-perm="'sysPrint/detail'" link type="primary" size="small" @click="openDetail(row)">
						{{ t('sysPrint.btnDetail') }}
					</el-button>
					<el-button v-perm="'sysPrint/update'" link type="primary" size="small" @click="openEdit(row)">
						{{ t('common.edit') }}
					</el-button>
					<el-dropdown @command="(cmd: string) => onRowCommand(cmd, row)">
						<el-button link type="primary" size="small">
							{{ t('common.more') }}<el-icon class="more-arrow"><ArrowDown /></el-icon>
						</el-button>
						<template #dropdown>
							<el-dropdown-menu>
								<el-dropdown-item v-perm="'sysPrint/copy'" command="copy">{{ t('sysPrint.btnCopy') }}</el-dropdown-item>
								<el-dropdown-item v-perm="'sysPrint/delete'" command="delete">{{ t('common.delete') }}</el-dropdown-item>
							</el-dropdown-menu>
						</template>
					</el-dropdown>
				</template>
			</vxe-grid>
		</div>

		<!-- 新增/编辑对话框 -->
		<el-dialog
			v-model="dialog.visible"
			:title="dialog.mode === 'add' ? t('sysPrint.dlgAdd') : t('sysPrint.dlgEdit')"
			width="640px"
			destroy-on-close
		>
			<el-form ref="formRef" v-loading="dialog.loading" :model="form" :rules="rules" label-width="84px">
				<el-form-item :label="t('sysPrint.labelName')" prop="name">
					<el-input v-model="form.name" :placeholder="t('sysPrint.namePlaceholder')" />
				</el-form-item>
				<el-form-item :label="t('sysPrint.labelTemplate')" prop="template">
					<el-input
						v-model="form.template"
						type="textarea"
						:rows="10"
						:placeholder="t('sysPrint.phTemplate')"
					/>
					<p class="tpl-hint">{{ t('sysPrint.phTemplateHint') }}</p>
				</el-form-item>
				<el-form-item :label="t('sysPrint.labelType')" prop="printType">
					<el-select v-model="form.printType" class="full-width">
						<el-option v-for="o in PRINT_TYPE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
					</el-select>
				</el-form-item>
				<el-form-item :label="t('sysPrint.labelSort')">
					<el-input-number v-model="form.orderNo" :min="0" :max="9999" />
				</el-form-item>
				<el-form-item :label="t('common.status')" prop="status">
					<el-select v-model="form.status" class="full-width">
						<el-option v-for="o in STATUS_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
					</el-select>
				</el-form-item>
				<el-form-item :label="t('common.remark')">
					<el-input v-model="form.remark" :placeholder="t('sysPrint.remarkPlaceholder')" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" :disabled="dialog.loading || !dialog.detailLoaded" @click="onSave">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>

		<!-- 详情对话框(模板全文 <pre> 展示,本仓不做渲染/预览) -->
		<el-dialog v-model="detail.visible" :title="t('sysPrint.dlgDetail')" width="760px" destroy-on-close>
			<p v-if="detail.data" class="dialog-meta">
				{{ detail.data.name }} · {{ printTypeLabel(detail.data.printType) }} ·
				{{ statusLabel(detail.data.status) }} · {{ t('sysPrint.detailSort', { n: detail.data.orderNo }) }} ·
				{{ detail.data.createTime ?? '—' }}
			</p>
			<div v-loading="detail.loading">
				<h4 class="pre-title">{{ t('sysPrint.fullTemplate') }}</h4>
				<pre class="tpl-pre">{{ detail.data?.template || t('sysPrint.empty') }}</pre>
				<h4 class="pre-title">{{ t('common.remark') }}</h4>
				<pre class="tpl-pre">{{ detail.data?.remark || t('sysPrint.empty') }}</pre>
			</div>
			<template #footer>
				<el-button @click="detail.visible = false">{{ t('sysPrint.btnClose') }}</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'SysPrint' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { ArrowDown, Plus, Search } from '@element-plus/icons-vue'
import * as printApi from '@/api/sys/print'
import type { SysPrintOutput, SysPrintDetailOutput } from '@/api/sys/print'
import { usePaged } from '@/composables/usePaged'
import { formatDateTime } from '@/utils/format'

const { t } = useI18n()
type DateRange = [string, string] | null
/** 范围选择默认时刻:起 00:00:00,止 23:59:59(后端 CreateTime 闭区间) */
const defaultTime: [Date, Date] = [new Date(2000, 0, 1, 0, 0, 0), new Date(2000, 0, 1, 23, 59, 59)]

const query = reactive({ name: '', range: null as DateRange, orderBy: '' as string, desc: false as boolean })
const { loading, rows, pager, fetchPage, reload, onPageChange } = usePaged<SysPrintOutput>(q =>
	printApi.pagePrint({
		name: query.name || null,
		startDate: query.range?.[0] ?? null,
		endDate: query.range?.[1] ?? null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: query.orderBy || undefined,
		desc: query.orderBy ? query.desc : undefined
	})
)

const saving = ref(false)

function doReset(): void {
	query.name = ''
	query.range = null
	query.orderBy = ''
	query.desc = false
	reload()
}

function onSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	query.orderBy = order ? property : ''
	query.desc = order === 'desc'
	reload()
}

/** 打印方式选项(1 浏览器打印 / 2 客户端打印;仅存储语义,本仓后端不渲染)。 */
const PRINT_TYPE_OPTIONS = computed(() => [
	{ value: 1, label: t('sysPrint.printTypeBrowser') },
	{ value: 2, label: t('sysPrint.printTypeClient') }
])
/** 状态选项(1 启用 / 2 停用)。 */
const STATUS_OPTIONS = computed(() => [
	{ value: 1, label: t('sysPrint.statusEnabled') },
	{ value: 2, label: t('sysPrint.statusDisabled') }
])

/** 未知数值容错:显示「类型 N」/「状态 N」,后端扩充取值时前端不误标、不崩。 */
function printTypeLabel(v: number): string {
	return PRINT_TYPE_OPTIONS.value.find(o => o.value === v)?.label ?? t('sysPrint.printTypeFallback', { v })
}
function statusLabel(v: number): string {
	return STATUS_OPTIONS.value.find(o => o.value === v)?.label ?? t('sysPrint.statusFallback', { v })
}

const columns = computed(() => [
	{ field: 'id', title: 'Id', width: 130, sortable: true },
	{ field: 'name', title: t('sysPrint.colName'), minWidth: 160, sortable: true },
	{ field: 'printType', title: t('sysPrint.colType'), width: 110, sortable: true, slots: { default: 'cell_printType' } },
	{ field: 'status', title: t('common.status'), width: 90, sortable: true, slots: { default: 'cell_status' } },
	{ field: 'orderNo', title: t('sysPrint.colSort'), width: 80, sortable: true },
	{ field: 'remark', title: t('common.remark'), minWidth: 140, sortable: true, showOverflow: 'tooltip' },
	{ field: 'createTime', title: t('sysPrint.colCreateTime'), width: 170, sortable: true, formatter: ({ cellValue }: { cellValue: string | null }) => formatDateTime(cellValue) } as object,
	{ title: t('common.operations'), minWidth: 210, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

/* ── 新增 / 编辑 ─────────────────────────────── */
const dialog = reactive({ visible: false, loading: false, detailLoaded: true, mode: 'add' as 'add' | 'edit', id: 0 as number | string })
const formRef = ref<FormInstance>()
const form = reactive({
	id: 0 as number | string,
	name: '',
	template: '',
	printType: 1,
	status: 1,
	orderNo: 0,
	remark: ''
})
const rules = computed<FormRules>(() => ({
	name: [{ required: true, message: t('sysPrint.ruleNameRequired'), trigger: 'blur' }],
	template: [{ required: true, message: t('sysPrint.ruleTemplateRequired'), trigger: 'blur' }]
}))

function openAdd(): void {
	dialog.mode = 'add'
	dialog.id = 0
	dialog.loading = false
	dialog.detailLoaded = true
	dialog.visible = true
	Object.assign(form, { id: 0, name: '', template: '', printType: 1, status: 1, orderNo: 0, remark: '' })
}

async function openEdit(row: SysPrintOutput): Promise<void> {
	dialog.mode = 'edit'
	dialog.id = row.id
	// P0:detail 未取到前禁止保存——后端 Template is not null 才跳过,空串会清空模板
	dialog.detailLoaded = false
	dialog.visible = true
	// 列表行不含 template 大字段:先按行填基本字段,再拉 detail 补全文(避免把空模板回写)
	Object.assign(form, {
		id: row.id,
		name: row.name ?? '',
		template: '',
		printType: row.printType,
		status: row.status,
		orderNo: row.orderNo,
		remark: row.remark ?? ''
	})
	dialog.loading = true
	try {
		const d = await printApi.printDetail(row.id)
		Object.assign(form, {
			name: d.name ?? '',
			template: d.template ?? '',
			printType: d.printType,
			status: d.status,
			orderNo: d.orderNo,
			remark: d.remark ?? ''
		})
		dialog.detailLoaded = true
	} catch {
		ElMessage.error(t('common.loadError'))
	} finally {
		dialog.loading = false
	}
}

async function onSave(): Promise<void> {
	// P0:detail 未取到 ⇒ 不提交(template 空串会清空后端模板)
	if (dialog.mode === 'edit' && !dialog.detailLoaded) {
		ElMessage.warning(t('common.loadError'))
		return
	}
	await formRef.value?.validate()
	saving.value = true
	try {
		// 契约支持部分更新;此处按 detail 拉取后的完整表单整体提交(不传=不改的字段本页恒有值)
		if (dialog.mode === 'add') {
			await printApi.addPrint({
				name: form.name,
				template: form.template,
				printType: form.printType,
				status: form.status,
				orderNo: form.orderNo,
				remark: form.remark || undefined
			})
		} else {
			await printApi.updatePrint({
				id: form.id,
				name: form.name,
				template: form.template,
				printType: form.printType,
				status: form.status,
				orderNo: form.orderNo,
				remark: form.remark || undefined
			})
		}
		ElMessage.success(t('sysPrint.msgSaved'))
		dialog.visible = false
		void fetchPage()
	} finally {
		saving.value = false
	}
}

/* ── 详情 ─────────────────────────────── */
const detail = reactive({ visible: false, loading: false, data: null as SysPrintDetailOutput | null })

async function openDetail(row: SysPrintOutput): Promise<void> {
	detail.data = null
	detail.visible = true
	detail.loading = true
	try {
		detail.data = await printApi.printDetail(row.id)
	} finally {
		detail.loading = false
	}
}

/** 操作列「更多」下拉:复制/删除收折 */
function onRowCommand(command: string, row: SysPrintOutput): void {
	if (command === 'copy') {
		void onCopy(row)
	} else if (command === 'delete') {
		void onDelete(row)
	}
}

/* ── 复制 / 删除 ───────────────────────────── */
async function onCopy(row: SysPrintOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('sysPrint.msgCopyConfirm', { name: row.name }), t('sysPrint.msgCopyTitle'), {
			type: 'warning'
		})
	} catch {
		return
	}
	await printApi.copyPrint(row.id)
	ElMessage.success(t('sysPrint.msgCopied'))
	void fetchPage()
}

async function onDelete(row: SysPrintOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('sysPrint.msgDeleteConfirm', { name: row.name }), t('sysPrint.msgDeleteTitle'), { type: 'warning' })
	} catch {
		return
	}
	await printApi.deletePrint(row.id)
	ElMessage.success(t('sysPrint.msgDeleted'))
	void fetchPage()
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
}
.search-input {
	max-width: 280px;
}
.search-date {
	max-width: 360px;
}

.full-width {
	width: 100%;
}

.more-arrow {
	margin-left: 2px;
}

.dialog-meta {
	margin: 0 0 10px;
	color: var(--ba-text-secondary);
	font-size: 12px;
}
.tpl-hint {
	margin: 4px 0 0;
	color: var(--ba-text-secondary);
	font-size: 12px;
}
.pre-title {
	margin: 12px 0 6px;
	font-size: 13px;
	font-weight: 600;
}
.tpl-pre {
	max-height: 320px;
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
:deep(.st-info) {
	background: rgb(59 130 246 / 12%);
	color: #2563eb;
}
</style>