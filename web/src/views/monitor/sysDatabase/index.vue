<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysDatabase.title') }}</h3>
				<p class="ba-sub">{{ t('sysDatabase.sub') }}</p>
			</div>
			<el-button v-if="canTables" :loading="loadingTables" @click="loadTables">
				<el-icon><Refresh /></el-icon>{{ t('sysDatabase.refresh') }}
			</el-button>
		</div>

		<!-- 表清单(未授权:不请求也不渲染) -->
		<div v-if="canTables" v-perm="'sysDatabase/tables'" class="ba-card">
			<div class="section-title">
				{{ t('sysDatabase.tabTables') }}
				<span class="section-hint">{{ t('sysDatabase.tablesHint') }}</span>
			</div>
			<div class="search-row">
				<el-input
					v-model="keyword"
					:placeholder="t('sysDatabase.searchPlaceholder')"
					clearable
					class="search-input"
					@keyup.enter="loadTables"
					@clear="loadTables"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
				<el-button type="primary" @click="loadTables">{{ t('common.search') }}</el-button>
				<el-button @click="doReset">{{ t('common.reset') }}</el-button>
			</div>
			<vxe-grid
				:loading="loadingTables"
				:data="tables"
				:columns="tableColumns"
				:row-config="{ keyField: 'tableName' }"
				:radio-config="{ highlight: true }"
				@cell-click="onTableRowClick"
			/>
		</div>

		<!-- 列结构 -->
		<div v-if="canColumns" v-perm="'sysDatabase/columns'" class="ba-card card-gap">
			<div class="section-title">
				{{ t('sysDatabase.tabColumns') }}
				<span class="section-hint">{{ selectedTable ? t('sysDatabase.currentTable', { name: selectedTable.tableName }) : t('sysDatabase.selectTableHint') }}</span>
			</div>
			<vxe-grid
				v-if="selectedTable"
				:loading="loadingColumns"
				:data="columns"
				:columns="columnColumns"
				:row-config="{ keyField: 'columnName' }"
			>
				<template #col_nullable="{ row }">{{ row.isNullable ? t('sysDatabase.nullable') : t('sysDatabase.notNullable') }}</template>
				<template #col_maxlen="{ row }">{{ row.maxLength ?? '—' }}</template>
				<template #col_pk="{ row }">
					<span v-if="row.isPrimaryKey" class="st st-key">{{ t('sysDatabase.primaryKey') }}</span>
					<span v-else>—</span>
				</template>
			</vxe-grid>
			<BaEmpty v-else :message="t('sysDatabase.emptySelectTable')" />
		</div>

		<!-- 索引 -->
		<div v-if="canIndexes" v-perm="'sysDatabase/indexes'" class="ba-card card-gap">
			<div class="section-title">
				{{ t('sysDatabase.tabIndexes') }}
				<span class="section-hint">{{ selectedTable ? t('sysDatabase.currentTable', { name: selectedTable.tableName }) : t('sysDatabase.selectTableHint') }}</span>
			</div>
			<vxe-grid
				v-if="selectedTable"
				:loading="loadingIndexes"
				:data="indexes"
				:columns="indexColumns"
				:row-config="{ keyField: 'indexName' }"
			>
				<template #idx_unique="{ row }">
					<span v-if="row.isUnique" class="st st-key">{{ t('sysDatabase.unique') }}</span>
					<span v-else>—</span>
				</template>
				<template #idx_pk="{ row }">
					<span v-if="row.isPrimary" class="st st-key">{{ t('sysDatabase.primaryKey') }}</span>
					<span v-else>—</span>
				</template>
			</vxe-grid>
			<BaEmpty v-else :message="t('sysDatabase.emptySelectTable')" />
		</div>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'SysDatabase' })

import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Refresh, Search } from '@element-plus/icons-vue'
import BaEmpty from '@/components/BaEmpty.vue'
import * as databaseApi from '@/api/sys/database'
import type { DbTableOutput, DbColumnOutput, DbIndexOutput } from '@/api/sys/database'
import { useMenuStore } from '@/stores/menu'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()

const menuStore = useMenuStore()
const userStore = useUserStore()

/** 与 v-perm 同口径(超管直通):未授权分块既不渲染也不请求(v-perm 只摘 DOM,拦不住 mounted 拉数)。 */
function hasPerm(key: string): boolean {
	return userStore.user?.accountType === 999 || menuStore.permissions.includes(key)
}
const canTables = hasPerm('sysDatabase/tables')
const canColumns = hasPerm('sysDatabase/columns')
const canIndexes = hasPerm('sysDatabase/indexes')

