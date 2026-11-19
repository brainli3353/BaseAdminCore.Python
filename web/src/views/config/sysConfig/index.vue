<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysConfig.title') }}</h3>
				<p class="ba-sub">{{ t('sysConfig.sub') }}</p>
			</div>
			<el-button v-perm="'sysConfig/add'" type="primary" @click="openAdd">
				<el-icon><Plus /></el-icon>{{ t('sysConfig.btnAdd') }}
			</el-button>
		</div>

		<!-- 数据卡 -->
		<div class="ba-card">
			<div class="search-row">
				<el-input
					v-model="query.name"
					:placeholder="t('sysConfig.searchNamePlaceholder')"
					clearable
					class="search-input"
					@keyup.enter="reload"
					@clear="reload"
				/>
				<el-input
					v-model="query.code"
					:placeholder="t('sysConfig.searchCodePlaceholder')"
					clearable
					class="search-input"
					@keyup.enter="reload"
					@clear="reload"
				/>
				<el-input
					v-model="query.groupCode"
					:placeholder="t('sysConfig.searchGroupPlaceholder')"
					clearable
					class="search-input"
					@keyup.enter="reload"
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
				<template #cell_sysFlag="{ row }">
					<span v-if="row.sysFlag" class="st st-super">{{ t('sysConfig.builtin') }}</span>
					<span v-else>-</span>
				</template>
				<template #cell_value="{ row }">
					<el-select
						v-if="enumOptionsOf(row).length"
						:model-value="row.value"
						size="small"
						class="quick-value-select"
						:disabled="!canUpdate || quickSavingId === row.id"
						:loading="quickSavingId === row.id"
						@change="(v: string) => onEnumChange(row, v)"
					>
						<el-option v-for="opt in enumOptionsOf(row)" :key="opt.value" :label="opt.label" :value="opt.value" />
					</el-select>
					<el-switch
						v-else-if="isBoolValue(row.value)"
						:model-value="boolValue(row.value)"
						size="small"
						:disabled="!canUpdate || quickSavingId === row.id"
						:loading="quickSavingId === row.id"
						@change="(v: string | number | boolean) => onBoolChange(row, !!v)"
					/>
					<span v-else>{{ row.value }}</span>
				</template>
				<template #row_ops="{ row }">
					<el-button v-perm="'sysConfig/update'" link type="primary" size="small" @click="openEdit(row)">
						{{ t('common.edit') }}
					</el-button>
					<el-button v-perm="'sysConfig/delete'" link type="danger" size="small" :disabled="row.sysFlag" @click="onDelete(row)">
						{{ t('common.delete') }}
					</el-button>
				</template>
			</vxe-grid>
		</div>

		<!-- 新增/编辑对话框 -->
		<el-dialog
			v-model="dialog.visible"
			:title="dialog.mode === 'add' ? t('sysConfig.btnAdd') : t('sysConfig.btnEdit')"
			width="460px"
			destroy-on-close
		>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="72px">
				<el-form-item :label="t('sysConfig.colName')" prop="name">
					<el-input v-model="form.name" :placeholder="t('sysConfig.namePlaceholder')" />
				</el-form-item>
				<el-form-item :label="t('sysConfig.colCode')" prop="code">
					<el-input v-model="form.code" :disabled="dialog.mode === 'edit'" :placeholder="t('sysConfig.codePlaceholder')" />
				</el-form-item>
				<el-form-item :label="t('sysConfig.colValue')">
					<el-input v-model="form.value" :placeholder="t('sysConfig.valuePlaceholder')" />
				</el-form-item>
				<el-form-item :label="t('sysConfig.colEnumOptions')">
					<el-input
						v-model="form.enumOptions"
						type="textarea"
						:rows="3"
						:placeholder="t('sysConfig.enumOptionsPlaceholder')"
					/>
					<div class="form-hint">{{ t('sysConfig.enumOptionsHint') }}</div>
				</el-form-item>
				<el-form-item :label="t('sysConfig.colGroup')">
					<el-input v-model="form.groupCode" :placeholder="t('sysConfig.groupPlaceholder')" />
				</el-form-item>
				<el-form-item :label="t('common.remark')">
					<el-input v-model="form.remark" :placeholder="t('sysConfig.remarkPlaceholder')" />
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
	defineOptions({ name: 'SysConfig' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import * as configApi from '@/api/sys/config'
import type { SysConfigOutput } from '@/api/sys/config'
import { usePaged } from '@/composables/usePaged'
import { useUserStore } from '@/stores/user'
import { useMenuStore } from '@/stores/menu'
import { formatDateTime } from '@/utils/format'

const { t } = useI18n()
const userStore = useUserStore()
const menuStore = useMenuStore()

/** 快捷修改与 v-perm 同口径(超管直通):无权限时值列只读展示。 */
const canUpdate = computed(() => userStore.user?.accountType === 999 || menuStore.permissions.includes('sysConfig/update'))

interface ConfigEnumOption {
	value: string
	label: string
}

/** 解析枚举选项:每行 `值|显示名`(无 `|` 时显示名=值;空行忽略)。 */
function parseEnumOptions(raw: string | null | undefined): ConfigEnumOption[] {
	if (!raw) return []
	return raw
		.split(/\r?\n/)
		.map(line => line.trim())
		.filter(Boolean)
		.map(line => {
			const idx = line.indexOf('|')
			const value = (idx < 0 ? line : line.slice(0, idx)).trim()
			const label = (idx < 0 ? line : line.slice(idx + 1)).trim()
			return { value, label: label || value }
		})
		.filter(opt => opt.value !== '')
}

function enumOptionsOf(row: SysConfigOutput): ConfigEnumOption[] {
	const opts = parseEnumOptions(row.enumOptions)
	// 仅枚举型(选项非空)才补存量值,避免把普通文本/bool 行误渲染成下拉
	if (opts.length && row.value && !opts.some(opt => opt.value === row.value)) {
		return [...opts, { value: row.value, label: row.value }]
	}
	return opts
}

/** bool 型判定:值仅为 True/False(忽略大小写与首尾空白);枚举选项非空时优先按枚举处理。 */
function isBoolValue(value: string | null | undefined): boolean {
	const v = (value ?? '').trim().toLowerCase()
	return v === 'true' || v === 'false'
}

function boolValue(value: string | null | undefined): boolean {
	return (value ?? '').trim().toLowerCase() === 'true'
}

const quickSavingId = ref<number | string | null>(null)

/** 值列快捷修改:确认 → 乐观写值 → 后端部分更新(失败回滚该行)。 */
async function quickUpdate(row: SysConfigOutput, nextValue: string, valueText: string): Promise<void> {
	try {
		await ElMessageBox.confirm(
			t('sysConfig.msgQuickUpdateConfirm', { name: row.name || row.code, value: valueText }),
			t('sysConfig.msgQuickUpdateTitle'),
			{ type: 'warning' }
		)
	} catch {
		return
	}

	const prev = row.value
	quickSavingId.value = row.id
	row.value = nextValue
	try {
		await configApi.updateConfig({ id: row.id, value: nextValue })
		ElMessage.success(t('sysConfig.msgQuickUpdated'))
	} catch {
		row.value = prev
	} finally {
		quickSavingId.value = null
	}
}

async function onBoolChange(row: SysConfigOutput, enabled: boolean): Promise<void> {
	await quickUpdate(row, enabled ? 'True' : 'False', enabled ? t('sysConfig.valueOn') : t('sysConfig.valueOff'))
}

async function onEnumChange(row: SysConfigOutput, value: string): Promise<void> {
	const label = enumOptionsOf(row).find(opt => opt.value === value)?.label ?? value
	await quickUpdate(row, value, label)
}

const query = reactive({ name: '', code: '', groupCode: '', orderBy: '' as string, desc: false as boolean })
const { loading, rows, pager, fetchPage, reload, onPageChange } = usePaged<SysConfigOutput>(q =>
	configApi.pageConfig({
		name: query.name || null,
		code: query.code || null,
		groupCode: query.groupCode || null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: query.orderBy || undefined,
		desc: query.orderBy ? query.desc : undefined
	})
)

const saving = ref(false)

function doReset(): void {
	query.name = ''
	query.code = ''
	query.groupCode = ''
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
	{ field: 'name', title: t('sysConfig.colName'), minWidth: 120, sortable: true },
	{ field: 'code', title: t('sysConfig.colCode'), minWidth: 120, sortable: true },
	{ field: 'value', title: t('sysConfig.colValue'), minWidth: 160, sortable: true, showOverflow: 'tooltip' as const, slots: { default: 'cell_value' } } as object,
	{ field: 'groupCode', title: t('sysConfig.colGroup'), minWidth: 100, sortable: true },
	// WHY 用插槽而非 formatter:formatter 返回的字符串在 vxe-table v4 按纯文本渲染,
	// 返回 HTML 会原样显示尖括号(2026-09-24 测试版实证)
	{ field: 'sysFlag', title: t('sysConfig.builtin'), width: 80, sortable: true, slots: { default: 'cell_sysFlag' } } as object,
	{ field: 'remark', title: t('common.remark'), minWidth: 140, sortable: true, showOverflow: 'tooltip' as const },
	// 时间列统一 `YYYY-MM-DD HH:mm:ss`(批 UX·F0 公共件 utils/format.ts,勿在本页另造局部函数)
	{ field: 'createTime', title: t('sysConfig.colCreateTime'), width: 170, sortable: true, formatter: ({ cellValue }: { cellValue: string | null }) => formatDateTime(cellValue) },
	{ title: t('common.operations'), width: 130, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

const dialog = reactive({ visible: false, mode: 'add' as 'add' | 'edit', id: 0 as number | string })
const formRef = ref<FormInstance>()
const form = reactive({ id: 0 as number | string, name: '', code: '', value: '', groupCode: '', remark: '', enumOptions: '' })
const rules = computed<FormRules>(() => ({
	name: [{ required: true, message: t('sysConfig.ruleNameRequired'), trigger: 'blur' }],
	code: [{ required: true, message: t('sysConfig.ruleCodeRequired'), trigger: 'blur' }]
}))

function openAdd(): void {
	dialog.mode = 'add'
	dialog.visible = true
	Object.assign(form, { id: 0, name: '', code: '', value: '', groupCode: '', remark: '', enumOptions: '' })
}

function openEdit(row: SysConfigOutput): void {
	dialog.mode = 'edit'
	dialog.id = row.id
	dialog.visible = true
	Object.assign(form, {
		id: row.id,
		name: row.name ?? '',
		code: row.code ?? '',
		value: row.value ?? '',
		groupCode: row.groupCode ?? '',
		remark: row.remark ?? '',
		enumOptions: row.enumOptions ?? ''
	})
}

async function onSave(): Promise<void> {
	await formRef.value?.validate()
	saving.value = true
	try {
		if (dialog.mode === 'add') {
			await configApi.addConfig({
				name: form.name,
				code: form.code,
				value: form.value,
				groupCode: form.groupCode || undefined,
				remark: form.remark || undefined,
				enumOptions: form.enumOptions.trim() || undefined
			})
		} else {
			await configApi.updateConfig({
				id: form.id,
				name: form.name || undefined,
				value: form.value,
				groupCode: form.groupCode,
				remark: form.remark || undefined,
				enumOptions: form.enumOptions.trim()
			})
		}
		ElMessage.success(t('common.success'))
		dialog.visible = false
		void fetchPage()
	} finally {
		saving.value = false
	}
}

async function onDelete(row: SysConfigOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('sysConfig.msgDeleteConfirm', { code: row.code }), t('sysConfig.msgDeleteTitle'), { type: 'warning' })
	} catch {
		return
	}
	await configApi.deleteConfig(row.id)
	ElMessage.success(t('sysConfig.msgDeleted'))
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
	max-width: 180px;
}
.quick-value-select {
	width: 100%;
}
.form-hint {
	margin-top: 4px;
	font-size: 12px;
	line-height: 1.5;
	color: var(--el-text-color-secondary);
}

:deep(.st) {
	display: inline-block;
	padding: 2px 8px;
	border-radius: 10px;
	font-size: 12px;
}
:deep(.st-super) {
	background: var(--ba-brand-soft);
	color: var(--ba-brand);
}
</style>
