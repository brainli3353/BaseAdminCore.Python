<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('user.title') }}</h3>
				<p class="ba-sub">{{ t('user.sub') }}</p>
			</div>
			<el-button v-perm="'sysUser/export'" :loading="exporting" @click="onExport">
				<el-icon><Download /></el-icon>{{ t('user.btnExport') }}
			</el-button>
			<el-button @click="colSettingsVisible = true">{{ t('user.btnColSettings') }}</el-button>
			<el-button v-perm="'sysUser/add'" type="primary" @click="openAdd">
				<el-icon><Plus /></el-icon>{{ t('user.btnAdd') }}
			</el-button>
		</div>

		<!-- 数据卡 -->
		<div class="ba-card">
			<div class="search-row">
				<el-input
					v-model="query.account"
					:placeholder="t('user.phSearchAccount')"
					clearable
					class="search-input"
					@keyup.enter="reload"
					@clear="reload"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
				<!-- 批B6：EP 的 TreeOptionProps 无 value 键（key 计算＝nodeKey||valueKey||'value'），原 value:'id' 系无效配置，已删；该组件能否取到节点值属独立疑点，另登差距清单 -->
				<el-tree-select
					v-model="query.orgId"
					:data="orgTree"
					:props="{ label: 'name', children: 'children', disabled: 'disabled' }"
					check-strictly
					clearable
					:render-after-expand="false"
					:placeholder="t('user.phOrg')"
					class="search-org"
					@change="reload"
				/>
				<el-select v-model="query.status" :placeholder="t('common.phStatus')" class="search-status" @change="reload">
					<el-option :label="t('common.all')" :value="OPT_ALL" />
					<el-option :label="t('user.statusEnabled')" :value="0" />
					<el-option :label="t('user.statusDisabled')" :value="1" />
				</el-select>
				<el-button type="primary" @click="reload">{{ t('common.search') }}</el-button>
				<el-button @click="resetQuery">{{ t('common.reset') }}</el-button>
			</div>

			<vxe-grid
				ref="gridRef"
				:loading="loading"
				:data="rows"
				:columns="ccColumns"
				:pager-config="pagerConfig"
				:row-config="{ keyField: 'id' }"
				:sort-config="{ remote: true }"
				@page-change="onPageChange"
				@sort-change="onSortChange"
			>
				<template #cell_status="{ row }">
					<span class="st" :class="row.status === 0 ? 'st-ok' : 'st-off'">
						{{ row.status === 0 ? t('user.statusEnabled') : t('user.statusDisabled') }}
					</span>
				</template>
				<template #cell_type="{ row }">
					<span v-if="row.accountType === 999" class="st st-super">{{ t('user.typeSuper') }}</span>
					<span v-else>{{ t('user.typeNormal') }}</span>
				</template>
				<template #row_ops="{ row }">
					<el-button v-perm="'sysUser/update'" link type="primary" size="small" @click="openEdit(row)">
						{{ t('common.edit') }}
					</el-button>
					<el-button
						v-perm="'sysUser/delete'"
						link
						type="danger"
						size="small"
						:disabled="row.accountType === 999"
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
								<el-dropdown-item v-perm="'sysUser/grantRole'" command="grant">
									{{ t('user.btnGrantRole') }}
								</el-dropdown-item>
								<el-dropdown-item v-perm="'sysUser/resetPwd'" command="resetPwd">
									{{ t('user.btnResetPwd') }}
								</el-dropdown-item>
								<el-dropdown-item
									v-perm="'sysUser/unlockLogin'"
									command="unlock"
									:disabled="unlockingId === row.id"
								>
									{{ t('user.btnUnlock') }}
								</el-dropdown-item>
							</el-dropdown-menu>
						</template>
					</el-dropdown>
				</template>
			</vxe-grid>
		</div>

		<!-- 新增/编辑对话框 -->
		<el-dialog v-model="dialog.visible" :title="dialog.mode === 'add' ? t('user.dlgAdd') : t('user.dlgEdit')" width="480px" destroy-on-close>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="84px">
				<el-form-item :label="t('user.account')" prop="account">
					<el-input v-model="form.account" :placeholder="t('user.phAccount')" />
				</el-form-item>
				<el-form-item v-if="dialog.mode === 'add'" :label="t('user.password')" prop="password">
					<el-input v-model="form.password" type="password" show-password :placeholder="t('user.phPassword')" />
				</el-form-item>
				<el-form-item :label="t('user.realName')" prop="realName">
					<el-input v-model="form.realName" :placeholder="t('user.phRealName')" />
				</el-form-item>
				<el-form-item :label="t('common.status')" prop="status">
					<el-radio-group v-model="form.status">
						<el-radio :value="0">{{ t('user.statusEnabled') }}</el-radio>
						<el-radio :value="1">{{ t('user.statusDisabled') }}</el-radio>
					</el-radio-group>
				</el-form-item>
				<el-form-item :label="t('user.org')">
					<!-- 批B6：EP 的 TreeOptionProps 无 value 键（key 计算＝nodeKey||valueKey||'value'），原 value:'id' 系无效配置，已删；该组件能否取到节点值属独立疑点，另登差距清单 -->
					<el-tree-select
						v-model="form.orgId"
						:data="orgTree"
						:props="{ label: 'name', children: 'children', disabled: 'disabled' }"
						check-strictly
						clearable
						:render-after-expand="false"
						:placeholder="t('user.phOrg')"
					/>
				</el-form-item>
				<el-form-item :label="t('user.pos')">
					<el-select v-model="form.posId" clearable :placeholder="t('user.phPos')" class="full-width">
						<el-option v-for="p in posOptions" :key="p.id" :label="p.name ?? String(p.id)" :value="p.id" />
					</el-select>
				</el-form-item>
				<el-form-item v-if="dialog.mode === 'add'" :label="t('user.role')">
					<el-select v-model="form.roleIds" multiple :placeholder="t('user.phRole')" class="full-width">
						<el-option v-for="r in roleOptions" :key="r.id" :label="r.name ?? undefined" :value="r.id" />
					</el-select>
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSave">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>

		<!-- 分配角色对话框 -->
		<el-dialog v-model="grantDialog.visible" :title="t('user.dlgGrant')" width="420px" destroy-on-close>
			<div v-loading="grantDialog.loading">
				<p class="dialog-hint">{{ t('user.grantHint') }}</p>
				<el-select v-model="grantDialog.roleIds" multiple :placeholder="t('user.phSelectRole')" class="full-width">
					<el-option v-for="r in roleOptions" :key="r.id" :label="r.name ?? undefined" :value="r.id" />
				</el-select>
			</div>
			<template #footer>
				<el-button @click="grantDialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSaveGrant">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>

		<!-- 重置密码对话框 -->
		<el-dialog v-model="pwdDialog.visible" :title="t('user.dlgResetPwd')" width="420px" destroy-on-close>
			<p class="dialog-hint">
				{{ t('user.pwdHint') }}
			</p>
			<el-form>
				<el-form-item :label="t('user.newPassword')">
					<el-input v-model="pwdDialog.newPassword" type="password" show-password :placeholder="t('user.phNewPassword')" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="pwdDialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSavePwd">{{ t('user.btnConfirmReset') }}</el-button>
			</template>
		</el-dialog>

		<!-- 列设置对话框(批 A 4.12,用户级列设置,仅本人可见效果) -->
		<el-dialog v-model="colSettingsVisible" :title="t('user.dlgColSettings')" width="640px" destroy-on-close>
			<p class="dialog-hint">{{ t('user.colSettingsHint') }}</p>
			<div class="col-settings">
				<div v-for="(col, i) in ccColumns" :key="col.field ?? col.title" class="col-settings-row">
					<el-switch :model-value="colVisible(col)" @change="(v: string | number | boolean) => colSetVisible(col, !!v)" />
					<span class="col-name">{{ colTitle(col) }}</span>
					<el-input-number
						v-if="col.field"
						:model-value="col.width"
						:min="60"
						:max="600"
						:controls="false"
						@change="(v: number | undefined) => colSetWidth(col, v)"
					/>
					<el-select
						v-if="col.field"
						:model-value="colFixed(col)"
						@change="(v: string) => colSetFixed(col, v)"
					>
						<el-option :label="t('user.fixedNone')" value="none" />
						<el-option :label="t('user.fixedLeft')" value="left" />
						<el-option :label="t('user.fixedRight')" value="right" />
					</el-select>
					<el-button link :disabled="i === 0" @click="ccMove(i, -1)">{{ t('user.btnMoveUp') }}</el-button>
					<el-button link :disabled="i === ccColumns.length - 1" @click="ccMove(i, 1)">{{ t('user.btnMoveDown') }}</el-button>
				</div>
			</div>
			<template #footer>
				<el-button @click="onColReset">{{ t('user.btnResetDefault') }}</el-button>
				<el-button @click="colSettingsVisible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onColSave">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
