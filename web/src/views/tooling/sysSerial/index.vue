<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysSerial.title') }}</h3>
				<p class="ba-sub">{{ t('sysSerial.sub') }}</p>
			</div>
			<el-button v-perm="'sysSerial/add'" type="primary" @click="openAdd">
				<el-icon><Plus /></el-icon>{{ t('common.add') }}
			</el-button>
		</div>

		<!-- 数据卡 -->
		<div class="ba-card">
			<div class="search-row">
				<el-select
					v-model="query.type"
					:placeholder="t('sysSerial.phType')"
					clearable
					class="search-select"
					@change="reload"
					@clear="reload"
				>
					<el-option v-for="item in typeOptions" :key="item.value" :label="item.text" :value="item.value" />
				</el-select>
				<el-select
					v-model="query.status"
					:placeholder="t('sysSerial.phStatus')"
					clearable
					class="search-select"
					@change="reload"
					@clear="reload"
				>
					<el-option :label="t('sysSerial.statusEnabled')" :value="0" />
					<el-option :label="t('sysSerial.statusDisabled')" :value="1" />
				</el-select>
				<el-input
					v-model="query.keyword"
					:placeholder="t('sysSerial.phKeyword')"
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
				<template #row_type="{ row }">
					<el-tag v-if="typeLabel(row.type)">{{ typeLabel(row.type) }}</el-tag>
					<span v-else>{{ row.type ?? '-' }}</span>
				</template>
				<template #row_resetInterval="{ row }">
					{{ t('sysSerial.interval.' + intervalLabel(row.resetInterval)) }}
				</template>
				<template #row_seq="{ row }">
					{{ row.seq }}
				</template>
				<template #row_status="{ row }">
					<el-switch
						v-perm="'sysSerial/setStatus'"
						:model-value="row.status"
						:active-value="0"
						:inactive-value="1"
						:disabled="statusPending.has(row.id)"
						:loading="statusPending.has(row.id)"
						@change="(v: string | number | boolean) => onToggleStatus(row, v as number)"
					/>
				</template>
				<template #row_ops="{ row }">
					<el-button v-perm="'sysSerial/update'" link type="primary" size="small" @click="openEdit(row)">
						{{ t('common.edit') }}
					</el-button>
					<el-button v-perm="'sysSerial/nextSeqNo'" link type="success" size="small" @click="onNextSeqNo(row)">
						{{ t('sysSerial.btnNextSeqNo') }}
					</el-button>
					<el-button v-perm="'sysSerial/delete'" link type="danger" size="small" @click="onDelete(row)">
						{{ t('common.delete') }}
					</el-button>
				</template>
			</vxe-grid>
		</div>

		<!-- 新增/编辑对话框 -->
		<el-dialog
			v-model="dialog.visible"
			:title="dialog.mode === 'add' ? t('common.add') : t('common.edit')"
			width="560px"
			destroy-on-close
		>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
				<el-form-item :label="t('sysSerial.labelType')" prop="type">
					<el-select v-model="form.type" :disabled="dialog.mode === 'edit'" :placeholder="t('sysSerial.phType')" class="full-width">
						<el-option v-for="item in typeOptions" :key="item.value" :label="item.text" :value="item.value" />
					</el-select>
				</el-form-item>
				<el-form-item :label="t('sysSerial.labelInterval')" prop="resetInterval">
					<el-select v-model="form.resetInterval" class="full-width">
						<el-option :label="t('sysSerial.interval.Never')" :value="0" />
						<el-option :label="t('sysSerial.interval.Day')" :value="1" />
						<el-option :label="t('sysSerial.interval.Month')" :value="2" />
						<el-option :label="t('sysSerial.interval.Year')" :value="3" />
					</el-select>
				</el-form-item>
				<el-form-item :label="t('sysSerial.labelFormater')" prop="formater">
					<div class="formater-row">
						<el-input v-model="form.formater" :placeholder="t('sysSerial.phFormater')" />
						<el-button @click="onPreview">{{ t('sysSerial.btnPreview') }}</el-button>
					</div>
					<p class="dialog-hint">{{ t('sysSerial.hintFormater', { slots: slots.join(' ') }) }}</p>
				</el-form-item>
				<el-form-item :label="t('sysSerial.labelMin')" prop="min">
					<el-input-number v-model="form.min" :min="1" :max="9999999999" class="full-width" />
				</el-form-item>
				<el-form-item :label="t('sysSerial.labelMax')" prop="max">
					<el-input-number v-model="form.max" :min="1" :max="9999999999" class="full-width" />
				</el-form-item>
				<el-form-item :label="t('sysSerial.labelOrderNo')" prop="orderNo">
					<el-input-number v-model="form.orderNo" :min="0" :max="999999" class="full-width" />
				</el-form-item>
				<el-form-item :label="t('sysSerial.labelRemark')" prop="remark">
					<el-input v-model="form.remark" type="textarea" :rows="2" :placeholder="t('sysSerial.phRemark')" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSave">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>

		<!-- 取号结果对话框(消耗序列警示) -->
		<el-dialog v-model="seqDialog.visible" :title="t('sysSerial.titleSeqResult')" width="480px">
			<el-alert
				:title="t('sysSerial.msgSeqConsumed')"
				type="warning"
				show-icon
				:closable="false"
				class="seq-alert"
			/>
			<div class="seq-row">
				<span class="seq-value">{{ seqDialog.value }}</span>
				<el-button link type="primary" @click="copySeq">{{ t('sysSerial.btnCopy') }}</el-button>
			</div>
			<template #footer>
				<el-button type="primary" @click="seqDialog.visible = false">{{ t('common.confirm') }}</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'SysSerial' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import * as serialApi from '@/api/sys/serial'
