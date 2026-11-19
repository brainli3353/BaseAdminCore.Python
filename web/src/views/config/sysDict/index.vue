<template>
	<div class="ba-page">
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysDict.title') }}</h3>
				<p class="ba-sub">{{ t('sysDict.sub') }}</p>
			</div>
			<el-button v-perm="'sysDictType/add'" type="primary" @click="openTypeAdd">
				<el-icon><Plus /></el-icon>{{ t('sysDict.btnAddType') }}
			</el-button>
		</div>

		<!-- 字典类型 -->
		<div class="ba-card">
			<div class="section-title">{{ t('sysDict.cardType') }}</div>
			<div class="search-row">
				<el-input
					v-model="typeQuery.keyword"
					:placeholder="t('common.phKeyword')"
					clearable
					class="search-input"
					@keyup.enter="reloadTypes"
					@clear="reloadTypes"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
				<el-button type="primary" @click="reloadTypes">{{ t('common.search') }}</el-button>
			</div>
			<vxe-grid
				:loading="typeLoading"
				:data="typeRows"
				:columns="typeColumns"
				:pager-config="typePager"
				:row-config="{ keyField: 'id' }"
				:radio-config="{ highlight: true }"
				:sort-config="{ remote: true }"
				@page-change="onTypePageChange"
				@sort-change="onTypeSortChange"
				@cell-click="onTypeRowClick"
			>
				<template #cell_enum="{ row }">
					<span v-if="row.isEnum" class="st st-super">{{ t('common.yes') }}</span>
					<span v-else>-</span>
				</template>
				<template #row_type_ops="{ row }">
					<el-button v-perm="'sysDictType/update'" link type="primary" size="small" @click.stop="openTypeEdit(row)">
						{{ t('common.edit') }}
					</el-button>
					<el-button v-perm="'sysDictType/delete'" link type="danger" size="small" @click.stop="onDeleteType(row)">
						{{ t('common.delete') }}
					</el-button>
				</template>
			</vxe-grid>
		</div>

		<!-- 字典值 -->
		<div class="ba-card" style="margin-top: 14px">
			<div class="section-title">
				{{ t('sysDict.cardData') }}
				<span class="section-hint">
					{{ selectedType ? t('sysDict.currentType', { code: selectedType.code }) : t('sysDict.selectTypeHint') }}
				</span>
				<el-button v-perm="'sysDictData/add'" type="primary" size="small" :disabled="!selectedType" @click="openDataAdd">
					<el-icon><Plus /></el-icon>{{ t('sysDict.btnAddValue') }}
				</el-button>
			</div>
			<div class="search-row">
				<el-input
					v-model="dataQuery.keyword"
					:placeholder="t('common.phKeyword')"
					clearable
					class="search-input"
					@keyup.enter="reloadData"
					@clear="reloadData"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
				<el-button type="primary" @click="reloadData">{{ t('common.search') }}</el-button>
			</div>
			<vxe-grid
				:loading="dataLoading"
				:data="dataRows"
				:columns="dataColumns"
				:pager-config="dataPager"
				:row-config="{ keyField: 'id' }"
				:sort-config="{ remote: true }"
				@page-change="onDataPageChange"
				@sort-change="onDataSortChange"
			>
				<template #cell_value="{ row }">
					<el-tag :type="tagTypeOf(row)" disable-transitions size="small">{{ row.label }}</el-tag>
				</template>
				<template #cell_isEnable="{ row }">
					<el-tag :type="row.isEnable ? 'success' : 'info'" disable-transitions size="small">
						{{ row.isEnable ? t('sysDict.statusEnabled') : t('sysDict.statusDisabled') }}
					</el-tag>
				</template>
				<template #row_data_ops="{ row }">
					<el-button
						v-perm="'sysDictData/updateStatus'"
						link
						:type="row.isEnable ? 'warning' : 'success'"
						size="small"
						:loading="togglingId === row.id"
						:disabled="togglingId === row.id"
						@click="onToggleStatus(row)"
					>
						{{ row.isEnable ? t('sysDict.statusDisabled') : t('sysDict.statusEnabled') }}
					</el-button>
					<el-button v-perm="'sysDictData/update'" link type="primary" size="small" @click="openDataEdit(row)">
						{{ t('common.edit') }}
					</el-button>
					<el-button v-perm="'sysDictData/delete'" link type="danger" size="small" @click="onDeleteData(row)">
						{{ t('common.delete') }}
					</el-button>
				</template>
			</vxe-grid>
		</div>

		<!-- 类型对话框 -->
		<el-dialog v-model="typeDialog.visible" :title="typeDialog.mode === 'add' ? t('sysDict.dlgTypeAdd') : t('sysDict.dlgTypeEdit')" width="440px" destroy-on-close>
			<el-form label-width="72px">
				<el-form-item :label="t('sysDict.labelName')">
					<el-input v-model="typeForm.name" :placeholder="t('sysDict.phName')" />
				</el-form-item>
				<el-form-item :label="t('sysDict.labelCode')">
					<el-input v-if="typeDialog.mode === 'add'" v-model="typeForm.code" :placeholder="t('sysDict.phCodeType')" />
					<el-input v-else :model-value="typeForm.code" disabled />
				</el-form-item>
				<el-form-item :label="t('sysDict.labelIsEnum')">
					<el-switch v-model="typeForm.isEnum" />
				</el-form-item>
				<el-form-item :label="t('common.remark')">
					<el-input v-model="typeForm.remark" :placeholder="t('sysDict.phRemarkOptional')" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="typeDialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSaveType">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>

		<!-- 值对话框 -->
		<el-dialog v-model="dataDialog.visible" :title="dataDialog.mode === 'add' ? t('sysDict.dlgDataAdd') : t('sysDict.dlgDataEdit')" width="480px" destroy-on-close>
			<el-form label-width="72px">
				<el-form-item :label="t('sysDict.labelTypeName')">
					<el-input :model-value="dataDialog.typeLabel" disabled />
				</el-form-item>
				<el-form-item :label="t('sysDict.labelLabel')">
					<el-input v-model="dataForm.label" :placeholder="t('sysDict.phLabel')" />
				</el-form-item>
				<el-form-item :label="t('sysDict.labelValue')">
					<el-input v-model="dataForm.value" :placeholder="t('sysDict.phValue')" />
				</el-form-item>
				<el-form-item :label="t('sysDict.labelCode')">
					<el-input v-model="dataForm.code" :placeholder="t('sysDict.phCodeData')" />
				</el-form-item>
				<el-form-item :label="t('sysDict.labelTagType')">
					<el-select v-model="dataForm.tagType" class="full-width">
						<el-option :value="1" label="primary" />
						<el-option :value="2" label="success" />
						<el-option :value="3" label="warning" />
						<el-option :value="4" label="danger" />
						<el-option :value="5" label="info" />
					</el-select>
				</el-form-item>
				<el-form-item :label="t('sysDict.labelOrderNo')">
					<el-input-number v-model="dataForm.orderNo" :min="0" :max="9999" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dataDialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSaveData">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'SysDict' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import * as dictApi from '@/api/sys/dict'
