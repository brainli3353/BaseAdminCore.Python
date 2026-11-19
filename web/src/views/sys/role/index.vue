<template>
	<div class="ba-page">
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('role.title') }}</h3>
				<p class="ba-sub">{{ t('role.sub') }}</p>
			</div>
			<el-button v-perm="'sysRole/add'" type="primary" @click="openAdd">
				<el-icon><Plus /></el-icon>{{ t('role.btnAdd') }}
			</el-button>
		</div>

		<div class="ba-card">
			<div class="search-row">
				<el-input
					v-model="query.keyword"
					:placeholder="t('common.phKeyword')"
					clearable
					class="search-input"
					@keyup.enter="reload"
					@clear="reload"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
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
				<template #cell_sys="{ row }">
					<span v-if="row.sysFlag" class="st st-super">{{ t('role.tagSys') }}</span>
					<span v-else>—</span>
				</template>
				<template #row_ops="{ row }">
					<el-button v-perm="'sysRole/update'" link type="primary" size="small" @click="openEdit(row)">
						{{ t('common.edit') }}
					</el-button>
					<el-button
						v-perm="'sysRole/delete'"
						link
						type="danger"
						size="small"
						:disabled="row.sysFlag"
						:loading="deletingId === row.id"
						@click="onDelete(row)"
					>
						{{ t('common.delete') }}
					</el-button>
					<el-dropdown @command="(cmd: unknown) => onRowCommand(cmd, row)">
						<el-button link type="primary" size="small">
							{{ t('common.more') }}<el-icon class="more-arrow"><ArrowDown /></el-icon>
						</el-button>
						<template #dropdown>
							<el-dropdown-menu>
								<el-dropdown-item v-perm="'sysRole/grantMenu'" command="grantMenu" :disabled="row.sysFlag">
									{{ t('role.btnGrantMenu') }}
								</el-dropdown-item>
								<el-dropdown-item v-perm="'sysRole/grantOrg'" command="scope" :disabled="row.sysFlag">
									{{ t('role.btnDataScope') }}
								</el-dropdown-item>
								<el-dropdown-item v-perm="'sysRole/grantTable'" command="field" :disabled="row.sysFlag">
									{{ t('role.btnFieldPerm') }}
								</el-dropdown-item>
								<el-dropdown-item v-perm="'sysRole/grantApi'" command="api" :disabled="row.sysFlag">
									{{ t('role.btnApiBlacklist') }}
								</el-dropdown-item>
								<el-dropdown-item
									v-perm="'sysRole/copy'"
									command="copy"
									:disabled="copyingId === row.id"
								>
									{{ t('role.btnCopy') }}
								</el-dropdown-item>
							</el-dropdown-menu>
						</template>
					</el-dropdown>
				</template>
			</vxe-grid>
		</div>

		<!-- 新增/编辑 -->
		<el-dialog v-model="dialog.visible" :title="dialog.mode === 'add' ? t('role.dlgAdd') : t('role.dlgEdit')" width="480px" destroy-on-close>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="84px">
				<el-form-item :label="t('role.labelName')" prop="name">
					<el-input v-model="form.name" :placeholder="t('role.phName')" />
				</el-form-item>
				<el-form-item v-if="dialog.mode === 'add'" :label="t('role.labelCode')" prop="code">
					<el-input v-model="form.code" :placeholder="t('role.phCode')" />
				</el-form-item>
				<el-form-item :label="t('role.labelDataScope')">
					<el-select v-model="form.dataScope" class="full-width">
						<el-option v-for="d in dataScopeOptions" :key="d.value" :label="d.label" :value="d.value" />
					</el-select>
				</el-form-item>
				<el-form-item :label="t('common.remark')">
					<el-input v-model="form.remark" type="textarea" :rows="2" :placeholder="t('role.phOptional')" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSave">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>

		<!-- 菜单授权(全量替换) -->
		<el-dialog v-model="grantDialog.visible" :title="t('role.dlgGrantMenu')" width="520px" destroy-on-close>
			<p class="dialog-hint">{{ t('role.hintGrantMenu') }}</p>
			<div v-loading="grantDialog.loading" class="grant-tree">
				<el-tree
					ref="treeRef"
					:data="menuTree"
					show-checkbox
					node-key="id"
					:props="{ label: 'title', children: 'children' }"
					:default-checked-keys="grantDialog.checked"
					default-expand-all
				/>
			</div>
			<template #footer>
				<el-button @click="grantDialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSaveGrant">{{ t('role.btnSaveGrant') }}</el-button>
			</template>
		</el-dialog>

		<!-- 数据范围(自定义机构,全量替换;批 BH) -->
		<el-dialog v-model="scopeDialog.visible" :title="t('role.dlgDataScope', { name: scopeDialog.roleName })" width="520px" destroy-on-close>
			<p class="dialog-hint">{{ t('role.hintDataScope') }}</p>
			<el-form label-width="84px">
				<el-form-item :label="t('role.labelDataScope')">
					<el-select v-model="scopeDialog.dataScope" class="full-width">
						<el-option v-for="d in dataScopeOptions" :key="d.value" :label="d.label" :value="d.value" />
					</el-select>
				</el-form-item>
			</el-form>
			<div v-show="scopeDialog.dataScope === 5">
				<div v-loading="scopeDialog.loading" class="grant-tree">
					<el-tree
						ref="scopeTreeRef"
						:data="orgTree"
						show-checkbox
						node-key="id"
						:props="{ label: 'name', children: 'children', disabled: 'disabled' }"
						:default-checked-keys="scopeDialog.checked"
					/>
				</div>
			</div>
			<template #footer>
				<el-button @click="scopeDialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSaveScope">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>

		<!-- 字段权限(表-列授权,全量替换) -->
		<el-drawer v-model="fieldDrawer.visible" :title="t('role.drawerFieldPerm', { name: fieldDrawer.roleName })" size="560px" destroy-on-close>
			<el-alert
				class="field-alert"
				type="warning"
				:closable="false"
				show-icon
				:title="t('role.alertFieldEmpty')"
			/>
			<div v-loading="fieldDrawer.loading" class="grant-tree field-tree">
				<el-tree
					ref="fieldTreeRef"
					:data="fieldDrawer.nodes"
					show-checkbox
					node-key="id"
					:props="{ label: 'label', children: 'children' }"
					:default-checked-keys="fieldDrawer.checked"
					default-expand-all
				>
					<template #default="{ data }: { data: FieldTreeNode }">
						<span class="field-node">
							<span>{{ data.label }}</span>
							<span v-if="data.comment" class="field-comment">{{ data.comment }}</span>
						</span>
					</template>
				</el-tree>
				<el-empty
					v-if="!fieldDrawer.loading && !fieldDrawer.nodes.length"
					:description="canAllTableColumn ? t('role.emptyNoField') : t('role.emptyNoPermAllTableColumn')"
					:image-size="60"
				/>
			</div>

			<!-- 表级开关(受管表):手动开/关该表字段权限,授权会自动开启 -->
			<div class="table-scope-panel">
				<div class="section-title">
					{{ t('role.tableScopeTitle') }}
					<span class="section-hint">{{ t('role.tableScopeHint') }}</span>
				</div>
				<el-alert
					class="field-alert"
					type="info"
					:closable="false"
					show-icon
					:title="t('role.alertTableScope')"
				/>
				<div v-loading="tableScopesLoading" class="table-scope-wrap">
					<el-table v-if="tableScopes.length" :data="tableScopes" size="small" row-key="tableName" class="table-scope-grid">
						<el-table-column prop="tableName" :label="t('role.colTableName')" min-width="180" show-overflow-tooltip />
						<el-table-column prop="tableComment" :label="t('role.colTableComment')" min-width="130" show-overflow-tooltip>
							<template #default="scope">{{ (scope.row as TableScopeRow).tableComment || '—' }}</template>
						</el-table-column>
						<el-table-column prop="columnCount" :label="t('role.colColumnCount')" width="70" align="center" />
						<el-table-column :label="t('role.colGrantedRoleCount')" min-width="150">
							<template #default="scope">
								<span v-if="(scope.row as TableScopeRow).grantedRoleCount > 0 && !(scope.row as TableScopeRow).enabled" class="st st-warn">{{ t('role.tagGrantedButStopped') }}</span>
								<span v-else>{{ (scope.row as TableScopeRow).grantedRoleCount }}</span>
							</template>
						</el-table-column>
						<el-table-column :label="t('role.colSwitch')" width="90" align="center">
							<template #default="scope">
								<el-switch
									v-perm="'sysRole/tableScope'"
									:model-value="(scope.row as TableScopeRow).enabled"
									:loading="(scope.row as TableScopeRow)._updating ?? false"
									@change="(val: boolean | string | number) => onTableScopeChange(scope.row as TableScopeRow, val as boolean)"
								/>
							</template>
						</el-table-column>
					</el-table>
					<el-empty
						v-else-if="!tableScopesLoading"
						:description="canTableScope ? t('role.emptyNoTable') : t('role.emptyNoPermTableScope')"
						:image-size="60"
					/>
				</div>
			</div>
			<template #footer>
				<el-button @click="fieldDrawer.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button v-perm="'sysRole/grantTable'" type="primary" :loading="saving" @click="onSaveFieldGrant">{{ t('common.save') }}</el-button>
			</template>
		</el-drawer>

		<!-- API 黑名单(全量替换;批 CF 补 G27:后端批 A 2.10 已完整,此前零 UI 消费) -->
		<el-dialog v-model="apiDialog.visible" :title="t('role.dlgApiBlacklist', { name: apiDialog.roleName })" width="560px" destroy-on-close>
			<p class="dialog-hint">{{ t('role.hintApiBlacklist') }}</p>
			<div v-loading="apiDialog.loading">
				<el-select
					v-model="apiDialog.selected"
					multiple
					filterable
					allow-create
					default-first-option
					:placeholder="t('role.phApiBlacklist')"
					class="full-width"
				>
					<el-option v-for="p in apiPermOptions" :key="p" :label="p" :value="p" />
				</el-select>
			</div>
			<template #footer>
				<el-button @click="apiDialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSaveApiBlacklist">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'Role' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, ArrowDown, Search } from '@element-plus/icons-vue'