import type { SerialOutput } from '@/api/sys/serial'
import { usePaged } from '@/composables/usePaged'
import { formatDateTime } from '@/utils/format'

const { t } = useI18n()

const typeOptions = ref<Array<{ text: string; value: string }>>([])
const slots = ref<string[]>([])
/** 状态开关逐行 pending:进行中行禁用并转圈,防重复提交;失败不落库 */
const statusPending = reactive(new Set<number | string>())

type DateRange = [string, string] | null
/** 范围选择默认时刻:起 00:00:00,止 23:59:59(后端 CreateTime 闭区间) */
const defaultTime: [Date, Date] = [new Date(2000, 0, 1, 0, 0, 0), new Date(2000, 0, 1, 23, 59, 59)]

const query = reactive({
	type: null as string | null,
	status: null as number | null,
	keyword: '',
	range: null as DateRange,
	orderBy: '' as string,
	desc: false as boolean
})
// 筛选直连页面自有 query:usePaged 的 params 从不写入,旧写法 type/status/keyword 恒为 undefined(后端恒 null)
const { loading, rows, pager, fetchPage, reload, onPageChange } = usePaged<SerialOutput>(q =>
	serialApi.pageSerial({
		type: query.type,
		status: query.status,
		keyword: query.keyword || null,
		startDate: query.range?.[0] ?? null,
		endDate: query.range?.[1] ?? null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: query.orderBy || undefined,
		desc: query.orderBy ? query.desc : undefined
	})
)