import type { DictTypeOutput, DictDataOutput } from '@/api/sys/dict'
import { usePaged } from '@/composables/usePaged'

const { t } = useI18n()

const typeQuery = reactive({ keyword: '', orderBy: '' as string, desc: false as boolean })
const dataQuery = reactive({ keyword: '', orderBy: '' as string, desc: false as boolean })

const { loading: typeLoading, rows: typeRows, pager: typePager, fetchPage: fetchTypes, reload: reloadTypes, onPageChange: onTypePageChange } =
	usePaged<DictTypeOutput>(q =>
		dictApi.pageDictType({
			keyword: typeQuery.keyword || null,
			pageIndex: q.pageIndex as number,
			pageSize: q.pageSize as number,
			orderBy: typeQuery.orderBy || undefined,
			desc: typeQuery.orderBy ? typeQuery.desc : undefined
		})
	)

const { loading: dataLoading, rows: dataRows, pager: dataPager, params: dataParams, fetchPage: fetchData, reload: reloadData, onPageChange: onDataPageChange } =
	usePaged<DictDataOutput>(q =>
		dictApi.pageDictData({
			dictTypeId: (q.dictTypeId as number | string) ?? null,
			keyword: dataQuery.keyword || null,
			pageIndex: q.pageIndex as number,
			pageSize: q.pageSize as number,
			orderBy: dataQuery.orderBy || undefined,
			desc: dataQuery.orderBy ? dataQuery.desc : undefined
		})
	)

