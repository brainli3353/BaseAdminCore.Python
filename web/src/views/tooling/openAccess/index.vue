<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('openAccess.title') }}</h3>
				<p class="ba-sub">{{ t('openAccess.sub') }}</p>
			</div>
			<el-button v-perm="'sysOpenAccess/add'" type="primary" @click="openAdd">
				<el-icon><Plus /></el-icon>{{ t('openAccess.btnAdd') }}
			</el-button>
		</div>

		<!-- 数据卡 -->
		<div class="ba-card">
			<div class="search-row">
				<el-input
					v-model="query.accessKey"
					:placeholder="t('openAccess.searchPlaceholder')"
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
				@page-change="onPageChange"
			>
				<template #row_ops="{ row }">
					<el-button v-perm="'sysOpenAccess/update'" link type="primary" size="small" @click="openEdit(row)">
						{{ t('openAccess.btnEditBind') }}
					</el-button>
					<el-button v-perm="'sysOpenAccess/resetSecret'" link type="warning" size="small" @click="onResetSecret(row)">
						{{ t('openAccess.btnResetSecret') }}
					</el-button>
					<el-button v-perm="'sysOpenAccess/delete'" link type="danger" size="small" @click="onDelete(row)">
						{{ t('common.delete') }}
					</el-button>
				</template>
			</vxe-grid>
		</div>

		<!-- 新增/编辑绑定对话框 -->
		<el-dialog
			v-model="dialog.visible"
			:title="dialog.mode === 'add' ? t('openAccess.btnAdd') : t('openAccess.btnEditBind')"
			width="480px"
			destroy-on-close
		>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
				<el-form-item v-if="dialog.mode === 'add'" label="AccessKey" prop="accessKey">
					<el-input v-model="form.accessKey" :placeholder="t('openAccess.phAccessKey')" />
				</el-form-item>
				<el-form-item v-else label="AccessKey">
					<el-input :model-value="dialog.accessKey" disabled />
				</el-form-item>
				<el-form-item :label="t('openAccess.labelBindUser')" prop="bindUserId">
					<el-select
						v-model="form.bindUserId"
						filterable
						remote
						:remote-method="searchUsers"
						:loading="userLoading"
						:placeholder="t('openAccess.phBindUser')"
						class="full-width"
					>
						<el-option v-for="u in userOptions" :key="String(u.id)" :label="userLabel(u)" :value="u.id" />
					</el-select>
				</el-form-item>
				<el-form-item :label="t('openAccess.labelBindTenant')" prop="bindTenantId">
					<el-select
						v-model="form.bindTenantId"
						filterable
						remote
						:remote-method="searchTenants"
						:loading="tenantLoading"
						:placeholder="t('openAccess.phBindTenant')"
						class="full-width"
					>
						<el-option v-for="t in tenantOptions" :key="String(t.id)" :label="t.name ?? undefined" :value="t.id" />
					</el-select>
				</el-form-item>
				<p v-if="dialog.mode === 'add'" class="dialog-hint">{{ t('openAccess.hintSecretAuto') }}</p>
			</el-form>
			<template #footer>
				<el-button @click="dialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSave">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>

		<!-- 密钥一次性展示对话框 -->
		<el-dialog v-model="secretDialog.visible" :title="secretDialog.title" width="540px">
			<el-alert
				type="warning"
				show-icon
				:closable="false"
				:title="t('openAccess.msgSecretOnce')"
				class="secret-alert"
			/>
			<div class="secret-row">
				<span class="secret-key">{{ secretDialog.secret }}</span>
				<el-button link type="primary" @click="copySecret">{{ t('openAccess.btnCopy') }}</el-button>
			</div>
			<template #footer>
				<el-button type="primary" @click="secretDialog.visible = false">{{ t('openAccess.btnSaved') }}</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'OpenAccess' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import * as openApi from '@/api/sys/openAccess'
import type { OpenAccessOutput } from '@/api/sys/openAccess'
import * as userApi from '@/api/sys/user'
import type { UserOutput } from '@/api/sys/user'
import * as tenantApi from '@/api/sys/tenant'
import type { TenantOutput } from '@/api/sys/tenant'
import { usePaged } from '@/composables/usePaged'
import { formatDateTime } from '@/utils/format'