function doReset(): void {
	query.type = null
	query.status = null
	query.keyword = ''
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

function typeLabel(value: string | null): string {
	const hit = typeOptions.value.find(u => u.value === value)
	return hit ? hit.text : ''
}

function intervalLabel(v: number): string {
	return v === 1 ? 'Day' : v === 2 ? 'Month' : v === 3 ? 'Year' : 'Never'
}

const columns = computed(() => [
	{ field: 'id', title: 'Id', width: 130, sortable: true },
	{ field: 'type', title: t('sysSerial.colType'), minWidth: 140, sortable: true, slots: { default: 'row_type' } },
	{ field: 'resetInterval', title: t('sysSerial.colInterval'), width: 100, sortable: true, slots: { default: 'row_resetInterval' } },
	{ field: 'formater', title: t('sysSerial.colFormater'), minWidth: 200, sortable: true, showOverflow: 'tooltip' },
	{ field: 'seq', title: t('sysSerial.colSeq'), width: 100, sortable: true, slots: { default: 'row_seq' } },
	{ field: 'min', title: t('sysSerial.colMin'), width: 90, sortable: true },
	{ field: 'max', title: t('sysSerial.colMax'), width: 110, sortable: true },
	{ field: 'expy', title: t('sysSerial.colExpy'), width: 170, sortable: true, formatter: ({ cellValue }: { cellValue: string | null }) => formatDateTime(cellValue) } as object,
	{ field: 'orderNo', title: t('sysSerial.colOrderNo'), width: 80, sortable: true },
	{ field: 'status', title: t('sysSerial.colStatus'), width: 90, sortable: true, slots: { default: 'row_status' } },
	{ field: 'remark', title: t('sysSerial.colRemark'), minWidth: 140, sortable: true, showOverflow: 'tooltip' },
	{ title: t('common.operations'), minWidth: 210, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

async function loadMeta(): Promise<void> {
	try {
		const [types, slotList] = await Promise.all([serialApi.typeListSerial(), serialApi.slotListSerial()])
		typeOptions.value = types
		slots.value = slotList
	} catch {
		/* 元数据加载失败不阻塞列表 */
	}
}

/* ── 新增/编辑 ─────────────────────────── */
const dialog = reactive({
	visible: false,
	mode: 'add' as 'add' | 'edit',
	id: 0 as number | string
})
const formRef = ref<FormInstance>()
const form = reactive({
	type: '',
	resetInterval: 1 as number,
	formater: '',
	min: 1 as number,
	max: 10000000 as number,
	orderNo: 100 as number,
	remark: '' as string
})
const rules = computed<FormRules>(() => ({
	type: [{ required: true, message: t('sysSerial.ruleType'), trigger: 'change' }],
	resetInterval: [{ required: true, message: t('sysSerial.ruleInterval'), trigger: 'change' }],
	formater: [
		{ required: true, message: t('sysSerial.ruleFormater'), trigger: 'blur' },
		{ pattern: /\{SEQ\}/, message: t('sysSerial.ruleFormaterSeq'), trigger: 'blur' }
	],
	min: [{ required: true, message: t('sysSerial.ruleMin'), trigger: 'blur' }],
	max: [{ required: true, message: t('sysSerial.ruleMax'), trigger: 'blur' }]
}))

function openAdd(): void {
	dialog.mode = 'add'
	dialog.visible = true
	Object.assign(form, {
		type: typeOptions.value[0]?.value ?? '',
		resetInterval: 1,
		formater: '',
		min: 1,
		max: 10000000,
		orderNo: 100,
		remark: ''
	})
}

function openEdit(row: SerialOutput): void {
	dialog.mode = 'edit'
	dialog.id = row.id
	dialog.visible = true
	Object.assign(form, {
		type: row.type ?? '',
		resetInterval: row.resetInterval,
		formater: row.formater ?? '',
		min: row.min,
		max: row.max,
		orderNo: row.orderNo,
		remark: row.remark ?? ''
	})
}

const saving = ref(false)

async function onSave(): Promise<void> {
	await formRef.value?.validate()
	if (form.min >= form.max) {
		ElMessage.warning(t('sysSerial.msgMinMax'))
		return
	}
	saving.value = true
	try {
		if (dialog.mode === 'add') {
			await serialApi.addSerial({
				type: form.type,
				resetInterval: form.resetInterval,
				formater: form.formater,
				min: form.min,
				max: form.max,
				orderNo: form.orderNo,
				remark: form.remark || null
			})
		} else {
			await serialApi.updateSerial({
				id: dialog.id,
				type: form.type,
				resetInterval: form.resetInterval,
				formater: form.formater,
				min: form.min,
				max: form.max,
				orderNo: form.orderNo,
				remark: form.remark || null
			})
		}
		ElMessage.success(t('common.success'))
		dialog.visible = false
		void fetchPage()
	} finally {
		saving.value = false
	}
}

/** 表达式预览(不消耗序列;取号样本用当前区间 [min, max]) */
async function onPreview(): Promise<void> {
	if (!form.formater) {
		ElMessage.warning(t('sysSerial.ruleFormater'))
		return
	}
	const value = await serialApi.previewSerial({ formater: form.formater, seq: form.min, max: form.max })
	await ElMessageBox.alert(value, t('sysSerial.titlePreview'), { confirmButtonText: t('common.confirm') })
}

/* ── 启停 ─────────────────────────── */
async function onToggleStatus(row: SerialOutput, value: number): Promise<void> {
	// 0 启用 / 1 停用:两个方向都确认(停用会拒绝该类型取号)
	const msgKey = value === 1 ? 'sysSerial.msgDisableConfirm' : 'sysSerial.msgEnableConfirm'
	try {
		await ElMessageBox.confirm(t(msgKey, { name: row.type ?? '' }), t('sysSerial.confirmTitle'), {
			type: 'warning'
		})
	} catch {
		return
	}
	statusPending.add(row.id)
	try {
		await serialApi.setSerialStatus(row.id, value)
		row.status = value
		ElMessage.success(t('common.success'))
	} catch {
		/* 失败时 switch 不更新(回滚) */
	} finally {
		statusPending.delete(row.id)
	}
}

/* ── 取号测试 ─────────────────────────── */
const seqDialog = reactive({ visible: false, value: '' })

async function onNextSeqNo(row: SerialOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('sysSerial.msgSeqConfirm', { name: row.type ?? '' }), t('sysSerial.confirmTitle'), {
			type: 'warning'
		})
	} catch {
		return
	}
	const value = await serialApi.nextSeqNo(row.type as string)
	seqDialog.value = value
	seqDialog.visible = true
	void fetchPage()
}

async function copySeq(): Promise<void> {
	try {
		await navigator.clipboard.writeText(seqDialog.value)
		ElMessage.success(t('sysSerial.msgCopied'))
	} catch {
		ElMessage.warning(t('sysSerial.msgCopyFailed'))
	}
}

/* ── 删除 ─────────────────────────── */
async function onDelete(row: SerialOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('sysSerial.msgDeleteConfirm', { name: row.type ?? '' }), t('sysSerial.confirmTitle'), {
			type: 'warning'
		})
	} catch {
		return
	}
	await serialApi.deleteSerial(row.id)
	ElMessage.success(t('common.success'))
	void fetchPage()
}

onMounted(() => {
	void loadMeta()
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
	max-width: 240px;
}
.search-select {
	width: 160px;
}
.search-date {
	max-width: 360px;
}

.full-width {
	width: 100%;
}

.formater-row {
	display: flex;
	gap: 8px;
	width: 100%;
}
.formater-row :deep(.el-input) {
	flex: 1;
}

.dialog-hint {
	font-size: 12px;
	color: var(--ba-text-tertiary);
	margin: 4px 0 0;
	line-height: 1.6;
}

.seq-alert {
	margin-bottom: 14px;
}
.seq-row {
	display: flex;
	align-items: center;
	gap: 10px;
}
.seq-value {
	flex: 1;
	font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
	font-size: 15px;
	font-weight: 600;
	background: rgb(0 0 0 / 4%);
	border-radius: 6px;
	padding: 8px 12px;
	word-break: break-all;
	user-select: all;
}
</style>
