<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysOrg.title') }}</h3>
				<p class="ba-sub">{{ t('sysOrg.sub') }}</p>
			</div>
			<el-button v-perm="'sysOrg/add'" type="primary" @click="openAdd(selectedOrg)">
				<el-icon><Plus /></el-icon>{{ t('sysOrg.btnAdd') }}
			</el-button>
		</div>

		<!-- 数据卡 -->
		<div class="ba-card">
			<p class="table-hint">{{ t('sysOrg.tableHint') }}</p>
			<div class="search-row">
				<el-input
					v-model="filterKeyword"
					:placeholder="t('sysOrg.filterPlaceholder')"
					clearable
					class="search-input"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
			</div>
			<p class="org-selected">
				{{ selectedOrg ? t('sysOrg.currentOrg', { name: selectedOrg.name }) : t('sysOrg.selectOrgHint') }}
			</p>
			<vxe-grid
				:loading="loading"
				:data="filteredRows"
				:columns="columns"
				:row-config="{ keyField: 'id' }"
				:tree-config="{ rowField: 'id', expandAll: true }"
				:radio-config="{ highlight: true }"
				@cell-click="onRowClick"
			>
				<template #cell_status="{ row }">
					<span class="st" :class="row.status === 0 ? 'st-ok' : 'st-off'">
						{{ row.status === 0 ? t('sysOrg.statusNormal') : t('sysOrg.statusDisabled') }}
					</span>
				</template>
				<template #row_ops="{ row }">
					<el-button v-perm="'sysOrg/add'" link type="primary" size="small" @click.stop="openAdd(row)">
						{{ t('sysOrg.btnAddChild') }}
					</el-button>
					<el-button v-perm="'sysOrg/update'" link type="primary" size="small" :disabled="row.disabled" @click.stop="openEdit(row)">
						{{ t('common.edit') }}
					</el-button>
					<el-button v-perm="'sysOrg/delete'" link type="danger" size="small" :disabled="row.disabled" @click.stop="onDelete(row)">
						{{ t('common.delete') }}
					</el-button>
				</template>
			</vxe-grid>
		</div>

		<!-- 新增/编辑对话框 -->
		<el-dialog
			v-model="dialog.visible"
			:title="dialog.mode === 'add' ? t('sysOrg.btnAdd') : t('sysOrg.btnEdit')"
			width="460px"
			destroy-on-close
		>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="72px">
				<el-form-item :label="t('sysOrg.parentOrg')">
					<el-input :model-value="dialog.pidLabel" disabled />
				</el-form-item>
				<el-form-item :label="t('sysOrg.colName')" prop="name">
					<el-input v-model="form.name" :placeholder="t('sysOrg.namePlaceholder')" />
				</el-form-item>
				<el-form-item :label="t('sysOrg.colCode')">
					<el-input v-model="form.code" :placeholder="t('sysOrg.codePlaceholder')" />
				</el-form-item>
				<el-form-item :label="t('sysOrg.colSort')">
					<el-input-number v-model="form.sort" :min="0" :max="9999" />
				</el-form-item>
				<el-form-item :label="t('common.status')">
					<el-radio-group v-model="form.status">
						<el-radio :value="0">{{ t('sysOrg.statusNormal') }}</el-radio>
						<el-radio :value="1">{{ t('sysOrg.statusDisabled') }}</el-radio>
					</el-radio-group>
				</el-form-item>
				<el-form-item :label="t('common.remark')">
					<el-input v-model="form.remark" :placeholder="t('sysOrg.remarkPlaceholder')" />
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
	defineOptions({ name: 'SysOrg' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import * as orgApi from '@/api/sys/org'
import type { OrgOutput } from '@/api/sys/org'

const { t } = useI18n()
const loading = ref(false)
const saving = ref(false)
const rows = ref<OrgOutput[]>([])
const selectedOrg = ref<OrgOutput | null>(null)

/* ── 前端过滤(树已全量加载:名称/编码子串匹配;命中自身保留整棵子树) ── */
const filterKeyword = ref('')

function filterOrgs(nodes: OrgOutput[], keyword: string): OrgOutput[] {
	const out: OrgOutput[] = []
	for (const n of nodes) {
		const children = filterOrgs(n.children ?? [], keyword)
		const selfOk = !keyword || (n.name ?? '').toLowerCase().includes(keyword) || (n.code ?? '').toLowerCase().includes(keyword)
		if (selfOk || children.length > 0) {
			out.push({ ...n, children: selfOk ? n.children : children })
		}
	}
	return out
}

const filteredRows = computed(() => filterOrgs(rows.value, filterKeyword.value.trim().toLowerCase()))

const columns = computed(() => [
	{ field: 'name', title: t('sysOrg.colName'), minWidth: 200, treeNode: true, showOverflow: 'tooltip' as const },
	{ field: 'code', title: t('sysOrg.colCode'), minWidth: 120, showOverflow: 'tooltip' as const },
	{ field: 'sort', title: t('sysOrg.colSort'), width: 80 },
	{ field: 'remark', title: t('common.remark'), minWidth: 160, showOverflow: 'tooltip' as const },
	// WHY 用插槽而非 formatter:formatter 返回的字符串在 vxe-table v4 按纯文本渲染,
	// 返回 HTML 会原样显示尖括号(2026-09-24 测试版实证)
	{ field: 'status', title: t('common.status'), width: 90, slots: { default: 'cell_status' } } as object,
	{ title: t('common.operations'), minWidth: 180, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

async function fetchData(): Promise<void> {
	loading.value = true
	try {
		rows.value = await orgApi.getOrgTree()
	} finally {
		loading.value = false
	}
}

function onRowClick({ row }: { row: OrgOutput }): void {
	selectedOrg.value = row
}

/* ── 新增/编辑 ─────────────────────────────── */
const dialog = reactive({ visible: false, mode: 'add' as 'add' | 'edit', id: 0 as number | string, pid: 0 as number | string, pidLabel: t('sysOrg.topLevel') })
const formRef = ref<FormInstance>()
const form = reactive({ name: '', code: '', sort: 0, remark: '', status: 0 })
const rules = computed<FormRules>(() => ({
	name: [{ required: true, message: t('sysOrg.ruleNameRequired'), trigger: 'blur' }]
}))

function openAdd(parent: OrgOutput | null): void {
	dialog.mode = 'add'
	dialog.id = 0
	dialog.pid = parent ? parent.id : 0
	dialog.pidLabel = parent ? parent.name ?? '' : t('sysOrg.topLevel')
	dialog.visible = true
	Object.assign(form, { name: '', code: '', sort: 0, remark: '', status: 0 })
}

function findOrgName(id: number | string, nodes: OrgOutput[] = rows.value): string | null {
	for (const n of nodes) {
		if (String(n.id) === String(id)) return n.name
		const hit = findOrgName(id, n.children ?? [])
		if (hit !== null) return hit
	}
	return null
}

function openEdit(row: OrgOutput): void {
	dialog.mode = 'edit'
	dialog.id = row.id
	dialog.pid = row.pid
	// 父级回显父机构名;树中找不到(如被过滤/越权范围外)回落 #id
	dialog.pidLabel = String(row.pid) === '0' ? t('sysOrg.topLevel') : findOrgName(row.pid) ?? `#${row.pid}`
	dialog.visible = true
	Object.assign(form, { name: row.name ?? '', code: row.code ?? '', sort: row.sort, remark: row.remark ?? '', status: row.status })
}

async function onSave(): Promise<void> {
	await formRef.value?.validate()
	saving.value = true
	try {
		if (dialog.mode === 'add') {
			await orgApi.addOrg({
				pid: dialog.pid,
				name: form.name,
				code: form.code || undefined,
				sort: form.sort,
				remark: form.remark || undefined,
				status: form.status
			})
		} else {
			await orgApi.updateOrg({
				id: dialog.id,
				pid: dialog.pid,
				name: form.name,
				code: form.code || undefined,
				sort: form.sort,
				remark: form.remark || undefined,
				status: form.status
			})
		}
		ElMessage.success(t('common.success'))
		dialog.visible = false
		void fetchData()
	} finally {
		saving.value = false
	}
}

async function onDelete(row: OrgOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('sysOrg.msgDeleteConfirm', { name: row.name }), t('sysOrg.msgDeleteTitle'), {
			type: 'warning'
		})
	} catch {
		return
	}
	await orgApi.deleteOrg(row.id)
	ElMessage.success(t('sysOrg.msgDeleted'))
	if (selectedOrg.value?.id === row.id) {
		selectedOrg.value = null
	}
	void fetchData()
}

onMounted(() => {
	void fetchData()
})
</script>

<style scoped>
.table-hint {
	font-size: 12px;
	color: var(--ba-text-tertiary);
	margin: 0 0 10px;
}

.search-row {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 10px;
}
.search-input {
	max-width: 280px;
}

/* 选中机构提示条(参照 sysDict 的 currentType 提示写法,非 radio 控件) */
.org-selected {
	display: inline-block;
	font-size: 12px;
	line-height: 1.5;
	color: var(--ba-brand);
	background: var(--ba-brand-soft);
	border-radius: 10px;
	padding: 2px 10px;
	margin: 0 0 10px;
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