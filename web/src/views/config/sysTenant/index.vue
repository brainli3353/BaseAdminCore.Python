<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysTenant.title') }}</h3>
				<p class="ba-sub">{{ t('sysTenant.sub') }}</p>
			</div>
			<el-button v-perm="'sysTenant/add'" type="primary" @click="openAdd">
				<el-icon><Plus /></el-icon>{{ t('sysTenant.btnAdd') }}
			</el-button>
		</div>

		<!-- 数据卡 -->
		<div class="ba-card">
			<div class="search-row">
				<el-input
					v-model="query.name"
					:placeholder="t('sysTenant.searchPlaceholder')"
					clearable
					class="search-input"
					@keyup.enter="reload"
					@clear="reload"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
				<el-select v-model="query.status" :placeholder="t('common.phStatus')" class="search-status" @change="reload">
					<el-option :label="t('common.all')" :value="OPT_ALL" />
					<el-option :label="t('sysTenant.statusEnabled')" :value="0" />
					<el-option :label="t('sysTenant.statusDisabled')" :value="1" />
				</el-select>
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
				<template #cell_status="{ row }">
					<span class="st" :class="row.status === 0 ? 'st-ok' : 'st-off'">
						{{ row.status === 0 ? t('sysTenant.statusEnabled') : t('sysTenant.statusDisabled') }}
					</span>
				</template>
				<template #cell_db="{ row }">
					{{ row.hasConnection === true ? row.dbName || t('sysTenant.dbStandalone') : t('sysTenant.dbPrimary') }}
				</template>
				<template #row_ops="{ row }">
					<el-button v-perm="'sysTenant/update'" link type="primary" size="small" @click="openEdit(row)">
						{{ t('common.edit') }}
					</el-button>
					<el-button
						v-perm="'sysTenant/initDb'"
						link
						type="primary"
						size="small"
						:loading="rowLoading(row, 'initDb')"
						:disabled="rowBusy(row)"
						@click="onInitDb(row)"
					>
						{{ t('sysTenant.btnInitDb') }}
					</el-button>
					<el-button
						v-perm="'sysTenant/setStatus'"
						link
						:type="row.status === 0 ? 'warning' : 'success'"
						size="small"
						:loading="rowLoading(row, 'status')"
						:disabled="rowBusy(row)"
						@click="onSetStatus(row)"
					>
						{{ row.status === 0 ? t('sysTenant.statusDisabled') : t('sysTenant.statusEnabled') }}
					</el-button>
					<el-button
						v-perm="'sysTenant/delete'"
						link
						type="danger"
						size="small"
						:loading="rowLoading(row, 'delete')"
						:disabled="rowBusy(row)"
						@click="onDelete(row)"
					>
						{{ t('common.delete') }}
					</el-button>
				</template>
			</vxe-grid>
		</div>

		<!-- 新增/编辑对话框 -->
		<el-dialog
			v-model="dialog.visible"
			:title="dialog.mode === 'add' ? t('sysTenant.dlgAdd') : t('sysTenant.dlgEdit')"
			width="460px"
			destroy-on-close
		>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="84px">
				<el-form-item :label="t('sysTenant.labelName')" prop="name">
					<el-input v-model="form.name" :placeholder="t('sysTenant.phName')" />
				</el-form-item>
				<el-form-item :label="t('sysTenant.labelPlan')">
					<el-input v-model="form.plan" :placeholder="t('sysTenant.phPlan')" />
				</el-form-item>
				<el-form-item :label="t('sysTenant.labelExpiration')">
					<el-date-picker
						v-model="form.expirationTime"
						type="datetime"
						value-format="YYYY-MM-DD HH:mm:ss"
						:placeholder="t('sysTenant.phExpiration')"
						clearable
						class="full-width"
					/>
				</el-form-item>
				<el-form-item :label="t('sysTenant.labelSort')">
					<el-input-number v-model="form.orderNo" :min="0" :max="9999" />
				</el-form-item>
				<el-form-item :label="t('common.remark')">
					<el-input v-model="form.remark" :placeholder="t('sysTenant.phOptional')" />
				</el-form-item>
				<el-form-item :label="t('sysTenant.labelConnection')">
					<el-input
						v-model="form.connection"
						:placeholder="t('sysTenant.phConnection')"
					/>
				</el-form-item>
				<el-form-item :label="t('sysTenant.labelDbName')">
					<el-input v-model="form.dbName" :placeholder="t('sysTenant.phDbName')" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSave">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
