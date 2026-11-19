<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('onlineUser.title') }}</h3>
				<p class="ba-sub">{{ t('onlineUser.sub') }}</p>
			</div>
			<el-button :loading="loading" @click="fetchList">
				<el-icon><Refresh /></el-icon>{{ t('onlineUser.btnRefresh') }}
			</el-button>
		</div>

		<!-- 数据卡 -->
		<div class="ba-card">
			<div class="online-bar">{{ t('onlineUser.onlineCount', { n: rows.length }) }}</div>
			<vxe-grid :loading="loading" :data="rows" :columns="columns" :row-config="{ keyField: 'connectionId' }">
				<template #row_ops="{ row }">
					<el-button
						v-perm="'onlineUser/forceOffline'"
						link
						type="danger"
						size="small"
						:loading="busyId === row.connectionId"
						@click="onForceOffline(row)"
					>
						{{ t('onlineUser.btnForceOffline') }}
					</el-button>
				</template>
			</vxe-grid>
		</div>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'OnlineUser' })

import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import * as onlineApi from '@/api/sys/onlineUser'
import type { OnlineUserInfo } from '@/api/sys/onlineUser'
import { onOnlineUserList, type OnlineUserListPayload } from '@/utils/realtime'

const { t } = useI18n()
const loading = ref(false)
const busyId = ref<string | null>(null)
const rows = ref<OnlineUserInfo[]>([])
let offList: (() => void) | undefined

/** 上线时间:后端 ISO 串 → YYYY-MM-DD HH:mm:ss(本页局部口径,无全局工具;非法值原样兜底)。 */
function formatTime(value: string | null): string {
	if (!value) return '—'
	const d = new Date(value)
	if (Number.isNaN(d.getTime())) return value
	const p = (n: number): string => String(n).padStart(2, '0')
	return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

const columns = computed(() => [
	{ field: 'connectionId', title: t('onlineUser.colConnectionId'), minWidth: 200, sortable: true },
	{ field: 'account', title: t('onlineUser.colAccount'), width: 130, sortable: true },
	{ field: 'realName', title: t('onlineUser.colRealName'), width: 120, sortable: true, showOverflow: 'tooltip' },
	{ field: 'ip', title: t('onlineUser.colIp'), width: 130, sortable: true, showOverflow: 'tooltip' },
	{ field: 'browser', title: t('onlineUser.colBrowser'), width: 120, sortable: true, showOverflow: 'tooltip' },
	{ field: 'os', title: t('onlineUser.colOs'), width: 120, sortable: true, showOverflow: 'tooltip' },
	{
		field: 'time',
		title: t('onlineUser.colTime'),
		width: 170,
		sortable: true,
		formatter: ({ cellValue }: { cellValue: string | null }) => formatTime(cellValue)
	} as object,
	{ title: t('common.operations'), width: 110, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

async function fetchList(): Promise<void> {
	loading.value = true
	try {
		rows.value = await onlineApi.listOnline()
	} finally {
		loading.value = false
	}
}

async function onForceOffline(row: OnlineUserInfo): Promise<void> {
	try {
		await ElMessageBox.confirm(
			t('onlineUser.msgForceConfirm', { name: row.realName || row.account }),
			t('onlineUser.msgForceTitle'),
			{ type: 'warning' }
		)
	} catch {
		return
	}
	busyId.value = row.connectionId
	try {
		await onlineApi.forceOffline(row.connectionId)
		ElMessage.success(t('onlineUser.msgForceDone'))
		await fetchList()
	} finally {
		busyId.value = null
	}
}

onMounted(() => {
	void fetchList()
	// 批 CL G31:实时在线列表——服务端推送全量列表直接替换(免再拉 API)
	offList = onOnlineUserList((m: OnlineUserListPayload) => {
		rows.value = (m.userList ?? []) as OnlineUserInfo[]
	})
})
onUnmounted(() => {
	offList?.()
})
</script>

<style scoped>
/* 页头右上刷新按钮与既有页面口径一致,无额外样式 */
.online-bar {
	font-size: 13px;
	color: var(--ba-text-tertiary);
	margin-bottom: 10px;
}
</style>