const { t } = useI18n()

const userOptions = ref<UserOutput[]>([])
const tenantOptions = ref<TenantOutput[]>([])
/** 远程搜索中的加载态(供下拉显示 loading) */
const userLoading = ref(false)
const tenantLoading = ref(false)

type DateRange = [string, string] | null
/** 范围选择默认时刻:起 00:00:00,止 23:59:59(后端 CreateTime 闭区间) */
const defaultTime: [Date, Date] = [new Date(2000, 0, 1, 0, 0, 0), new Date(2000, 0, 1, 23, 59, 59)]

const query = reactive({ accessKey: '', range: null as DateRange })
const { loading, rows, pager, fetchPage, reload, onPageChange } = usePaged<OpenAccessOutput>(q =>
	openApi.pageOpenAccess({
		accessKey: query.accessKey || null,
		startDate: query.range?.[0] ?? null,
		endDate: query.range?.[1] ?? null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number
	})
)

const saving = ref(false)

function doReset(): void {
	query.accessKey = ''
	query.range = null
	reload()
}

const columns = computed(() => [
	{ field: 'id', title: 'Id', width: 130, sortable: true },
	{ field: 'accessKey', title: 'AccessKey', minWidth: 170, sortable: true },
	{ field: 'bindUserAccount', title: t('openAccess.colBindUser'), width: 130, sortable: true },
	{ field: 'bindTenantName', title: t('openAccess.colBindTenant'), width: 130, sortable: true },
	{ field: 'createTime', title: t('openAccess.colCreateTime'), width: 170, sortable: true, formatter: ({ cellValue }: { cellValue: string | null }) => formatDateTime(cellValue) },
	{ field: 'updateTime', title: t('openAccess.colUpdateTime'), width: 170, sortable: true, formatter: ({ cellValue }: { cellValue: string | null }) => formatDateTime(cellValue) },
	{ title: t('common.operations'), minWidth: 200, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

/** 300ms 防抖:远程下拉输入时避免每敲一键发一次请求 */
function debounce<A extends unknown[]>(fn: (...args: A) => unknown, wait: number): (...args: A) => void {
	let timer: ReturnType<typeof setTimeout> | null = null
	return (...args: A): void => {
		if (timer) clearTimeout(timer)
		timer = setTimeout(() => {
			void fn(...args)
		}, wait)
	}
}

/** 用户下拉:按 Account 模糊,pageSize 50(不再一次性拉 200) */
async function loadUsers(keyword: string): Promise<void> {
	userLoading.value = true
	try {
		const res = await userApi.pageUser({ account: keyword || null, pageIndex: 1, pageSize: 50 })
		userOptions.value = res.list
	} finally {
		userLoading.value = false
	}
}

/** 租户下拉:按 Name 模糊,pageSize 50 */
async function loadTenants(keyword: string): Promise<void> {
	tenantLoading.value = true
	try {
		const res = await tenantApi.pageTenant({ name: keyword || null, pageIndex: 1, pageSize: 50 })
		tenantOptions.value = res.list
	} finally {
		tenantLoading.value = false
	}
}

const searchUsers = debounce(loadUsers, 300)
const searchTenants = debounce(loadTenants, 300)

/** 打开对话框时的初始候选(各 50 条);失败必须可见,不静默吞 */
async function loadMeta(): Promise<void> {
	try {
		await Promise.all([loadUsers(''), loadTenants('')])
	} catch {
		ElMessage.error(t('common.loadError'))
	}
}

function userLabel(u: UserOutput): string {
	return u.realName ? `${u.account}(${u.realName})` : `${u.account}`
}

/* ── 新增/编辑绑定 ─────────────────────────── */
const dialog = reactive({
	visible: false,
	mode: 'add' as 'add' | 'edit',
	id: 0 as number | string,
	accessKey: ''
})
const formRef = ref<FormInstance>()
const form = reactive({
	accessKey: '',
	bindUserId: null as number | string | null,
	bindTenantId: null as number | string | null
})
const rules = computed<FormRules>(() => ({
	accessKey: [{ required: true, message: t('openAccess.ruleAccessKey'), trigger: 'blur' }],
	bindUserId: [{ required: true, message: t('openAccess.ruleBindUser'), trigger: 'change' }],
	bindTenantId: [{ required: true, message: t('openAccess.ruleBindTenant'), trigger: 'change' }]
}))

function openAdd(): void {
	dialog.mode = 'add'
	dialog.visible = true
	Object.assign(form, { accessKey: '', bindUserId: null, bindTenantId: null })
}

function openEdit(row: OpenAccessOutput): void {
	dialog.mode = 'edit'
	dialog.id = row.id
	dialog.accessKey = row.accessKey
	dialog.visible = true
	Object.assign(form, { accessKey: row.accessKey, bindUserId: row.bindUserId, bindTenantId: row.bindTenantId })
	// 回显:按已绑定账号/租户名回查候选,否则下拉只剩 id 无可读标签(失败可见)
	void loadUsers(row.bindUserAccount ?? '').catch(() => ElMessage.error(t('common.loadError')))
	void loadTenants(row.bindTenantName ?? '').catch(() => ElMessage.error(t('common.loadError')))
}

async function onSave(): Promise<void> {
	await formRef.value?.validate()
	saving.value = true
	try {
		if (dialog.mode === 'add') {
			const res = await openApi.addOpenAccess({
				accessKey: form.accessKey,
				bindUserId: form.bindUserId as number | string,
				bindTenantId: form.bindTenantId as number | string
			})
			dialog.visible = false
			void fetchPage()
			showSecret(t('openAccess.titleSecretAdd'), res.accessSecret)
		} else {
			await openApi.updateOpenAccess({
				id: dialog.id,
				bindUserId: form.bindUserId as number | string,
				bindTenantId: form.bindTenantId as number | string
			})
			ElMessage.success(t('openAccess.msgBindUpdated'))
			dialog.visible = false
			void fetchPage()
		}
	} finally {
		saving.value = false
	}
}

/* ── 密钥一次性展示 ────────────────────────── */
const secretDialog = reactive({ visible: false, title: '', secret: '' })

function showSecret(title: string, secret: string): void {
	secretDialog.title = title
	secretDialog.secret = secret
	secretDialog.visible = true
}

async function copySecret(): Promise<void> {
	try {
		await navigator.clipboard.writeText(secretDialog.secret)
		ElMessage.success(t('openAccess.msgCopied'))
	} catch {
		ElMessage.warning(t('openAccess.msgCopyFailed'))
	}
}

async function onResetSecret(row: OpenAccessOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(
			t('openAccess.msgResetSecretConfirm', { name: row.accessKey }),
			t('openAccess.resetConfirmTitle'),
			{ type: 'warning' }
		)
	} catch {
		return
	}
	const secret = await openApi.resetOpenAccessSecret(row.id)
	showSecret(t('openAccess.titleSecretReset'), secret)
}

async function onDelete(row: OpenAccessOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('openAccess.msgDeleteConfirm', { name: row.accessKey }), t('openAccess.deleteConfirmTitle'), {
			type: 'warning'
		})
	} catch {
		return
	}
	await openApi.deleteOpenAccess(row.id)
	ElMessage.success(t('openAccess.msgDeleted'))
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
	max-width: 280px;
}
.search-date {
	max-width: 360px;
}

.full-width {
	width: 100%;
}

.dialog-hint {
	font-size: 12px;
	color: var(--ba-text-tertiary);
	margin: 0;
	line-height: 1.6;
}

.secret-alert {
	margin-bottom: 14px;
}
.secret-row {
	display: flex;
	align-items: center;
	gap: 10px;
}
.secret-key {
	flex: 1;
	font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
	font-size: 14px;
	font-weight: 600;
	background: rgb(0 0 0 / 4%);
	border-radius: 6px;
	padding: 8px 12px;
	word-break: break-all;
	user-select: all;
}
</style>