<template>
	<div class="ba-page">
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('menuAdmin.title') }}</h3>
				<p class="ba-sub">{{ t('menuAdmin.sub') }}</p>
			</div>
			<el-button v-perm="'sysMenu/add'" type="primary" @click="openAdd(null)">
				<el-icon><Plus /></el-icon>{{ t('menuAdmin.btnAddTop') }}
			</el-button>
		</div>

		<div class="ba-card">
			<div class="search-row">
				<el-input
					v-model="filter.keyword"
					:placeholder="t('menuAdmin.filterKeywordPlaceholder')"
					clearable
					class="search-input"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
				<el-select v-model="filter.status" :placeholder="t('menuAdmin.filterStatusPlaceholder')" class="status-select">
					<el-option :value="''" :label="t('menuAdmin.filterStatusPlaceholder')" />
					<el-option :value="0" :label="t('menuAdmin.statusEnabled')" />
					<el-option :value="1" :label="t('menuAdmin.statusDisabled')" />
				</el-select>
			</div>
			<vxe-grid
				:loading="loading"
				:data="filteredTree"
				:columns="columns"
				:tree-config="{ rowField: 'id', expandAll: true, reserve: true }"
				:row-config="{ keyField: 'id' }"
			>
				<template #cell_type="{ row }">
					<span class="mt" :class="row.type === 1 ? 'mt-dir' : row.type === 2 ? 'mt-menu' : 'mt-btn'">
						{{ row.type === 1 ? t('menuAdmin.typeDirectory') : row.type === 2 ? t('menuAdmin.typeMenu') : t('menuAdmin.typeButton') }}
					</span>
				</template>
				<template #cell_status="{ row }">
					<el-switch
						v-perm="'sysMenu/setStatus'"
						:model-value="row.status === 0"
						@change="(v: string | number | boolean) => onToggleStatus(row, v === true)"
					/>
				</template>
				<template #cell_keepAlive="{ row }">
					<el-tag :type="row.isKeepAlive === 0 ? 'info' : 'success'" size="small">
						{{ row.isKeepAlive === 0 ? t('common.no') : t('common.yes') }}
					</el-tag>
				</template>
				<template #row_ops="{ row }">
					<el-button v-perm="'sysMenu/add'" link type="primary" size="small" @click="openAdd(row)">
						{{ t('menuAdmin.btnChild') }}
					</el-button>
					<el-button v-perm="'sysMenu/update'" link type="primary" size="small" @click="openEdit(row)">
						{{ t('common.edit') }}
					</el-button>
					<el-button v-perm="'sysMenu/delete'" link type="danger" size="small" @click="onDelete(row)">
						{{ t('common.delete') }}
					</el-button>
				</template>
			</vxe-grid>
		</div>

		<!-- 新增/编辑 -->
		<el-dialog v-model="dialog.visible" :title="dialog.mode === 'add' ? t('menuAdmin.dlgAdd') : t('menuAdmin.dlgEdit')" width="500px" destroy-on-close>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="84px">
				<el-form-item :label="t('menuAdmin.labelParent')">
					<el-input :model-value="parentLabel" disabled />
				</el-form-item>
				<el-form-item :label="t('menuAdmin.labelType')" prop="type">
					<el-radio-group v-model="form.type">
						<el-radio :value="1">{{ t('menuAdmin.typeDirectory') }}</el-radio>
						<el-radio :value="2">{{ t('menuAdmin.typeMenu') }}</el-radio>
						<el-radio :value="3">{{ t('menuAdmin.typeButton') }}</el-radio>
					</el-radio-group>
				</el-form-item>
				<el-form-item :label="t('menuAdmin.labelName')" prop="name">
					<el-input v-model="form.name" :placeholder="t('menuAdmin.placeholderName')" />
				</el-form-item>
				<el-form-item :label="t('menuAdmin.labelTitle')" prop="title">
					<el-input v-model="form.title" :placeholder="t('menuAdmin.placeholderTitle')" />
				</el-form-item>
				<el-form-item v-if="form.type === 3" :label="t('menuAdmin.labelPermission')" prop="permission">
					<el-input v-model="form.permission" :placeholder="t('menuAdmin.placeholderPermission')" />
				</el-form-item>
				<el-form-item v-if="form.type !== 3" :label="t('menuAdmin.labelIcon')">
					<el-input v-model="form.icon" :placeholder="t('menuAdmin.placeholderIcon')" />
				</el-form-item>
				<el-form-item :label="t('menuAdmin.labelSort')" prop="orderNo">
					<el-input-number v-model="form.orderNo" :min="0" :max="9999" />
				</el-form-item>
				<el-form-item v-if="form.type !== 3" :label="t('menuAdmin.labelKeepAlive')">
					<el-radio-group v-model="form.isKeepAlive">
						<el-radio :value="1">{{ t('menuAdmin.keepAliveYes') }}</el-radio>
						<el-radio :value="0">{{ t('menuAdmin.keepAliveNo') }}</el-radio>
					</el-radio-group>
					<div class="form-tip">{{ t('menuAdmin.keepAliveTip') }}</div>
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
	defineOptions({ name: 'Menu' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import * as menuAdminApi from '@/api/sys/menuAdmin'
import type { MenuNode } from '@/types/api'

const { t } = useI18n()
const loading = ref(false)
const tree = ref<MenuNode[]>([])

/* ── 前端过滤(树已全量加载:关键字命中 title/name/permission,状态精确匹配) ── */
const filter = reactive({ keyword: '', status: '' as '' | number })

function nodeMatched(n: MenuNode, keyword: string): boolean {
	const statusOk = filter.status === '' || n.status === filter.status
	if (!statusOk) return false
	if (!keyword) return true
	return [n.title, n.name, n.permission].some(v => (v ?? '').toLowerCase().includes(keyword))
}

/** 命中自身则整棵子树保留;否则父节点仅在存在命中后代时保留。 */
function filterNodes(nodes: MenuNode[], keyword: string): MenuNode[] {
	const out: MenuNode[] = []
	for (const n of nodes) {
		const children = filterNodes(n.children ?? [], keyword)
		const selfOk = nodeMatched(n, keyword)
		if (selfOk || children.length > 0) {
			out.push({ ...n, children: selfOk ? n.children : children })
		}
	}
	return out
}

const filteredTree = computed(() => filterNodes(tree.value, filter.keyword.trim().toLowerCase()))

const columns = computed(() => [
	{ field: 'title', title: t('menuAdmin.colTitle'), minWidth: 200, treeNode: true, showOverflow: 'tooltip' as const },
	{ field: 'name', title: t('menuAdmin.colName'), minWidth: 150, showOverflow: 'tooltip' as const },
	{ field: 'type', title: t('menuAdmin.colType'), width: 90, slots: { default: 'cell_type' } },
	{ field: 'permission', title: t('menuAdmin.colPermission'), minWidth: 160, showOverflow: 'tooltip' as const },
	{ field: 'icon', title: t('menuAdmin.colIcon'), width: 110 },
	{ field: 'status', title: t('menuAdmin.colStatus'), width: 80, slots: { default: 'cell_status' } },
	{ field: 'isKeepAlive', title: t('menuAdmin.colKeepAlive'), width: 80, slots: { default: 'cell_keepAlive' } },
	{ field: 'orderNo', title: t('menuAdmin.colSort'), width: 80 },
	{ title: t('common.operations'), minWidth: 190, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

async function loadTree(): Promise<void> {
	loading.value = true
	try {
		tree.value = await menuAdminApi.getFullMenuTree()
	} finally {
		loading.value = false
	}
}

/* ── 新增/编辑 ─────────────────────────────── */
const dialog = reactive({ visible: false, mode: 'add' as 'add' | 'edit', id: 0 as number | string, pid: 0 as number | string, parentTitle: '' })
const formRef = ref<FormInstance>()
const saving = ref(false)
const form = reactive({ id: 0 as number | string, pid: 0 as number | string, name: '', title: '', type: 2, permission: '', icon: '', orderNo: 0, isKeepAlive: 1 })
const rules = computed<FormRules>(() => ({
	name: [{ required: true, message: t('menuAdmin.ruleNameRequired'), trigger: 'blur' }],
	title: [{ required: true, message: t('menuAdmin.ruleTitleRequired'), trigger: 'blur' }],
	permission: [{ required: true, message: t('menuAdmin.rulePermissionRequired'), trigger: 'blur' }]
}))

const parentLabel = computed(() =>
	dialog.mode === 'edit' ? dialog.parentTitle : String(dialog.pid) === '0' ? t('menuAdmin.topLevel') : dialog.parentTitle
)

function openAdd(parent: MenuNode | null): void {
	dialog.mode = 'add'
	dialog.pid = parent ? parent.id : 0
	dialog.parentTitle = parent ? parent.title ?? '' : ''
	dialog.visible = true
	Object.assign(form, {
		id: 0,
		pid: dialog.pid,
		name: '',
		title: '',
		// 目录/菜单下默认建菜单;菜单下默认建按钮
		type: parent ? (parent.type === 1 ? 2 : 3) : 1,
		permission: '',
		icon: '',
		orderNo: 0,
		isKeepAlive: 1
	})
}

function openEdit(row: MenuNode): void {
	dialog.mode = 'edit'
	dialog.id = row.id
	dialog.pid = row.pid
	dialog.parentTitle = row.title ?? ''
	dialog.visible = true
	Object.assign(form, {
		id: row.id,
		pid: row.pid,
		name: row.name ?? '',
		title: row.title ?? '',
		type: row.type,
		permission: row.permission ?? '',
		icon: row.icon ?? '',
		orderNo: row.orderNo,
		isKeepAlive: row.isKeepAlive === 0 ? 0 : 1
	})
}

async function onSave(): Promise<void> {
	await formRef.value?.validate()
	saving.value = true
	try {
		if (dialog.mode === 'add') {
			await menuAdminApi.addMenu({
				pid: form.pid,
				name: form.name,
				title: form.title,
				type: form.type,
				permission: form.permission || undefined,
				orderNo: form.orderNo,
				icon: form.icon || undefined,
				isKeepAlive: form.type === 3 ? undefined : form.isKeepAlive
			})
		} else {
			await menuAdminApi.updateMenu({
				id: form.id,
				pid: form.pid,
				name: form.name,
				title: form.title,
				type: form.type,
				permission: form.permission || undefined,
				orderNo: form.orderNo,
				icon: form.icon || undefined,
				isKeepAlive: form.type === 3 ? undefined : form.isKeepAlive
			})
		}
		ElMessage.success(t('menuAdmin.msgSaved'))
		dialog.visible = false
		void loadTree()
	} finally {
		saving.value = false
	}
}

/* ── 启停(批 CH G28:0 启用/1 停用;停用节点+整子树退出登录菜单树) ── */
async function onToggleStatus(row: MenuNode, enabled: boolean): Promise<void> {
	// 停用是子树级影响:先确认;取消则直接返回——开关为受控 model-value,不会自行翻转,保持原状即还原
	if (!enabled) {
		try {
			await ElMessageBox.confirm(
				t('menuAdmin.msgDisableConfirm', { name: row.title }),
				t('menuAdmin.msgToggleTitle'),
				{ type: 'warning', confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel') }
			)
		} catch {
			return
		}
	}
	await menuAdminApi.setStatusMenu(row.id, enabled ? 0 : 1)
	ElMessage.success(enabled ? t('menuAdmin.msgEnabled') : t('menuAdmin.msgDisabled'))
	void loadTree()
}

async function onDelete(row: MenuNode): Promise<void> {	try {
		await ElMessageBox.confirm(t('menuAdmin.msgDeleteConfirm', { name: row.title }), t('menuAdmin.msgDeleteTitle'), {
			type: 'warning'
		})
	} catch {
		return
	}
	await menuAdminApi.deleteMenu(row.id)
	ElMessage.success(t('menuAdmin.msgDeleted'))
	void loadTree()
}

onMounted(() => {
	void loadTree()
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
.status-select {
	width: 150px;
}

.form-tip {
	font-size: 12px;
	line-height: 1.5;
	color: var(--ba-text-tertiary);
}

:deep(.mt) {
	display: inline-block;
	padding: 2px 8px;
	border-radius: 10px;
	font-size: 12px;
}
:deep(.mt-dir) {
	background: rgb(59 130 246 / 12%);
	color: #2563eb;
}
:deep(.mt-menu) {
	background: var(--ba-brand-soft);
	color: var(--ba-brand);
}
:deep(.mt-btn) {
	background: rgb(16 185 129 / 12%);
	color: #059669;
}
</style>