const selectedType = ref<DictTypeOutput | null>(null)
const saving = ref(false)
/** 值区启停逐行 pending:同一时刻只允许一行在途,该行按钮 loading+禁用(防连点重复提交)。 */
const togglingId = ref<number | string | null>(null)

function onTypeSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	typeQuery.orderBy = order ? property : ''
	typeQuery.desc = order === 'desc'
	reloadTypes()
}

function onDataSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	dataQuery.orderBy = order ? property : ''
	dataQuery.desc = order === 'desc'
	reloadData()
}

const typeColumns = computed(() => [
	{ field: 'name', title: t('sysDict.colName'), minWidth: 140, sortable: true },
	{ field: 'code', title: t('sysDict.colCode'), minWidth: 140, sortable: true },
	{ field: 'isEnum', title: t('sysDict.colIsEnum'), width: 90, sortable: true, slots: { default: 'cell_enum' } },
	{ field: 'remark', title: t('common.remark'), minWidth: 180, sortable: true, showOverflow: 'tooltip' as const },
	{ title: t('common.operations'), width: 150, fixed: 'right' as const, slots: { default: 'row_type_ops' } }
])

const dataColumns = computed(() => [
	{ field: 'label', title: t('sysDict.colLabel'), minWidth: 120, sortable: true, showOverflow: 'tooltip' as const, slots: { default: 'cell_value' } },
	{ field: 'value', title: t('sysDict.colValue'), minWidth: 100, sortable: true, showOverflow: 'tooltip' as const },
	{ field: 'code', title: t('sysDict.colCode'), minWidth: 120, sortable: true, showOverflow: 'tooltip' as const },
	{ field: 'orderNo', title: t('sysDict.colOrderNo'), width: 80, sortable: true },
	{ field: 'isEnable', title: t('common.status'), width: 90, sortable: true, slots: { default: 'cell_isEnable' } },
	{ title: t('common.operations'), minWidth: 200, fixed: 'right' as const, slots: { default: 'row_data_ops' } }
])

const TAG_MAP: Record<number, '' | 'success' | 'warning' | 'danger' | 'info'> = {
	1: '',
	2: 'success',
	3: 'warning',
	4: 'danger',
	5: 'info'
}
/* 批B6：'' 是 EP 历史默认值（TAG_MAP 的 1: ''），按需加载后 el-tag 的 type 不再接受；此处只收口类型，运行时仍传 '' */
function tagTypeOf(row: DictDataOutput): 'success' | 'warning' | 'danger' | 'info' {
	return (TAG_MAP[row.tagType] ?? 'info') as 'success' | 'warning' | 'danger' | 'info'
}

function onTypeRowClick({ row }: { row: DictTypeOutput }): void {
	selectedType.value = row
	dataParams.dictTypeId = row.id
	void reloadData()
}

/* ── 类型 ─────────────────────────────────── */
const typeDialog = reactive({ visible: false, mode: 'add' as 'add' | 'edit', id: 0 as number | string })
const typeForm = reactive({ id: 0 as number | string, name: '', code: '', isEnum: false, remark: '' })

function openTypeAdd(): void {
	typeDialog.mode = 'add'
	typeDialog.visible = true
	Object.assign(typeForm, { id: 0, name: '', code: '', isEnum: false, remark: '' })
}

function openTypeEdit(row: DictTypeOutput): void {
	typeDialog.mode = 'edit'
	typeDialog.id = row.id
	typeDialog.visible = true
	Object.assign(typeForm, { id: row.id, name: row.name ?? '', code: row.code ?? '', isEnum: row.isEnum, remark: row.remark ?? '' })
}

async function onSaveType(): Promise<void> {
	if (!typeForm.name || (typeDialog.mode === 'add' && !typeForm.code)) {
		ElMessage.warning(t('sysDict.msgNameCodeRequired'))
		return
	}
	saving.value = true
	try {
		if (typeDialog.mode === 'add') {
			await dictApi.addDictType({ name: typeForm.name, code: typeForm.code, isEnum: typeForm.isEnum, remark: typeForm.remark || undefined })
		} else {
			await dictApi.updateDictType({ id: typeForm.id, name: typeForm.name, isEnum: typeForm.isEnum, remark: typeForm.remark || undefined })
		}
		ElMessage.success(t('sysDict.msgSaved'))
		typeDialog.visible = false
		void reloadTypes()
	} finally {
		saving.value = false
	}
}

