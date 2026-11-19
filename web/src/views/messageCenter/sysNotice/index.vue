<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysNotice.title') }}</h3>
				<p class="ba-sub">{{ t('sysNotice.sub') }}</p>
			</div>
			<el-button v-perm="'sysNotice/add'" type="primary" @click="openAdd">
				<el-icon><Plus /></el-icon>{{ t('sysNotice.btnAdd') }}
			</el-button>
		</div>

		<!-- 数据卡 -->
		<div class="ba-card">
			<div class="search-row">
				<el-input
					v-model="query.title"
					:placeholder="t('sysNotice.searchPlaceholder')"
					clearable
					class="search-input"
					@keyup.enter="reload"
					@clear="reload"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
				<el-select v-model="query.type" class="search-select">
					<el-option :label="t('sysNotice.allTypes')" :value="0" />
					<el-option :label="t('sysNotice.typeNotice')" :value="1" />
					<el-option :label="t('sysNotice.typeAnnouncement')" :value="2" />
					<!-- 3 系统升级(4.11 升级公告以该类型承载;与后端 NoticeTypeEnum.Upgrade = 3 对齐) -->
					<el-option :label="t('sysNotice.typeUpgrade')" :value="3" />
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
				<template #cell_type="{ row }">
					<!-- 标签走 noticeTypeLabel:未知取值容错为「类型 N」(后端扩充枚举时不误标) -->
					<span class="st" :class="typeClass(row.type)">
						{{ noticeTypeLabel(row.type) }}
					</span>
				</template>
				<template #cell_status="{ row }">
					<span class="st" :class="row.status === 1 ? 'st-ok' : 'st-warn'">
						{{ row.status === 1 ? t('sysNotice.statusPublished') : t('sysNotice.statusDraft') }}
					</span>
				</template>
				<template #row_ops="{ row }">
					<el-button
						v-perm="'sysNotice/update'"
						link
						type="primary"
						size="small"
						:disabled="row.status === 1"
						@click="openEdit(row)"
					>
						{{ t('common.edit') }}
					</el-button>
					<el-button
						v-perm="'sysNotice/public'"
						link
						type="success"
						size="small"
						:loading="rowLoading(row, 'public')"
						:disabled="rowBusy(row)"
						@click="onPublic(row)"
					>
						{{ t('sysNotice.btnPublic') }}
					</el-button>
					<el-button
						v-perm="'sysNotice/delete'"
						link
						type="danger"
						size="small"
						:loading="rowLoading(row, 'delete')"
						:disabled="rowBusy(row) || row.status === 1"
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
			:title="dialog.mode === 'add' ? t('sysNotice.dlgAdd') : t('sysNotice.dlgEdit')"
			width="560px"
			destroy-on-close
		>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="84px">
				<el-form-item :label="t('sysNotice.colTitle')" prop="title">
					<el-input v-model="form.title" :placeholder="t('sysNotice.phTitle')" />
				</el-form-item>
				<el-form-item :label="t('sysNotice.colType')" prop="type">
					<el-select v-model="form.type" class="full-width">
						<el-option :label="t('sysNotice.typeNotice')" :value="1" />
						<el-option :label="t('sysNotice.typeAnnouncement')" :value="2" />
						<!-- 3 系统升级:登录后未读弹窗承载的升级公告类型(受配置开关 sys_upgrade 控制是否提示) -->
						<el-option :label="t('sysNotice.typeUpgrade')" :value="3" />
					</el-select>
				</el-form-item>
				<el-form-item :label="t('sysNotice.colContent')" prop="content">
					<el-input v-model="form.content" type="textarea" :rows="5" :placeholder="t('sysNotice.phContent')" />
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
	defineOptions({ name: 'SysNotice' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import * as noticeApi from '@/api/sys/notice'
import type { NoticeOutput } from '@/api/sys/notice'
import { usePaged } from '@/composables/usePaged'
import { formatDateTime } from '@/utils/format'

const { t } = useI18n()

type DateRange = [string, string] | null
/** 范围选择默认时刻:起 00:00:00,止 23:59:59(后端 CreateTime 闭区间) */
const defaultTime: [Date, Date] = [new Date(2000, 0, 1, 0, 0, 0), new Date(2000, 0, 1, 23, 59, 59)]

const query = reactive({
	title: '',
	type: 0,
	range: null as DateRange,
	orderBy: '' as string,
	desc: false as boolean
})
const { loading, rows, pager, fetchPage, reload, onPageChange } = usePaged<NoticeOutput>(q =>
	noticeApi.pageNotice({
		title: query.title || null,
		type: query.type,
		startDate: query.range?.[0] ?? null,
		endDate: query.range?.[1] ?? null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: query.orderBy || undefined,
		desc: query.orderBy ? query.desc : undefined
	})
)

const saving = ref(false)

/** 行级 pending:同行的发布/删除进行中即禁用该行按钮(防连点重复提交)。 */
const pendingRow = ref<number | string | null>(null)
const pendingAction = ref<'' | 'public' | 'delete'>('')

function rowBusy(row: NoticeOutput): boolean {
	return pendingRow.value === row.id
}

function rowLoading(row: NoticeOutput, action: 'public' | 'delete'): boolean {
	return pendingRow.value === row.id && pendingAction.value === action
}

async function withRowPending(
	row: NoticeOutput,
	action: 'public' | 'delete',
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
	query.title = ''
	query.type = 0
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

/** 类型标签映射(i18n 依赖当前语言,须 computed 以随语言切换重算;与后端 NoticeTypeEnum 对齐)。 */
const typeLabels = computed<Record<number, string>>(() => ({
	1: t('sysNotice.typeNotice'),
	2: t('sysNotice.typeAnnouncement'),
	3: t('sysNotice.typeUpgrade')
}))

/** 类型标签;未知取值容错为「类型 N」(后端扩充枚举值时前端不误标、不崩)。 */
function noticeTypeLabel(type: number): string {
	return typeLabels.value[type] ?? t('sysNotice.typeFallback', { type })
}

/** 类型标签色:1 通知=蓝 / 3 系统升级=橙(醒目) / 其余(2 公告、未知取值)沿用品牌软色。 */
function typeClass(type: number): string {
	if (type === 1) {
		return 'st-info'
	}
	if (type === 3) {
		return 'st-upgrade'
	}
	return 'st-super'
}

const columns = computed(() => [
	{ field: 'id', title: 'Id', width: 130, sortable: true },
	{ field: 'title', title: t('sysNotice.colTitle'), minWidth: 160, sortable: true, showOverflow: 'tooltip' },
	{ field: 'type', title: t('sysNotice.colType'), width: 90, sortable: true, slots: { default: 'cell_type' } },
	{ field: 'publicUserName', title: t('sysNotice.colPublisher'), width: 110, sortable: true },
	{
		field: 'publicTime',
		title: t('sysNotice.colPublicTime'),
		width: 170,
		sortable: true,
		formatter: ({ cellValue }: { cellValue: string | null }) => formatDateTime(cellValue)
	} as object,
	{ field: 'status', title: t('common.status'), width: 100, sortable: true, slots: { default: 'cell_status' } },
	{
		field: 'createTime',
		title: t('sysNotice.colCreateTime'),
		width: 170,
		sortable: true,
		formatter: ({ cellValue }: { cellValue: string | null }) => formatDateTime(cellValue)
	} as object,
	{ title: t('common.operations'), minWidth: 170, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

/* ── 新增/编辑 ─────────────────────────────── */
const dialog = reactive({ visible: false, mode: 'add' as 'add' | 'edit', id: 0 as number | string })
const formRef = ref<FormInstance>()
const form = reactive({ title: '', content: '', type: 1 })
const rules = computed<FormRules>(() => ({
	title: [{ required: true, message: t('sysNotice.ruleTitleRequired'), trigger: 'blur' }],
	content: [{ required: true, message: t('sysNotice.ruleContentRequired'), trigger: 'blur' }]
}))

function openAdd(): void {
	dialog.mode = 'add'
	dialog.visible = true
	Object.assign(form, { title: '', content: '', type: 1 })
}

function openEdit(row: NoticeOutput): void {
	dialog.mode = 'edit'
	dialog.id = row.id
	dialog.visible = true
	Object.assign(form, { title: row.title ?? '', content: row.content ?? '', type: row.type })
}

async function onSave(): Promise<void> {
	await formRef.value?.validate()
	saving.value = true
	try {
		if (dialog.mode === 'add') {
			await noticeApi.addNotice({ title: form.title, content: form.content, type: form.type })
		} else {
			await noticeApi.updateNotice({ id: dialog.id, title: form.title, content: form.content, type: form.type })
		}
		ElMessage.success(t('sysNotice.msgSaved'))
		dialog.visible = false
		void fetchPage()
	} finally {
		saving.value = false
	}
}

/* ── 发布 / 删除 ───────────────────────────── */
async function onPublic(row: NoticeOutput): Promise<void> {
	await withRowPending(row, 'public', async () => {
		try {
			await ElMessageBox.confirm(
				t('sysNotice.msgPublicConfirm', { name: row.title }),
				t('sysNotice.msgPublicTitle'),
				{ type: 'warning' }
			)
		} catch {
			return
		}
		await noticeApi.publicNotice(row.id)
		ElMessage.success(t('sysNotice.msgPublished'))
		void fetchPage()
	})
}

async function onDelete(row: NoticeOutput): Promise<void> {
	await withRowPending(row, 'delete', async () => {
		try {
			await ElMessageBox.confirm(
				t('sysNotice.msgDeleteConfirm', { name: row.title }),
				t('sysNotice.msgDeleteTitle'),
				{ type: 'warning' }
			)
		} catch {
			return
		}
		await noticeApi.deleteNotice(row.id)
		ElMessage.success(t('sysNotice.msgDeleted'))
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
.search-select {
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
:deep(.st-warn) {
	background: rgb(245 158 11 / 12%);
	color: #d97706;
}
:deep(.st-info) {
	background: rgb(59 130 246 / 12%);
	color: #2563eb;
}
:deep(.st-super) {
	background: var(--ba-brand-soft);
	color: var(--ba-brand);
}
:deep(.st-upgrade) {
	background: rgb(245 158 11 / 12%);
	color: #d97706;
}
</style>