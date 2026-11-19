<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('localization.title') }}</h3>
				<p class="ba-sub">{{ t('localization.sub') }}</p>
			</div>
			<el-button :loading="loading" @click="fetchCultures">
				<el-icon><Refresh /></el-icon>{{ t('localization.refresh') }}
			</el-button>
		</div>

		<!-- 只读视图:与后端同一份解析结果(按钮权限键 sysLocalization/cultures) -->
		<div v-perm="'sysLocalization/cultures'" class="ba-card">
			<h4 class="ba-card-title">{{ t('localization.overview') }}</h4>
			<el-descriptions :column="3" border>
				<el-descriptions-item :label="t('localization.defaultCulture')">
					{{ data?.defaultCulture ?? '-' }}
				</el-descriptions-item>
				<el-descriptions-item :label="t('localization.current')">
					{{ data?.current ?? '-' }}
				</el-descriptions-item>
				<el-descriptions-item :label="t('localization.count')">
					{{ data?.supported?.length ?? 0 }}
				</el-descriptions-item>
			</el-descriptions>

			<h4 class="ba-card-title" style="margin-top: 16px">{{ t('localization.supported') }}</h4>
			<el-table v-ba-loading="loading" :data="rows" size="small">
				<el-table-column prop="code" :label="t('localization.code')" min-width="160" sortable />
				<el-table-column :label="t('localization.isDefault')" width="120">
					<template #default="{ row }">
						<el-tag v-if="row.isDefault" type="success">{{ t('common.yes') }}</el-tag>
						<span v-else>-</span>
					</template>
				</el-table-column>
				<el-table-column :label="t('localization.isCurrent')" width="120">
					<template #default="{ row }">
						<el-tag v-if="row.isCurrent" type="primary">{{ t('common.yes') }}</el-tag>
						<span v-else>-</span>
					</template>
				</el-table-column>
			</el-table>
			<!-- 三态占位:加载中/暂无数据不再共用一行文案(原 `loading ? noData` 二态塌缩) -->
			<BaEmpty v-if="!rows.length" :state="loading ? 'loading' : 'empty'" />
		</div>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'SysLocalization' })

import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Refresh } from '@element-plus/icons-vue'
import BaEmpty from '@/components/BaEmpty.vue'
import { getCultures, type LocalizationCulturesOutput } from '@/api/sys/localization'

const { t } = useI18n()
const loading = ref(false)
const data = ref<LocalizationCulturesOutput>()

/** 受支持语言 → 表格行(标出缺省/当前) */
const rows = computed(() =>
	(data.value?.supported ?? []).map(code => ({
		code,
		isDefault: code === data.value?.defaultCulture,
		isCurrent: code === data.value?.current
	}))
)

async function fetchCultures() {
	loading.value = true
	try {
		data.value = await getCultures()
	} finally {
		loading.value = false
	}
}

onMounted(fetchCultures)
</script>