/** 「全部」哨兵：该查询条件为 null ＝ 不带此筛选（业务语义，运行时必须保持 null）。
 *  批 B6：EP 按需后 `el-option.value` 的 prop 类型不再含 null ⇒ 只收口类型、不改值（改成 '' 会让"全部"变成"按空串筛选"）。 */
const OPT_ALL = null as unknown as string | number
	defineOptions({ name: 'User' })

import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, Download, ArrowDown } from '@element-plus/icons-vue'
import { useColumnCustom, type ColumnDef } from '@/composables/useColumnCustom'
import * as userApi from '@/api/sys/user'
import { exportUser } from '@/api/sys/user'
import { downloadBlob } from '@/utils/download'
import * as roleApi from '@/api/sys/role'
import * as orgApi from '@/api/sys/org'
import * as posApi from '@/api/sys/pos'
import type { UserOutput } from '@/api/sys/user'
import type { RoleOutput } from '@/api/sys/role'
import type { OrgOutput } from '@/api/sys/org'
import type { PosOutput } from '@/api/sys/pos'

const { t } = useI18n()

const loading = ref(false)
const saving = ref(false)
const exporting = ref(false)
const deletingId = ref<number | string | null>(null)
const unlockingId = ref<number | string | null>(null)
const gridRef = ref()
const rows = ref<UserOutput[]>([])
const roleOptions = ref<RoleOutput[]>([])
const orgTree = ref<OrgOutput[]>([])
const posOptions = ref<PosOutput[]>([])

