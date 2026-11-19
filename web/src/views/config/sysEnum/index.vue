<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysEnum.title') }}</h3>
				<p class="ba-sub">{{ t('sysEnum.sub') }}</p>
			</div>
			<el-button :loading="loading" @click="fetchTypeList">
				<el-icon><Refresh /></el-icon>{{ t('sysEnum.btnRefresh') }}
			</el-button>
		</div>

		<!-- 枚举类型列表 -->
		<div v-perm="'sysEnum/typeList'" class="ba-card">
			<h4 class="ba-card-title">{{ t('sysEnum.cardTypes') }}</h4>
			<el-input
				v-model="keyword"
				class="ba-search"
				:placeholder="t('sysEnum.filterPlaceholder')"
				clearable
			/>
			<el-table v-loading="loading" :data="filteredTypes" row-key="typeName" :row-class-name="() => 'ba-enum-row'">
				<el-table-column type="expand">
					<template #default="{ row }">
						<el-table :data="row.enumEntities" size="small" class="ba-enum-vals">
							<el-table-column prop="name" :label="t('sysEnum.colMember')" width="160" sortable />
							<el-table-column prop="value" :label="t('sysEnum.colValue')" width="100" sortable />
							<el-table-column prop="describe" :label="t('sysEnum.colDescribe')" sortable show-overflow-tooltip />
						</el-table>
					</template>
				</el-table-column>
				<el-table-column prop="typeName" :label="t('sysEnum.colTypeName')" min-width="200" sortable />
				<el-table-column prop="typeDescribe" :label="t('sysEnum.colDescribe')" min-width="200" sortable show-overflow-tooltip />
				<el-table-column :label="t('sysEnum.colValueCount')" width="90">
					<template #default="{ row }">{{ row.enumEntities.length }}</template>
				</el-table-column>
			</el-table>
			<BaEmpty
				v-if="!filteredTypes.length"
				:state="loading ? 'loading' : 'empty'"
				:message="!loading && keyword ? t('sysEnum.emptyNoMatch') : undefined"
			/>
		</div>

		<!-- 单枚举值查询 -->
		<div v-perm="'sysEnum/data'" class="ba-card">
			<h4 class="ba-card-title">{{ t('sysEnum.cardDataQuery') }}</h4>
			<el-form inline>
				<el-form-item :label="t('sysEnum.labelEnumTypeName')">
					<el-select v-model="queryEnumName" filterable :placeholder="t('sysEnum.placeholderEnumType')" style="width: 240px">
						<el-option
							v-for="t in types"
							:key="t.typeName"
							:label="t.typeName"
							:value="t.typeName"
						/>
					</el-select>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" :loading="dataLoading" @click="fetchData">{{ t('common.search') }}</el-button>
					<el-button @click="resetDataQuery">{{ t('common.reset') }}</el-button>
				</el-form-item>
			</el-form>
			<el-table v-if="dataList.length" :data="dataList" size="small">
				<el-table-column prop="name" :label="t('sysEnum.colMember')" width="160" sortable />
				<el-table-column prop="value" :label="t('sysEnum.colValue')" width="100" sortable />
				<el-table-column prop="describe" :label="t('sysEnum.colDescribe')" sortable show-overflow-tooltip />
			</el-table>
			<div v-else class="ba-empty">{{ dataQueried ? t('common.noData') : '' }}</div>
		</div>

		<!-- 实体字段枚举查询 -->
		<div v-perm="'sysEnum/dataByField'" class="ba-card">
			<h4 class="ba-card-title">{{ t('sysEnum.cardFieldQuery') }}</h4>
			<el-form inline>
				<el-form-item :label="t('sysEnum.labelEntityName')">
					<el-input v-model="fieldQuery.entityName" :placeholder="t('sysEnum.placeholderEntity')" style="width: 180px" />
				</el-form-item>
				<el-form-item :label="t('sysEnum.labelFieldName')">
					<el-input v-model="fieldQuery.fieldName" :placeholder="t('sysEnum.placeholderField')" style="width: 160px" />
				</el-form-item>
				<el-form-item>
					<el-button type="primary" :loading="fieldLoading" @click="fetchDataByField">{{ t('common.search') }}</el-button>
					<el-button @click="resetFieldQuery">{{ t('common.reset') }}</el-button>
				</el-form-item>
			</el-form>
			<el-table v-if="fieldList.length" :data="fieldList" size="small">
				<el-table-column prop="name" :label="t('sysEnum.colMember')" width="160" sortable />
				<el-table-column prop="value" :label="t('sysEnum.colValue')" width="100" sortable />
				<el-table-column prop="describe" :label="t('sysEnum.colDescribe')" sortable show-overflow-tooltip />
			</el-table>
			<div v-else class="ba-empty">{{ fieldQueried ? t('common.noData') : '' }}</div>
		</div>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'SysEnum' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Refresh } from '@element-plus/icons-vue'
import BaEmpty from '@/components/BaEmpty.vue'
import {
	getEnumTypeList,
	getEnumData,
	getEnumDataByField,
	type EnumEntity,
	type EnumTypeOutput
} from '@/api/sys/enum'

const { t } = useI18n()
const loading = ref(false)
const types = ref<EnumTypeOutput[]>([])
const keyword = ref('')

const dataLoading = ref(false)
const dataQueried = ref(false)
const queryEnumName = ref('')
const dataList = ref<EnumEntity[]>([])

const fieldLoading = ref(false)
const fieldQueried = ref(false)
const fieldQuery = reactive({ entityName: '', fieldName: '' })
const fieldList = ref<EnumEntity[]>([])

const filteredTypes = computed(() => {
	const kw = keyword.value.trim().toLowerCase()
	if (!kw) return types.value
	return types.value.filter(
		t => t.typeName.toLowerCase().includes(kw) || t.typeDescribe.toLowerCase().includes(kw)
	)
})

async function fetchTypeList() {
	loading.value = true
	try {
		types.value = await getEnumTypeList()
	} finally {
		loading.value = false
	}
}

async function fetchData() {
	if (!queryEnumName.value) return
	dataLoading.value = true
	dataQueried.value = true
	try {
		dataList.value = await getEnumData(queryEnumName.value)
	} finally {
		dataLoading.value = false
	}
}

async function fetchDataByField() {
	if (!fieldQuery.entityName || !fieldQuery.fieldName) return
	fieldLoading.value = true
	fieldQueried.value = true
	try {
		fieldList.value = await getEnumDataByField(fieldQuery.entityName, fieldQuery.fieldName)
	} finally {
		fieldLoading.value = false
	}
}

/** 重置单枚举值查询:清筛选 + 清结果 + 回到未查询态(空态不再是"暂无数据",而是空白待查)。 */
function resetDataQuery(): void {
	queryEnumName.value = ''
	dataList.value = []
	dataQueried.value = false
}

/** 重置实体字段枚举查询:同上口径。 */
function resetFieldQuery(): void {
	fieldQuery.entityName = ''
	fieldQuery.fieldName = ''
	fieldList.value = []
	fieldQueried.value = false
}

onMounted(fetchTypeList)
</script>
