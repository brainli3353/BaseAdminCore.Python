<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysPos.title') }}</h3>
				<p class="ba-sub">{{ t('sysPos.sub') }}</p>
			</div>
			<el-button v-perm="'sysPos/import'" :loading="importing" @click="onImportClick">
				<el-icon><Upload /></el-icon>{{ t('sysPos.btnImport') }}
			</el-button>
			<el-button v-perm="'sysPos/add'" type="primary" @click="openAdd">
				<el-icon><Plus /></el-icon>{{ t('sysPos.btnAdd') }}
			</el-button>
		</div>

		<!-- 数据卡 -->
		<div class="ba-card">
			<div class="search-row">
				<el-input
					v-model="query.name"
					:placeholder="t('sysPos.searchPlaceholder')"
					clearable
					class="search-input"
					@keyup.enter="reload"
					@clear="reload"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
				<el-select v-model="query.status" :placeholder="t('common.phStatus')" class="search-status" @change="reload">
					<el-option :label="t('common.all')" :value="OPT_ALL" />
					<el-option :label="t('sysPos.statusNormal')" :value="0" />
					<el-option :label="t('sysPos.statusDisabled')" :value="1" />
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
				<template #cell_status="{ row }">
					<span class="st" :class="row.status === 0 ? 'st-ok' : 'st-off'">
						{{ row.status === 0 ? t('sysPos.statusNormal') : t('sysPos.statusDisabled') }}
					</span>
				</template>
				<template #row_ops="{ row }">
					<el-button v-perm="'sysPos/update'" link type="primary" size="small" @click="openEdit(row)">
						{{ t('common.edit') }}
					</el-button>
					<el-button v-perm="'sysPos/delete'" link type="danger" size="small" @click="onDelete(row)">
						{{ t('common.delete') }}
					</el-button>
				</template>
			</vxe-grid>
		</div>

		<!-- 新增/编辑对话框 -->
		<el-dialog
			v-model="dialog.visible"
			:title="dialog.mode === 'add' ? t('sysPos.btnAdd') : t('sysPos.btnEdit')"
			width="460px"
			destroy-on-close
		>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="72px">
				<el-form-item :label="t('sysPos.colName')" prop="name">
					<el-input v-model="form.name" :placeholder="t('sysPos.namePlaceholder')" />
				</el-form-item>
				<el-form-item :label="t('sysPos.colCode')">
					<el-input v-model="form.code" :placeholder="t('sysPos.codePlaceholder')" />
				</el-form-item>
				<el-form-item :label="t('sysPos.colSort')">
					<el-input-number v-model="form.sort" :min="0" :max="9999" />
				</el-form-item>
				<el-form-item :label="t('common.status')">
					<el-radio-group v-model="form.status">
						<el-radio :value="0">{{ t('sysPos.statusNormal') }}</el-radio>
						<el-radio :value="1">{{ t('sysPos.statusDisabled') }}</el-radio>
					</el-radio-group>
				</el-form-item>
				<el-form-item :label="t('common.remark')">
					<el-input v-model="form.remark" :placeholder="t('sysPos.remarkPlaceholder')" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSave">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>

		<!-- 导入错误回显(行级错误走 200+data,非异常) -->
		<el-dialog v-model="importDialog.visible" :title="t('sysPos.importErrorTitle')" width="640px">
			<el-alert
				v-if="importDialog.truncated"
				:title="t('sysPos.importTruncated')"
				type="warning"
				:closable="false"
				show-icon
				class="import-alert"
			/>
			<el-table :data="importDialog.errors" max-height="320" border size="small">
				<el-table-column prop="row" :label="t('sysPos.importColRow')" width="90" />
				<el-table-column prop="field" :label="t('sysPos.importColField')" width="150" />
				<el-table-column prop="reason" :label="t('sysPos.importColReason')" />
			</el-table>
			<template #footer>
				<el-button type="primary" @click="importDialog.visible = false">{{ t('common.confirm') }}</el-button>
			</template>
		</el-dialog>

		<!-- 隐藏文件选择器(手动触发,accept 限定可导入格式) -->
		<input ref="fileInputRef" type="file" accept=".xlsx,.csv" hidden @change="onFileChange" />
	</div>
</template>

<script setup lang="ts">
/** 「全部」哨兵：该查询条件为 null ＝ 不带此筛选（业务语义，运行时必须保持 null）。
 *  批 B6：EP 按需后 `el-option.value` 的 prop 类型不再含 null ⇒ 只收口类型、不改值（改成 '' 会让"全部"变成"按空串筛选"）。 */