const query = reactive({
	account: '' as string,
	orgId: null as number | string | null,
	status: null as number | null,
	pageIndex: 1,
	pageSize: 10,
	orderBy: '' as string,
	desc: false as boolean
})
const pagerConfig = reactive({
	total: 0,
	currentPage: 1,
	pageSize: 10,
	pageSizes: [10, 20, 50, 100]
})

/** 列标题映射(含无 field 的操作列,随语言响应式) */
const columnTitles = computed<Record<string, string>>(() => ({
	id: 'Id',
	account: t('user.colAccount'),
	realName: t('user.colRealName'),
	status: t('common.status'),
	accountType: t('user.colType'),
	ops: t('common.operations')
}))

const defaultColumns = computed<ColumnDef[]>(() => [
	{ field: 'id', title: columnTitles.value.id, width: 160, sortable: true, showOverflow: 'tooltip' },
	{ field: 'account', title: columnTitles.value.account, minWidth: 140, sortable: true, showOverflow: 'tooltip' },
	{ field: 'realName', title: columnTitles.value.realName, minWidth: 120, sortable: true, showOverflow: 'tooltip' },
	{ field: 'status', title: columnTitles.value.status, width: 100, sortable: true, slots: { default: 'cell_status' } },
	{ field: 'accountType', title: columnTitles.value.accountType, width: 100, sortable: true, slots: { default: 'cell_type' } },
	{ title: columnTitles.value.ops, minWidth: 270, fixed: 'right', slots: { default: 'row_ops' } }
])

/* ── 列设置(批 A 4.12,用户级,仅本人可见效果) ─────────────── */
const {
	localColumns: ccColumns,
	load: ccLoad,
	save: ccSave,
	reset: ccReset,
	move: ccMove,
	applyToGrid: ccApplyToGrid
} = useColumnCustom('sys/user', defaultColumns.value)
const colSettingsVisible = ref(false)

/** 列显示名(列设置对话框用,按 field 映射,随语言响应式) */
function colTitle(col: ColumnDef): string {
	const key = col.field ?? 'ops'
	return columnTitles.value[key] ?? col.title ?? ''
}

/** 同步列标题文案(保留用户列设置) */
function syncColumnTitles(): void {
	const titles = columnTitles.value
	for (const col of ccColumns.value) {
		const key = col.field ?? 'ops'
		if (titles[key]) {
			col.title = titles[key]
		}
	}
	ccApplyToGrid(gridRef.value)
}

/** 语言切换后刷新列标题(仅换文案) */
watch(columnTitles, syncColumnTitles)

function colVisible(col: ColumnDef): boolean {
	return (col as Record<string, unknown>).visible !== false
}

function colSetVisible(col: ColumnDef, visible: boolean): void {
	;(col as Record<string, unknown>).visible = visible
}

function colSetWidth(col: ColumnDef, width: number | undefined): void {
	col.width = width
}

function colFixed(col: ColumnDef): string {
	return col.fixed === 'left' || col.fixed === 'right' ? col.fixed : 'none'
}

function colSetFixed(col: ColumnDef, value: string): void {
	col.fixed = value === 'none' ? '' : (value as 'left' | 'right')
}