import * as roleApi from '@/api/sys/role'
import * as menuAdminApi from '@/api/sys/menuAdmin'
import * as orgApi from '@/api/sys/org'
import type { OrgOutput } from '@/api/sys/org'
import type { RoleOutput, RoleTableOutput, TableColumnOutput, TableScopeOutput } from '@/api/sys/role'
import type { MenuNode } from '@/types/api'
import { usePaged } from '@/composables/usePaged'
import { useMenuStore } from '@/stores/menu'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()

/** 与 v-perm 同口径(超管 999 直通):未授权即不请求对应端点(v-perm 只摘 DOM,拦不住抽屉拉数)。 */
const menuStore = useMenuStore()
const userStore = useUserStore()

function hasPerm(key: string): boolean {
	return userStore.user?.accountType === 999 || menuStore.permissions.includes(key)
}
const canAllTableColumn = hasPerm('sysRole/allTableColumn')
const canRoleTable = hasPerm('sysRole/table')
const canTableScope = hasPerm('sysRole/tableScope')
const canRoleOrg = hasPerm('sysRole/org') // 批 BH:数据范围自定义机构回读
const canOrgTree = hasPerm('sysOrg/tree') // 批 BH:机构树
const canRoleApi = hasPerm('sysRole/api') // 批 CF:接口黑名单回读
const canMenuPage = hasPerm('sysMenu/page') // 批 CF:黑名单选项源(按钮权限标识来自全菜单树)

