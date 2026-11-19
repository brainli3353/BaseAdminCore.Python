<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysFile.title') }}</h3>
				<p class="ba-sub">
					{{ t('sysFile.sub') }}
				</p>
			</div>
		</div>

		<!-- 上传卡 -->
		<div v-ba-loading="uploading" class="ba-card">
			<el-upload
				drag
				multiple
				action="#"
				:auto-upload="true"
				:show-file-list="false"
				:disabled="uploading"
				:http-request="doUpload"
			>
				<el-icon class="upload-icon"><UploadFilled /></el-icon>
				<div class="el-upload__text">{{ t('sysFile.dragHint') }}<em>{{ t('sysFile.clickUpload') }}</em></div>
			</el-upload>
		</div>

		<!-- 文件清单(服务端分页) -->
		<div class="ba-card">
			<div class="table-title">{{ t('sysFile.listTitle') }}</div>

			<div class="search-row">
				<el-input
					v-model="query.fileName"
					:placeholder="t('sysFile.phFileName')"
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
					:start-placeholder="t('sysFile.phStartDate')"
					:end-placeholder="t('sysFile.phEndDate')"
					clearable
					class="search-date"
				/>
				<el-button type="primary" @click="reload">{{ t('common.search') }}</el-button>
				<el-button @click="doReset">{{ t('common.reset') }}</el-button>
			</div>

			<vxe-grid
				:loading="loading"
				:data="rows"
				:columns="columns"
				:pager-config="pager"
				:empty-text="t('common.noData')"
				:row-config="{ keyField: 'id' }"
				@page-change="onPageChange"
			>
				<template #cell_url="{ row }">
					<template v-if="row.url">
						<el-button link type="primary" size="small" @click="copyUrl(row.url)">
							{{ t('sysFile.btnCopy') }}
						</el-button>
						<el-button link type="primary" size="small" @click="openUrl(row.url)">
							{{ t('sysFile.btnDownload') }}
						</el-button>
					</template>
					<span v-else>-</span>
				</template>
				<template #row_ops="{ row }">
					<el-button v-perm="'sysFile/delete'" link type="danger" size="small" @click="onDelete(row)">
						{{ t('common.delete') }}
					</el-button>
				</template>
			</vxe-grid>
		</div>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'SysFile' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type UploadRequestOptions } from 'element-plus'
import { Search, UploadFilled } from '@element-plus/icons-vue'
import * as fileApi from '@/api/sys/file'
import type { SysFilePageOutput } from '@/api/sys/file'
import { usePaged } from '@/composables/usePaged'
import { formatDateTime } from '@/utils/format'

const { t } = useI18n()

type DateRange = [string, string] | null
/** 范围选择默认时刻:起 00:00:00,止 23:59:59(后端闭区间) */
const defaultTime: [Date, Date] = [new Date(2000, 0, 1, 0, 0, 0), new Date(2000, 0, 1, 23, 59, 59)]

const query = reactive({
	fileName: '',
	range: null as DateRange
})

// 筛选直连页面自有 query:usePaged 的 params 不写入,fetcher 内显式取值
const { loading, rows, pager, fetchPage, reload, onPageChange } = usePaged<SysFilePageOutput>(q =>
	fileApi.pageFile({
		fileName: query.fileName || null,
		startDate: query.range?.[0] ?? null,
		endDate: query.range?.[1] ?? null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number
	})
)

function doReset(): void {
	query.fileName = ''
	query.range = null
	reload()
}

const columns = computed(() => [
	{ field: 'fileName', title: t('sysFile.colFileName'), minWidth: 200, showOverflow: 'tooltip' },
	{ field: 'suffix', title: t('sysFile.colSuffix'), width: 90 },
	{
		field: 'sizeKb',
		title: t('sysFile.colSize'),
		width: 110,
		formatter: ({ cellValue }: { cellValue: number | string }) => `${cellValue} KB`
	} as object,
	{
		field: 'createTime',
		title: t('sysFile.colCreateTime'),
		width: 170,
		formatter: ({ cellValue }: { cellValue: string | null }) => formatDateTime(cellValue)
	} as object,
	{ title: t('sysFile.colUrl'), width: 150, slots: { default: 'cell_url' } },
	{ title: t('common.operations'), width: 90, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

/** 上传中计数:多选并发上传时 >0 即禁用上传区,防重复提交 */
const uploadingCount = ref(0)
const uploading = computed(() => uploadingCount.value > 0)

/** 自定义上传:走统一 axios 实例手发 multipart(字段名 file;Bearer 令牌由请求拦截器附加);
 * 响应已由拦截器拆包为 SysFileOutput。上传不贴权限键,登录即可。成功后回第一页重查清单。 */
async function doUpload(options: UploadRequestOptions): Promise<void> {
	uploadingCount.value++
	try {
		const res = await fileApi.uploadFile(options.file)
		ElMessage.success(t('sysFile.msgUploadSuccess', { name: res.fileName ?? options.file.name }))
		reload()
	} catch {
		// 逐文件结果提示:全局拦截器已报错,这里补出具体文件名,避免多选失败时分不清是哪个
		ElMessage.error(t('sysFile.msgUploadFailed', { name: options.file.name }))
	} finally {
		uploadingCount.value--
	}
}

function openUrl(url: string): void {
	window.open(url, '_blank', 'noopener')
}

async function copyUrl(url: string): Promise<void> {
	try {
		await navigator.clipboard.writeText(url)
		ElMessage.success(t('sysFile.msgCopied'))
	} catch {
		ElMessage.warning(t('sysFile.msgCopyFailed'))
	}
}

async function onDelete(row: SysFilePageOutput): Promise<void> {
	try {
		await ElMessageBox.confirm(
			t('sysFile.msgDeleteConfirm', { name: row.fileName ?? row.id }),
			t('sysFile.deleteConfirmTitle'),
			{ type: 'warning' }
		)
	} catch {
		return
	}
	await fileApi.deleteFile(row.id)
	ElMessage.success(t('sysFile.msgDeleted'))
	void fetchPage()
}

onMounted(() => {
	void fetchPage()
})
</script>

<style scoped>
.upload-icon {
	margin-top: 40px;
	font-size: 56px;
	color: var(--ba-text-tertiary);
}

.table-title {
	font-size: 14px;
	font-weight: 600;
	margin-bottom: 12px;
}

.search-row {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 14px;
}
.search-input {
	max-width: 240px;
}
.search-date {
	max-width: 360px;
}
</style>