async function onColSave(): Promise<void> {
	saving.value = true
	try {
		const ok = await ccSave()
		ccApplyToGrid(gridRef.value)
		colSettingsVisible.value = false
		if (!ok) {
			ElMessage.error(t('user.msgColSaveFailed'))
		}
	} finally {
		saving.value = false
	}
}

async function onColReset(): Promise<void> {
	saving.value = true
	try {
		const ok = await ccReset()
		syncColumnTitles()
		colSettingsVisible.value = false
		if (!ok) {
			ElMessage.error(t('user.msgColResetFailed'))
		}
	} finally {
		saving.value = false
	}
}

async function loadMeta(): Promise<void> {
	try {
		const [roles, orgs, poss] = await Promise.all([
			roleApi.pageRole({ pageIndex: 1, pageSize: 200 }),
			orgApi.getOrgTree(),
			posApi.pagePos({ pageIndex: 1, pageSize: 200 })
		])
		roleOptions.value = roles.list
		orgTree.value = orgs
		posOptions.value = poss.list
	} catch {
		/* 元数据加载失败不阻塞列表 */
	}
}

async function reload(): Promise<void> {
	query.pageIndex = 1
	await fetchData()
}

async function fetchData(): Promise<void> {
	loading.value = true
	try {
		const res = await userApi.pageUser({
			account: query.account || null,
			orgId: query.orgId,
			status: query.status,
			pageIndex: query.pageIndex,
			pageSize: query.pageSize,
			orderBy: query.orderBy || undefined,
			desc: query.orderBy ? query.desc : undefined
		})
		rows.value = res.list
		pagerConfig.total = Number(res.total)
		pagerConfig.currentPage = query.pageIndex
		pagerConfig.pageSize = query.pageSize
	} finally {
		loading.value = false
	}
}

function resetQuery(): void {
	query.account = ''
	query.orgId = null
	query.status = null
	query.orderBy = ''
	query.desc = false
	void reload()
}

/** 导出当前查询条件下的用户列表(xlsx)。全局响应拦截器对二进制响应原样回 AxiosResponse(非 ApiResult 不解包),
 *  故此处兼容 Blob 与 AxiosResponse 两种形态取 Blob。 */
async function onExport(): Promise<void> {
	exporting.value = true
	try {
		const res = await exportUser({
			account: query.account || null,
			orgId: query.orgId,
			status: query.status,
			orderBy: query.orderBy || undefined,
			desc: query.orderBy ? query.desc : undefined
		})
		const blob = res instanceof Blob ? res : (res as unknown as { data: Blob }).data
		const stamp = new Date().toISOString().slice(0, 14).replace(/[-T:]/g, '')
		downloadBlob(blob, `用户列表_${stamp}.xlsx`)
	} finally {
		exporting.value = false
	}
}

function onSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	query.orderBy = order ? property : ''
	query.desc = order === 'desc'
	query.pageIndex = 1
	void fetchData()
}

function onPageChange({ currentPage, pageSize }: { currentPage: number; pageSize: number }): void {
	query.pageIndex = currentPage
	query.pageSize = pageSize
	void fetchData()
}

/* ── 新增/编辑 ─────────────────────────────── */
const dialog = reactive({ visible: false, mode: 'add' as 'add' | 'edit', id: 0 as number | string })
const formRef = ref<FormInstance>()
const form = reactive({
	id: 0 as number | string,
	account: '',
	password: '',
	realName: '',
	status: 0,
	orgId: null as number | string | null,
	posId: null as number | string | null,
	roleIds: [] as (number | string)[]
})
const rules = computed<FormRules>(() => ({
	account: [{ required: true, message: t('user.ruleAccountRequired'), trigger: 'blur' }],
	password: [{ required: true, message: t('user.rulePasswordRequired'), trigger: 'blur' }],
	realName: [{ required: true, message: t('user.ruleNameRequired'), trigger: 'blur' }]
}))

function openAdd(): void {
	dialog.mode = 'add'
	dialog.visible = true
	Object.assign(form, { id: 0, account: '', password: '', realName: '', status: 0, orgId: null, posId: null, roleIds: [] })
}

function openEdit(row: UserOutput): void {
	dialog.mode = 'edit'
	dialog.id = row.id
	dialog.visible = true
	Object.assign(form, {
		id: row.id,
		account: row.account ?? '',
		password: '',
		realName: row.realName ?? '',
		status: row.status,
		orgId: row.orgId,
		posId: row.posId,
		roleIds: []
	})
}