const OPT_ALL = null as unknown as string | number
	defineOptions({ name: 'SysPos' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, Upload } from '@element-plus/icons-vue'
import * as posApi from '@/api/sys/pos'
import type { PosOutput } from '@/api/sys/pos'
import { usePaged } from '@/composables/usePaged'

const { t } = useI18n()
const query = reactive({ name: '', status: null as number | null, orderBy: '' as string, desc: false as boolean })
const { loading, rows, pager, fetchPage, reload, onPageChange } = usePaged<PosOutput>(q =>
	posApi.pagePos({
		name: query.name || null,
		status: query.status,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: query.orderBy || undefined,
		desc: query.orderBy ? query.desc : undefined
	})
)

const saving = ref(false)

function doReset(): void {
	query.name = ''
	query.status = null
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
	{ field: 'name', title: t('sysPos.colName'), minWidth: 140, sortable: true, showOverflow: 'tooltip' as const },
	{ field: 'code', title: t('sysPos.colCode'), minWidth: 120, sortable: true, showOverflow: 'tooltip' as const },
	{ field: 'sort', title: t('sysPos.colSort'), width: 80, sortable: true },
	// WHY 用插槽而非 formatter:formatter 返回的字符串在 vxe-table v4 按纯文本渲染,
	// 返回 HTML 会原样显示尖括号(2026-09-24 测试版实证)
	{ field: 'status', title: t('common.status'), width: 90, sortable: true, slots: { default: 'cell_status' } } as object,
	{ field: 'remark', title: t('common.remark'), minWidth: 160, sortable: true, showOverflow: 'tooltip' as const },
	{ title: t('common.operations'), width: 130, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

const dialog = reactive({ visible: false, mode: 'add' as 'add' | 'edit', id: 0 as number | string })
const formRef = ref<FormInstance>()
const form = reactive({ id: 0 as number | string, name: '', code: '', sort: 0, status: 0, remark: '' })
const rules = computed<FormRules>(() => ({
	name: [{ required: true, message: t('sysPos.ruleNameRequired'), trigger: 'blur' }],
	// 批 BK:服务层 Code 非空校验(PosNameCodeRequired)前端同口径,避免空 Code 必撞 400
	code: [{ required: true, message: t('sysPos.ruleCodeRequired'), trigger: 'blur' }]
}))

function openAdd(): void {
	dialog.mode = 'add'
	dialog.visible = true
	Object.assign(form, { id: 0, name: '', code: '', sort: 0, status: 0, remark: '' })
}

function openEdit(row: PosOutput): void {
	dialog.mode = 'edit'
	dialog.id = row.id
	dialog.visible = true
	Object.assign(form, {
		id: row.id,
		name: row.name ?? '',
		code: row.code ?? '',
		sort: row.sort,
		status: row.status,
		remark: row.remark ?? ''
	})
}

async function onSave(): Promise<void> {
	await formRef.value?.validate()
	saving.value = true
	try {
		const payload = {
			name: form.name,
			code: form.code || undefined,
			sort: form.sort,
			status: form.status,
			remark: form.remark || undefined
		}
		if (dialog.mode === 'add') {
			await posApi.addPos(payload)
		} else {
			await posApi.updatePos({ id: form.id, ...payload })
		}
		ElMessage.success(t('common.success'))
		dialog.visible = false
		void fetchPage()
	} finally {
		saving.value = false
	}
}

async function onDelete(row: PosOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('sysPos.msgDeleteConfirm', { name: row.name }), t('sysPos.msgDeleteTitle'), {
			type: 'warning'
		})
	} catch {
		return
	}
	await posApi.deletePos(row.id)
	ElMessage.success(t('sysPos.msgDeleted'))
	void fetchPage()
}

/** 导入(契约 /api/sysPos/import):行级错误走 200+data;文件级错误由全局拦截器弹窗,此处不特殊处理。 */
const fileInputRef = ref<HTMLInputElement>()
const importing = ref(false)
const importDialog = reactive({
	visible: false,
	truncated: false,
	errors: [] as posApi.ImportRowError[]
})

function onImportClick(): void {
	fileInputRef.value?.click()
}

async function onFileChange(e: Event): Promise<void> {
	const input = e.target as HTMLInputElement
	const file = input.files?.[0]
	// 清空 value 以允许连续选择同一文件
	input.value = ''
	if (!file) {
		return
	}
	importing.value = true
	try {
		const res = await posApi.importPos(file)
		if (res.errors.length > 0) {
			importDialog.errors = res.errors
			importDialog.truncated = res.truncated
			importDialog.visible = true
		}
		if (res.imported > 0) {
			ElMessage.success(t('sysPos.msgImported', { count: res.imported }))
			void fetchPage()
		}
	} finally {
		importing.value = false
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
}
.search-input {
	max-width: 280px;
}
.search-status {
	width: 130px;
}
.import-alert {
	margin-bottom: 12px;
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