const query = reactive({ keyword: '', orderBy: '' as string, desc: false as boolean })
const { loading, rows, pager, fetchPage, reload, onPageChange } = usePaged<RoleOutput>(q =>
	roleApi.pageRole({
		keyword: query.keyword || null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: query.orderBy || undefined,
		desc: query.orderBy ? query.desc : undefined
	})
)

function doReset(): void {
	query.keyword = ''
	query.orderBy = ''
	query.desc = false
	reload()
}

function onSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	query.orderBy = order ? property : ''
	query.desc = order === 'desc'
	reload()
}

const dataScopeOptions = computed(() => [
	{ label: t('role.scopeAll'), value: 1 },
	{ label: t('role.scopeOrgAndChild'), value: 2 },
	{ label: t('role.scopeOrg'), value: 3 },
	{ label: t('role.scopeSelf'), value: 4 },
	{ label: t('role.scopeCustom'), value: 5 }
])

const columns = computed(() => [
	{ field: 'id', title: 'Id', minWidth: 150, sortable: true },
	{ field: 'name', title: t('role.colName'), minWidth: 130, sortable: true, showOverflow: 'tooltip' },
	{ field: 'code', title: t('role.colCode'), minWidth: 120, sortable: true, showOverflow: 'tooltip' },
	{
		field: 'dataScope',
		title: t('role.colDataScope'),
		width: 120,
		sortable: true,
		formatter: ({ cellValue }: { cellValue: number }) =>
			dataScopeOptions.value.find(d => d.value === cellValue)?.label ?? cellValue
	} as object,
	{ field: 'sysFlag', title: t('role.colSysFlag'), width: 80, sortable: true, slots: { default: 'cell_sys' } },
	{ field: 'remark', title: t('common.remark'), minWidth: 160, sortable: true, showOverflow: 'tooltip' },
	{ title: t('common.operations'), minWidth: 320, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

/* ── 新增/编辑 ─────────────────────────────── */
const dialog = reactive({ visible: false, mode: 'add' as 'add' | 'edit', id: 0 as number | string })
const formRef = ref<FormInstance>()
const saving = ref(false)
const copyingId = ref<number | string | null>(null)
const deletingId = ref<number | string | null>(null)
const form = reactive({ id: 0 as number | string, name: '', code: '', remark: '', dataScope: 4 })
const rules = computed<FormRules>(() => ({
	name: [{ required: true, message: t('role.ruleNameRequired'), trigger: 'blur' }],
	code: [{ required: true, message: t('role.ruleCodeRequired'), trigger: 'blur' }]
}))

function openAdd(): void {
	dialog.mode = 'add'
	dialog.visible = true
	Object.assign(form, { id: 0, name: '', code: '', remark: '', dataScope: 4 })
}

function openEdit(row: RoleOutput): void {
	dialog.mode = 'edit'
	dialog.id = row.id
	dialog.visible = true
	Object.assign(form, {
		id: row.id,
		name: row.name ?? '',
		code: row.code ?? '',
		remark: row.remark ?? '',
		dataScope: row.dataScope
	})
}

async function onSave(): Promise<void> {
	await formRef.value?.validate()
	saving.value = true
	try {
		if (dialog.mode === 'add') {
			await roleApi.addRole({ name: form.name, code: form.code, remark: form.remark || undefined, dataScope: form.dataScope })
		} else {
			await roleApi.updateRole({ id: form.id, name: form.name, remark: form.remark || undefined, dataScope: form.dataScope })
		}
		ElMessage.success(t('role.msgSaved'))
		dialog.visible = false
		void fetchPage()
	} finally {
		saving.value = false
	}
}

/* ── 菜单授权 ─────────────────────────────── */
const grantDialog = reactive({ visible: false, roleId: 0 as number | string, loading: false, checked: [] as (number | string)[] })
const treeRef = ref<InstanceType<typeof import('element-plus')['ElTree']>>()
const menuTree = ref<MenuNode[]>([])

async function openGrantMenu(row: RoleOutput): Promise<void> {
	grantDialog.roleId = row.id
	grantDialog.checked = []
	grantDialog.visible = true
	grantDialog.loading = true
	try {
		// 全树(含按钮) + 已授权 Id 回读
		const [tree, checked] = await Promise.all([
			menuAdminApi.getFullMenuTree(),
			roleApi.getRoleMenus(row.id)
		])
		menuTree.value = tree
		grantDialog.checked = checked
	} finally {
		grantDialog.loading = false
	}
}

async function onSaveGrant(): Promise<void> {
	const checked = (treeRef.value?.getCheckedKeys() as (number | string)[]) ?? []
	const halfChecked = (treeRef.value?.getHalfCheckedKeys() as (number | string)[]) ?? []
	// 全量替换:父节点勾选状态一并提交,与服务端 Id 集合口径一致
	saving.value = true
	try {
		await roleApi.grantRoleMenu(grantDialog.roleId, [...checked, ...halfChecked] as unknown as (number | string)[])
		ElMessage.success(t('role.msgGrantMenuSaved'))
		grantDialog.visible = false
	} finally {
		saving.value = false
	}
}

/* ── API 黑名单(全量替换;批 CF 补 G27) ──────────── */
const apiPermOptions = ref<string[]>([])
const apiDialog = reactive({ visible: false, roleId: 0 as number | string, roleName: '', loading: false, selected: [] as string[] })

/** 从全菜单树抽按钮(type=3)权限标识作选项源(与 v-perm/[MenuPerm] 同一份数据) */
function collectPermKeys(nodes: MenuNode[]): string[] {
	const out = new Set<string>()
	const walk = (list: MenuNode[]): void => {
		for (const n of list) {
			if (n.type === 3 && n.permission) out.add(n.permission)
			walk(n.children ?? [])
		}
	}
	walk(nodes)
	return [...out]
}

async function openApiBlacklist(row: RoleOutput): Promise<void> {
	apiDialog.roleId = row.id
	apiDialog.roleName = row.name ?? ''
	apiDialog.selected = []
	apiDialog.visible = true
	apiDialog.loading = true
	try {
		// 选项源 + 现值回读;未授权即不请求(与 v-perm 同口径,v-perm 只摘 DOM 拦不住拉数)
		const [tree, current] = await Promise.all([
			canMenuPage ? menuAdminApi.getFullMenuTree() : Promise.resolve<MenuNode[]>([]),
			canRoleApi ? roleApi.getRoleApis(row.id) : Promise.resolve<string[]>([])
		])
		apiPermOptions.value = collectPermKeys(tree)
		// 回读值可能含选项外标识(手工录入的历史值),el-select 对选项外值原样显示 tag,直接采用
		apiDialog.selected = current
	} finally {
		apiDialog.loading = false
	}
}

async function onSaveApiBlacklist(): Promise<void> {
	saving.value = true
	try {
		await roleApi.grantRoleApi(apiDialog.roleId, apiDialog.selected)
		ElMessage.success(t('role.msgApiBlacklistSaved'))
		apiDialog.visible = false
	} finally {
		saving.value = false
	}
}

/* ── 数据范围(自定义机构,全量替换;批 BH) ──── */
const scopeDialog = reactive({
	visible: false,
	roleId: 0 as number | string,
	roleName: '',
	remark: undefined as string | undefined,
	dataScope: 4,
	loading: false,
	checked: [] as (number | string)[]
})
const scopeTreeRef = ref<InstanceType<typeof import('element-plus')['ElTree']>>()
const orgTree = ref<OrgOutput[]>([])

async function openScope(row: RoleOutput): Promise<void> {
	scopeDialog.roleId = row.id
	scopeDialog.roleName = row.name ?? ''
	// UpdateAsync 无条件覆盖 Remark ⇒ 原样带回现有备注(防保存数据范围时抹掉备注)
	scopeDialog.remark = row.remark ?? undefined
	scopeDialog.dataScope = row.dataScope
	scopeDialog.checked = []
	scopeDialog.visible = true
	scopeDialog.loading = true
	try {
		// 机构全树(服务端已把范围外机构标记 disabled,防越权勾选)+ 自定义机构 Id 回读;未授权即不请求
		const [tree, checked] = await Promise.all([
			canOrgTree ? orgApi.getOrgTree() : Promise.resolve<OrgOutput[]>([]),
			canRoleOrg ? roleApi.getRoleOrgs(row.id) : Promise.resolve<(number | string)[]>([])
		])
		// 同一 tick 内一次性赋值:el-tree 的 default-checked-keys 依赖树数据已就位
		orgTree.value = tree
		scopeDialog.checked = checked
	} finally {
		scopeDialog.loading = false
	}
}

async function onSaveScope(): Promise<void> {
	// 全量替换:非自定义范围显式提交空集清空(比参照更严:防切回自定义时复活陈旧机构集)
	const checked = (scopeTreeRef.value?.getCheckedKeys() as (number | string)[]) ?? []
	const orgIds = scopeDialog.dataScope === 5 ? checked : []
	saving.value = true
	try {
		await roleApi.updateRole({
			id: scopeDialog.roleId,
			name: scopeDialog.roleName,
			remark: scopeDialog.remark,
			dataScope: scopeDialog.dataScope
		})
		await roleApi.grantRoleOrg(scopeDialog.roleId, orgIds)
		ElMessage.success(t('role.msgScopeSaved'))
		scopeDialog.visible = false
		void fetchPage()
	} finally {
		saving.value = false
	}
}

/* ── 字段权限(表-列授权) ───────────────────── */
/** 授权树节点两级:表(id=表名) → 列(id="表名:列名",即提交给服务的授权项) */
interface FieldTreeNode {
	id: string
	label: string
	comment: string
	children?: FieldTreeNode[]
}

const fieldDrawer = reactive({
	visible: false,
	roleId: 0 as number | string,
	roleName: '',
	loading: false,
	nodes: [] as FieldTreeNode[],
	checked: [] as string[]
})
const fieldTreeRef = ref<InstanceType<typeof import('element-plus')['ElTree']>>()

async function openFieldGrant(row: RoleOutput): Promise<void> {
	fieldDrawer.roleId = row.id
	fieldDrawer.roleName = row.name ?? ''
	fieldDrawer.nodes = []
	fieldDrawer.checked = []
	fieldDrawer.visible = true
	fieldDrawer.loading = true
	tableScopesLoading.value = true
	tableScopes.value = []
	try {
		// 授权树(表→列) + 该角色已授权项回读 + 表级开关(受管表)状态;三块各自按权限键前置判断,未授权即不请求
		const [tree, granted, scopes] = await Promise.all([
			canAllTableColumn ? roleApi.getAllTableColumn() : Promise.resolve<TableColumnOutput[]>([]),
			canRoleTable ? roleApi.getRoleTable(row.id) : Promise.resolve<RoleTableOutput | null>(null),
			canTableScope ? roleApi.getTableScopes() : Promise.resolve<TableScopeOutput[]>([])
		])
		// 同一 tick 内一次性赋值:el-tree 的 default-checked-keys 依赖树数据已就位
		fieldDrawer.nodes = tree.map(t => ({
			id: t.tableName,
			label: t.tableName,
			comment: t.tableComment ?? '',
			children: t.columns.map(c => ({
				id: `${t.tableName}:${c.columnName}`,
				label: c.columnName,
				comment: c.columnComment ?? ''
			}))
		}))
		fieldDrawer.checked = granted?.items ?? []
		tableScopes.value = scopes
	} finally {
		fieldDrawer.loading = false
		tableScopesLoading.value = false
	}
}

/* ── 表级开关(受管表) ─────────────────────────── */
/** 表格行 = 契约回读项 + 前端请求中标记(防重复提交) */
type TableScopeRow = TableScopeOutput & { _updating?: boolean }

const tableScopes = ref<TableScopeRow[]>([])
const tableScopesLoading = ref(false)

/** 切换开关:乐观更新,失败回滚该行(错误提示已由全局拦截器统一弹出) */
async function onTableScopeChange(row: TableScopeRow, val: boolean): Promise<void> {
	if (row._updating) return
	const prev = row.enabled
	row.enabled = val
	row._updating = true
	try {
		await roleApi.setTableScope({ tableName: row.tableName, enabled: val })
	} catch {
		// 失败回滚该行:开关弹回原状态
		row.enabled = prev
	} finally {
		row._updating = false
	}
}

async function onSaveFieldGrant(): Promise<void> {
	// 只取叶子(列)节点:表节点是表级伪节点,其 id(纯表名)不是合法授权项
	const keys = (fieldTreeRef.value?.getCheckedKeys(true) as (number | string)[] | undefined) ?? []
	const items = keys.map(k => String(k))
	saving.value = true
	try {
		await roleApi.grantRoleTable(fieldDrawer.roleId, items)
		ElMessage.success(t('role.msgFieldGrantSaved'))
		fieldDrawer.visible = false
	} finally {
		saving.value = false
	}
}

/* ── 复制 / 删除 ───────────────────────────── */
/** 操作列「更多」下拉分发(编辑/删除直出,其余折叠于此)。 */
function onRowCommand(cmd: unknown, row: RoleOutput): void {
	switch (cmd) {
		case 'grantMenu':
			void openGrantMenu(row)
			break
		case 'scope':
			void openScope(row)
			break
		case 'field':
			void openFieldGrant(row)
			break
		case 'api':
			void openApiBlacklist(row)
			break
		case 'copy':
			void onCopy(row)
			break
	}
}

async function onCopy(row: RoleOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('role.msgCopyConfirm', { name: row.name }), t('role.msgCopyTitle'), { type: 'info' })
	} catch {
		return
	}
	copyingId.value = row.id
	try {
		await roleApi.copyRole(row.id)
		ElMessage.success(t('role.msgCopied'))
		await fetchPage()
	} finally {
		copyingId.value = null
	}
}

async function onDelete(row: RoleOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('role.msgDeleteConfirm', { name: row.name }), t('role.msgDeleteTitle'), {
			type: 'warning'
		})
	} catch {
		return
	}
	deletingId.value = row.id
	try {
		await roleApi.deleteRole(row.id)
		ElMessage.success(t('role.msgDeleted'))
		await fetchPage()
	} finally {
		deletingId.value = null
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
.full-width {
	width: 100%;
}
.more-arrow {
	margin-left: 2px;
}
.dialog-hint {
	font-size: 12px;
	color: var(--ba-text-tertiary);
	margin: 0 0 12px;
	line-height: 1.6;
}
.grant-tree {
	max-height: 420px;
	overflow: auto;
	border: 1px solid var(--ba-border);
	border-radius: var(--ba-radius);
	padding: 8px;
}
.field-alert {
	margin-bottom: 12px;
}
.field-tree {
	max-height: calc(100vh - 260px);
}
.field-node {
	display: inline-flex;
	align-items: center;
	gap: 8px;
}
.field-comment {
	font-size: 12px;
	color: var(--ba-text-tertiary);
}
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
.table-scope-panel {
	margin-top: 16px;
}
.table-scope-wrap {
	min-height: 120px;
	margin-top: 12px;
}
.table-scope-grid {
	width: 100%;
}
:deep(.st) {
	display: inline-block;
	padding: 2px 8px;
	border-radius: 10px;
	font-size: 12px;
}
:deep(.st-warn) {
	background: var(--el-color-warning-light-9);
	color: var(--el-color-warning);
}
:deep(.st-super) {
	background: var(--ba-brand-soft);
	color: var(--ba-brand);
}
</style>