async function onSave(): Promise<void> {
	await formRef.value?.validate()
	saving.value = true
	try {
		if (dialog.mode === 'add') {
			await userApi.addUser({
				account: form.account,
				password: form.password,
				realName: form.realName,
				status: form.status,
				roleIds: form.roleIds,
				orgId: form.orgId,
				posId: form.posId
			})
		} else {
			await userApi.updateUser({
				id: form.id,
				account: form.account,
				realName: form.realName,
				status: form.status,
				orgId: form.orgId,
				posId: form.posId
			})
		}
		ElMessage.success(t('user.msgSaveSuccess'))
		dialog.visible = false
		void fetchData()
	} finally {
		saving.value = false
	}
}

/* ── 分配角色 ─────────────────────────────── */
const grantDialog = reactive({ visible: false, userId: 0 as number | string, roleIds: [] as (number | string)[], loading: false })

async function openGrant(row: UserOutput): Promise<void> {
	grantDialog.userId = row.id
	grantDialog.roleIds = []
	grantDialog.loading = true
	grantDialog.visible = true
	try {
		// 回显现有角色(批 BG):grantRole 为全量替换口径,不回显则管理员无法知悉现有授权,直接保存=误清
		grantDialog.roleIds = (await userApi.getUserRoleIds(row.id)) ?? []
	} finally {
		grantDialog.loading = false
	}
}

async function onSaveGrant(): Promise<void> {
	saving.value = true
	try {
		await userApi.grantUserRole(grantDialog.userId, grantDialog.roleIds)
		ElMessage.success(t('user.msgGrantSuccess'))
		grantDialog.visible = false
	} finally {
		saving.value = false
	}
}

/* ── 重置密码 / 解锁 ───────────────────────── */
const pwdDialog = reactive({ visible: false, userId: 0 as number | string, newPassword: '' })

function openResetPwd(row: UserOutput): void {
	pwdDialog.userId = row.id
	pwdDialog.newPassword = ''
	pwdDialog.visible = true
}

async function onSavePwd(): Promise<void> {
	if (!pwdDialog.newPassword) {
		ElMessage.warning(t('user.msgNewPwdRequired'))
		return
	}
	saving.value = true
	try {
		await userApi.resetUserPwd(pwdDialog.userId, pwdDialog.newPassword)
		ElMessage.success(t('user.msgResetPwdSuccess'))
		pwdDialog.visible = false
	} finally {
		saving.value = false
	}
}

async function onUnlock(row: UserOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('user.msgUnlockConfirm', { account: row.account }), t('user.dlgUnlock'), { type: 'warning' })
	} catch {
		return
	}
	unlockingId.value = row.id
	try {
		await userApi.unlockUserLogin(row.account ?? '')
		ElMessage.success(t('user.msgUnlockSuccess'))
	} finally {
		unlockingId.value = null
	}
}

/** 操作列「更多」下拉分发(编辑/删除直出,其余折叠于此)。 */
function onRowCommand(cmd: unknown, row: UserOutput): void {
	switch (cmd) {
		case 'grant':
			void openGrant(row)
			break
		case 'resetPwd':
			openResetPwd(row)
			break
		case 'unlock':
			void onUnlock(row)
			break
	}
}

async function onDelete(row: UserOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('user.msgDeleteConfirm', { name: row.realName || row.account }), t('user.dlgDelete'), {
			type: 'warning'
		})
	} catch {
		return
	}
	deletingId.value = row.id
	try {
		await userApi.deleteUser(row.id)
		ElMessage.success(t('user.msgDeleteSuccess'))
		await fetchData()
	} finally {
		deletingId.value = null
	}
}

onMounted(async () => {
	void loadMeta()
	await ccLoad()
	ccApplyToGrid(gridRef.value)
	void fetchData()
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
.search-org {
	width: 240px;
}
.search-status {
	width: 130px;
}
.more-arrow {
	margin-left: 2px;
}

.full-width {
	width: 100%;
}

.dialog-hint {
	font-size: 12px;
	color: var(--ba-text-tertiary);
	margin: 0 0 12px;
	line-height: 1.6;
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
:deep(.st-super) {
	background: var(--ba-brand-soft);
	color: var(--ba-brand);
}
.col-settings-row {
	display: flex;
	align-items: center;
	gap: 10px;
	padding: 6px 4px;
	border-bottom: 1px solid var(--el-border-color-lighter);
}
.col-settings-row:last-child {
	border-bottom: none;
}
.col-name {
	flex: 1;
}
</style>