/* ── 表清单 ─────────────────────────────── */
const keyword = ref('')
const tables = ref<DbTableOutput[]>([])
const loadingTables = ref(false)
const selectedTable = ref<DbTableOutput | null>(null)

/* ── 列结构 ─────────────────────────────── */
const columns = ref<DbColumnOutput[]>([])
const loadingColumns = ref(false)

/* ── 索引 ─────────────────────────────── */
const indexes = ref<DbIndexOutput[]>([])
const loadingIndexes = ref(false)

/** 选中表消失时联动清空下方两块,避免展示已不在列表中的表。 */
function clearSelection(): void {
	selectedTable.value = null
	columns.value = []
	indexes.value = []
}

/** 拉表清单(失败由全局拦截器提示,此处不 catch)。 */
async function loadTables(): Promise<void> {
	if (!canTables) return
	loadingTables.value = true
	try {
		tables.value = await databaseApi.listDbTables(keyword.value || null)
		// 选中表可能已被关键字过滤掉:仍在列表则保留选中,否则清空
		const stillThere = !!selectedTable.value && tables.value.some(t => t.tableName === selectedTable.value?.tableName)
		if (!stillThere) {
			clearSelection()
		}
	} finally {
		loadingTables.value = false
	}
}

function doReset(): void {
	keyword.value = ''
	void loadTables()
}

async function loadColumns(tableName: string): Promise<void> {
	if (!canColumns) return
	loadingColumns.value = true
	try {
		columns.value = await databaseApi.listDbColumns(tableName)
	} finally {
		loadingColumns.value = false
	}
}

async function loadIndexes(tableName: string): Promise<void> {
	if (!canIndexes) return
	loadingIndexes.value = true
	try {
		indexes.value = await databaseApi.listDbIndexes(tableName)
	} finally {
		loadingIndexes.value = false
	}
}

/** 点行选中:选中表变化即重新拉列与索引。 */
function onTableRowClick({ row }: { row: DbTableOutput }): void {
	if (selectedTable.value?.tableName === row.tableName) return
	selectedTable.value = row
	void loadColumns(row.tableName)
	void loadIndexes(row.tableName)
}

const tableColumns = computed(() => [
	{ field: 'tableName', title: t('sysDatabase.colTableName'), minWidth: 200, sortable: true },
	{ field: 'comment', title: t('sysDatabase.colComment'), minWidth: 180, sortable: true, showOverflow: 'tooltip' as const },
	{ field: 'rowEstimate', title: t('sysDatabase.colRowEstimate'), width: 110, sortable: true },
	{ field: 'totalSize', title: t('sysDatabase.colTotalSize'), width: 110, sortable: true },
	{ field: 'indexCount', title: t('sysDatabase.colIndexCount'), width: 90, sortable: true }
])

const columnColumns = computed(() => [
	{ field: 'ordinalPosition', title: t('sysDatabase.colOrdinalPosition'), width: 70, sortable: true },
	{ field: 'columnName', title: t('sysDatabase.colColumnName'), minWidth: 160, sortable: true },
	{ field: 'dataType', title: t('sysDatabase.colDataType'), minWidth: 130, sortable: true },
	{ field: 'isNullable', title: t('sysDatabase.nullable'), width: 80, sortable: true, slots: { default: 'col_nullable' } },
	{ field: 'maxLength', title: t('sysDatabase.colMaxLength'), width: 90, sortable: true, slots: { default: 'col_maxlen' } },
	{ field: 'isPrimaryKey', title: t('sysDatabase.primaryKey'), width: 90, sortable: true, slots: { default: 'col_pk' } },
	{ field: 'comment', title: t('sysDatabase.colComment'), minWidth: 160, sortable: true, showOverflow: 'tooltip' as const }
])

const indexColumns = computed(() => [
	{ field: 'indexName', title: t('sysDatabase.colIndexName'), minWidth: 200, sortable: true },
	{ field: 'isUnique', title: t('sysDatabase.unique'), width: 90, sortable: true, slots: { default: 'idx_unique' } },
	{ field: 'isPrimary', title: t('sysDatabase.primaryKey'), width: 90, sortable: true, slots: { default: 'idx_pk' } },
	{ field: 'definition', title: t('sysDatabase.colDefinition'), minWidth: 260, sortable: true, showOverflow: 'tooltip' as const }
])

onMounted(() => {
	void loadTables()
})
</script>

<style scoped>
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

.search-row {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 14px;
	flex-wrap: wrap;
}
.search-input {
	max-width: 280px;
}

.card-gap {
	margin-top: 14px;
}

:deep(.st) {
	display: inline-block;
	padding: 2px 8px;
	border-radius: 10px;
	font-size: 12px;
}
:deep(.st-key) {
	background: var(--ba-brand-soft);
	color: var(--ba-brand);
}
</style>