async function onDeleteType(row: DictTypeOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('sysDict.msgDeleteTypeConfirm', { name: row.name }), t('sysDict.msgDeleteTitle'), { type: 'warning' })
	} catch {
		return
	}
	await dictApi.deleteDictType(row.id)
	ElMessage.success(t('sysDict.msgDeleted'))
	if (selectedType.value?.id === row.id) {
		selectedType.value = null
		dataParams.dictTypeId = null
		void reloadData()
	}
	void reloadTypes()
}

/* ── 值 ───────────────────────────────────── */
const dataDialog = reactive({ visible: false, mode: 'add' as 'add' | 'edit', id: 0 as number | string, typeId: 0 as number | string, typeLabel: '' })
// isEnum 不在表单可见字段里,但值更新是全量提交(服务端 TagType/OrderNo/IsEnum 等缺省值覆盖):
// 编辑路径必须原样回传行内 isEnum(批 BO D2)——种子值 IsEnum=true(业务枚举消费标记),
// 若编辑时按缺省 false 提交,枚举标记会被静默重置
const dataForm = reactive({ id: 0 as number | string, label: '', value: '', code: '', tagType: 1, orderNo: 0, isEnum: false })

function openDataAdd(): void {
	if (!selectedType.value) {
		ElMessage.warning(t('sysDict.msgSelectTypeFirst'))
		return
	}
	dataDialog.mode = 'add'
	dataDialog.typeId = selectedType.value.id
	dataDialog.typeLabel = selectedType.value.code ?? ''
	dataDialog.visible = true
	Object.assign(dataForm, { id: 0, label: '', value: '', code: '', tagType: 1, orderNo: 0, isEnum: false })
}

function openDataEdit(row: DictDataOutput): void {
	dataDialog.mode = 'edit'
	dataDialog.id = row.id
	dataDialog.typeId = row.dictTypeId
	dataDialog.typeLabel = selectedType.value?.code ?? String(row.dictTypeId)
	dataDialog.visible = true
	Object.assign(dataForm, { id: row.id, label: row.label ?? '', value: row.value ?? '', code: row.code ?? '', tagType: row.tagType, orderNo: row.orderNo, isEnum: row.isEnum })
}

async function onSaveData(): Promise<void> {
	if (!dataForm.label || !dataForm.value || !dataForm.code) {
		ElMessage.warning(t('sysDict.msgLabelValueCodeRequired'))
		return
	}
	saving.value = true
	try {
		const base = { code: dataForm.code, value: dataForm.value, label: dataForm.label, tagType: dataForm.tagType, orderNo: dataForm.orderNo, isEnum: dataForm.isEnum }
		if (dataDialog.mode === 'add') {
			await dictApi.addDictData({ dictTypeId: dataDialog.typeId, ...base })
		} else {
			await dictApi.updateDictData({ id: dataForm.id, ...base })
		}
		ElMessage.success(t('sysDict.msgSaved'))
		dataDialog.visible = false
		void reloadData()
	} finally {
		saving.value = false
	}
}

async function onToggleStatus(row: DictDataOutput): Promise<void> {
	// P0:停用/启用属值区可见性变更,切换前必须二次确认(文案指名标签名,防误点整行状态)
	try {
		await ElMessageBox.confirm(
			row.isEnable ? t('sysDict.msgDisableConfirm', { label: row.label }) : t('sysDict.msgEnableConfirm', { label: row.label }),
			row.isEnable ? t('sysDict.msgDisableTitle') : t('sysDict.msgEnableTitle'),
			{ type: 'warning' }
		)
	} catch {
		return
	}
	togglingId.value = row.id
	try {
		await dictApi.updateDictDataStatus(row.id, !row.isEnable)
		ElMessage.success(row.isEnable ? t('sysDict.msgDisabled') : t('sysDict.msgEnabled'))
		void reloadData()
	} finally {
		togglingId.value = null
	}
}

async function onDeleteData(row: DictDataOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(t('sysDict.msgDeleteDataConfirm', { label: row.label }), t('sysDict.msgDeleteTitle'), { type: 'warning' })
	} catch {
		return
	}
	await dictApi.deleteDictData(row.id)
	ElMessage.success(t('sysDict.msgDeleted'))
	void reloadData()
}

onMounted(() => {
	// 类型区 + 全量值区(默认不按类型过滤)
	void fetchTypes()
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
.full-width {
	width: 100%;
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