/** 「全部」哨兵：该查询条件为 null ＝ 不带此筛选（业务语义，运行时必须保持 null）。
 *  批 B6：EP 按需后 `el-option.value` 的 prop 类型不再含 null ⇒ 只收口类型、不改值（改成 '' 会让"全部"变成"按空串筛选"）。 */
const OPT_ALL = null as unknown as string | number
	defineOptions({ name: 'SysTenant' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import * as tenantApi from '@/api/sys/tenant'
import type { TenantOutput } from '@/api/sys/tenant'
import { usePaged } from '@/composables/usePaged'
import { formatDateTime } from '@/utils/format'

const { t } = useI18n()

type DateRange = [string, string] | null
/** 范围选择默认时刻:起 00:00:00,止 23:59:59(后端 CreateTime 闭区间) */
const defaultTime: [Date, Date] = [new Date(2000, 0, 1, 0, 0, 0), new Date(2000, 0, 1, 23, 59, 59)]

const query = reactive({
	name: '',
	status: null as number | null,
	range: null as DateRange,
	orderBy: '' as string,
	desc: false as boolean
})
const { loading, rows, pager, fetchPage, reload, onPageChange } = usePaged<TenantOutput>(q =>
	tenantApi.pageTenant({
		name: query.name || null,
		status: query.status,
		startDate: query.range?.[0] ?? null,
		endDate: query.range?.[1] ?? null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: query.orderBy || undefined,
		desc: query.orderBy ? query.desc : undefined
	})
)

const saving = ref(false)

/** 行级 pending:同一行任一操作进行中即禁用该行全部按钮(initDb 连点=并发建表风险)。 */
const pendingRow = ref<number | string | null>(null)
const pendingAction = ref<'' | 'status' | 'initDb' | 'delete'>('')

function rowBusy(row: TenantOutput): boolean {
	return pendingRow.value === row.id
}

function rowLoading(row: TenantOutput, action: 'status' | 'initDb' | 'delete'): boolean {
	return pendingRow.value === row.id && pendingAction.value === action
}

/** 行级操作统一包裹:置 pending → 执行 → 复位(异常由全局拦截器提示) */
async function withRowPending(
	row: TenantOutput,
	action: 'status' | 'initDb' | 'delete',
	fn: () => Promise<void>
): Promise<void> {
	if (rowBusy(row)) {
		return
	}
	pendingRow.value = row.id
	pendingAction.value = action
	try {
		await fn()
	} finally {
		pendingRow.value = null
		pendingAction.value = ''
	}
}

function doReset(): void {
	query.name = ''
	query.status = null
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

const columns = computed(() => [
	{ field: 'id', title: 'Id', width: 130, sortable: true },
	{ field: 'name', title: t('sysTenant.colName'), minWidth: 140, sortable: true, showOverflow: 'tooltip' },
	{ field: 'plan', title: t('sysTenant.colPlan'), minWidth: 100, sortable: true, showOverflow: 'tooltip' },
	// 用插槽渲染(与下方状态列同理):按 hasConnection 决定显示独立库名还是「主库」
	{ field: 'dbName', title: t('sysTenant.colDb'), minWidth: 110, sortable: true, showOverflow: 'tooltip', slots: { default: 'cell_db' } } as object,
	// WHY 用插槽而非 formatter:formatter 返回的字符串在 vxe-table v4 按纯文本渲染,
	// 返回 HTML 会原样显示尖括号(2026-09-24 测试版实证)
	{ field: 'status', title: t('common.status'), width: 90, sortable: true, slots: { default: 'cell_status' } } as object,
	{
		field: 'expirationTime',
		title: t('sysTenant.colExpiration'),
		width: 170,
		sortable: true,
		// 空值仍显示「永久」(业务语义),有值统一 YYYY-MM-DD HH:mm:ss(批 UX·F0 公共口径)
		formatter: ({ cellValue }: { cellValue: string | null }) =>
			cellValue ? formatDateTime(cellValue) : t('sysTenant.permanent')
	} as object,
	{ field: 'orderNo', title: t('sysTenant.colSort'), width: 80, sortable: true },
	{ field: 'remark', title: t('common.remark'), minWidth: 140, sortable: true, showOverflow: 'tooltip' },
	{ title: t('common.operations'), minWidth: 180, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

const dialog = reactive({ visible: false, mode: 'add' as 'add' | 'edit', id: 0 as number | string })
const formRef = ref<FormInstance>()
const form = reactive({
	id: 0 as number | string,
	name: '',
	plan: '',
	expirationTime: null as string | null,
	orderNo: 0,
	remark: '',
	/** 租户独立库连接串(安全红线:编辑时恒为空,绝不回显) */
	connection: '',
	/** 库名(展示用) */
	dbName: ''
})
const rules = computed<FormRules>(() => ({
	name: [{ required: true, message: t('sysTenant.ruleNameRequired'), trigger: 'blur' }]
}))

function openAdd(): void {
	dialog.mode = 'add'
	dialog.visible = true
	Object.assign(form, { id: 0, name: '', plan: '', expirationTime: null, orderNo: 0, remark: '', connection: '', dbName: '' })
}

function openEdit(row: TenantOutput): void {
	dialog.mode = 'edit'
	dialog.id = row.id
	dialog.visible = true
	Object.assign(form, {
		id: row.id,
		name: row.name ?? '',
		plan: row.plan ?? '',
		expirationTime: row.expirationTime,
		orderNo: row.orderNo,
		remark: row.remark ?? '',
		// 安全红线:连接串后端不返回,恒置空,只有用户实际填写才提交
		connection: '',
		dbName: row.dbName ?? ''
	})
}

async function onSave(): Promise<void> {
	await formRef.value?.validate()
	saving.value = true
	try {
		if (dialog.mode === 'add') {
			await tenantApi.addTenant({
				name: form.name,
				plan: form.plan || undefined,
				expirationTime: form.expirationTime || null,
				orderNo: form.orderNo,
				remark: form.remark || undefined,
				connection: form.connection || undefined,
				dbName: form.dbName || undefined
			})
		} else {
			await tenantApi.updateTenant({
				id: form.id,
				name: form.name || undefined,
				plan: form.plan || undefined,
				expirationTime: form.expirationTime || null,
				orderNo: form.orderNo,
				remark: form.remark || undefined,
				connection: form.connection || undefined,
				dbName: form.dbName || undefined
			})
		}
		ElMessage.success(t('sysTenant.msgSaved'))
		dialog.visible = false
		void fetchPage()
	} finally {
		saving.value = false
	}
}

async function onSetStatus(row: TenantOutput): Promise<void> {
	await withRowPending(row, 'status', async () => {
		const toDisable = row.status === 0
		const msg = toDisable
			? t('sysTenant.msgDisableConfirm', { name: row.name })
			: t('sysTenant.msgEnableConfirm', { name: row.name })
		try {
			await ElMessageBox.confirm(msg, toDisable ? t('sysTenant.msgDisableTitle') : t('sysTenant.msgEnableTitle'), { type: 'warning' })
		} catch {
			return
		}
		await tenantApi.setTenantStatus(row.id, toDisable ? 1 : 0)
		ElMessage.success(toDisable ? t('sysTenant.msgDisabled') : t('sysTenant.msgEnabled'))
		void fetchPage()
	})
}

/** 初始化租户独立库:在该租户独立库上建表/初始化数据(失败由全局拦截器提示)。 */
async function onInitDb(row: TenantOutput): Promise<void> {
	await withRowPending(row, 'initDb', async () => {
		const msg = t('sysTenant.msgInitConfirm', { name: row.name })
		try {
			await ElMessageBox.confirm(msg, t('sysTenant.msgInitTitle'), { type: 'warning' })
		} catch {
			return
		}
		const res = await tenantApi.initTenantDb(row.id)
		ElMessage.success(t('sysTenant.msgInitDone', { count: res.tableCount }))
		void fetchPage()
	})
}

async function onDelete(row: TenantOutput): Promise<void> {
	await withRowPending(row, 'delete', async () => {
		try {
			await ElMessageBox.confirm(t('sysTenant.msgDeleteConfirm', { name: row.name }), t('sysTenant.msgDeleteTitle'), { type: 'warning' })
		} catch {
			return
		}
		await tenantApi.deleteTenant(row.id)
		ElMessage.success(t('sysTenant.msgDeleted'))
		void fetchPage()
	})
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
.search-status {
	width: 130px;
}
.search-date {
	max-width: 360px;
}

.full-width {
	width: 100%;
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
</style>