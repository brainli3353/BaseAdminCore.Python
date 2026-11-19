<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysServer.title') }}</h3>
				<p class="ba-sub">{{ t('sysServer.sub') }}</p>
				<p class="ba-hint">{{ mode === 'snapshot' ? t('sysServer.hintSnapshot') : t('sysServer.hintLive') }}</p>
			</div>
			<div class="ba-actions">
				<el-radio-group v-model="mode" size="small" @change="onModeChange">
					<el-radio-button value="snapshot">{{ t('sysServer.modeSnapshot') }}</el-radio-button>
					<el-radio-button value="live">{{ t('sysServer.modeLive') }}</el-radio-button>
				</el-radio-group>
				<el-button :loading="loading" @click="fetchAll">
					<el-icon><Refresh /></el-icon>{{ t('sysServer.btnRefresh') }}
				</el-button>
			</div>
		</div>

		<!-- 集群节点表(快照模式:各实例自报;读侧已隐藏超期死节点) -->
		<div v-if="mode === 'snapshot'" v-perm="'sysServer/nodes'" class="ba-card">
			<h4 class="ba-card-title">{{ t('sysServer.cardNodes') }}</h4>
			<template v-if="nodes.length">
				<vxe-grid
					:loading="loading"
					:data="nodes"
					:columns="nodeColumns"
					:row-config="{ keyField: 'instanceId', isHover: true }"
					:row-class-name="rowClassName"
					@cell-click="onCellClick"
				>
					<template #cell_self="{ row }">
						<el-tag v-if="row.isSelf" size="small" type="success">{{ t('sysServer.selfTag') }}</el-tag>
						<span v-else>—</span>
					</template>
					<template #cell_cpu="{ row }">{{ percent(row.cpuUsagePercent) }}</template>
					<template #cell_mem="{ row }">{{ percent(row.memoryUsagePercent) }}</template>
					<template #cell_disk="{ row }">{{ percent(row.diskMaxUsagePercent) }}</template>
					<template #cell_gc="{ row }">{{ row.gcGen0 }} / {{ row.gcGen1 }} / {{ row.gcGen2 }}</template>
					<template #cell_report="{ row }">{{ row.reportAt?.replace('T', ' ').slice(0, 19) }}</template>
				</vxe-grid>
				<p class="ba-selected">
					{{ t('sysServer.selectedNode') }}:
					<strong>{{ selectedNode?.nodeTag ?? '—' }}</strong>
					({{ selectedNode?.hostName ?? '—' }} · PID {{ selectedNode?.pid ?? '—' }})
				</p>
			</template>
			<BaEmpty v-else :message="t('sysServer.emptyNodes')" />
		</div>

		<!-- 运行时信息(首载 ≥300ms 出骨架;非加载无数据出三态空态——不再"加载中/暂无"二态塌缩) -->
		<div v-perm="'sysServer/runtime'" class="ba-card">
			<h4 class="ba-card-title">{{ t('sysServer.cardRuntime') }}</h4>
			<BaSkeleton :loading="loading" variant="card" :rows="4">
				<el-descriptions v-if="viewRuntime" :column="4" border size="small">
				<el-descriptions-item label="PID">{{ viewRuntime.pid }}</el-descriptions-item>
				<el-descriptions-item :label="t('sysServer.lblProcess')">{{ viewRuntime.processName }}</el-descriptions-item>
				<el-descriptions-item :label="t('sysServer.lblStartTime')">{{ viewRuntime.startTime?.replace('T', ' ').slice(0, 19) }}</el-descriptions-item>
				<el-descriptions-item :label="t('sysServer.lblUptime')">{{ viewRuntime.uptime }}</el-descriptions-item>
				<el-descriptions-item :label="t('sysServer.lblDotNetVersion')">{{ viewRuntime.dotNetVersion }}</el-descriptions-item>
				<el-descriptions-item :label="t('sysServer.lblHostName')">{{ viewRuntime.hostName }}</el-descriptions-item>
				<el-descriptions-item label="OS" :span="2">{{ viewRuntime.osDescription }}</el-descriptions-item>
				<el-descriptions-item :label="t('sysServer.lblWorkingSet')">{{ fmtBytes(viewRuntime.workingSetBytes) }}</el-descriptions-item>
				<el-descriptions-item :label="t('sysServer.lblPrivateMemory')">{{ fmtBytes(viewRuntime.privateMemoryBytes) }}</el-descriptions-item>
				<el-descriptions-item :label="t('sysServer.lblManagedMemory')">{{ fmtBytes(viewRuntime.managedMemoryBytes) }}</el-descriptions-item>
				<el-descriptions-item :label="t('sysServer.lblGcMode')">{{ viewRuntime.isServerGC ? 'Server' : 'Workstation' }}</el-descriptions-item>
				<el-descriptions-item :label="t('sysServer.lblGcCount')">{{ viewRuntime.gcGen0 }} / {{ viewRuntime.gcGen1 }} / {{ viewRuntime.gcGen2 }}</el-descriptions-item>
				<el-descriptions-item :label="t('sysServer.lblThreadCount')">{{ viewRuntime.threadCount ?? '—' }}</el-descriptions-item>
				<el-descriptions-item :label="t('sysServer.lblCpuCores')">{{ viewRuntime.processorCount }}</el-descriptions-item>
			</el-descriptions>
				<BaEmpty v-else />
			</BaSkeleton>
		</div>

		<!-- 硬件信息(同 runtime 卡三态口径) -->
		<div v-perm="'sysServer/hardware'" class="ba-card">
			<h4 class="ba-card-title">{{ t('sysServer.cardHardware') }}</h4>
			<BaSkeleton :loading="loading" variant="card" :rows="4">
				<template v-if="viewHardware">
				<el-descriptions :column="4" border size="small" class="ba-hw-summary">
					<el-descriptions-item label="CPU" :span="2">{{ viewHardware.cpuModelName ?? '—' }}</el-descriptions-item>
					<el-descriptions-item :label="t('sysServer.lblCpuUsage')">{{ percent(viewHardware.cpuUsagePercent) }}</el-descriptions-item>
					<el-descriptions-item :label="t('sysServer.lblCores')">{{ viewHardware.processorCount }}</el-descriptions-item>
					<el-descriptions-item :label="t('sysServer.lblMemTotal')">{{ fmtBytes(viewHardware.memoryTotalBytes) }}</el-descriptions-item>
					<el-descriptions-item :label="t('sysServer.lblMemAvailable')">{{ fmtBytes(viewHardware.memoryAvailableBytes) }}</el-descriptions-item>
					<el-descriptions-item :label="t('sysServer.lblMemUsage')">{{ percent(viewHardware.memoryUsagePercent) }}</el-descriptions-item>
				</el-descriptions>
				<vxe-grid :loading="loading" :data="viewHardware.disks" :columns="diskColumns" :row-config="{ keyField: 'root' }">
					<template #cell_total="{ row }">{{ fmtBytes(row.totalSize) }}</template>
					<template #cell_free="{ row }">{{ fmtBytes(row.availableFreeSpace) }}</template>
					<template #cell_usage="{ row }">{{ percent(row.usagePercent) }}</template>
				</vxe-grid>
				</template>
				<BaEmpty v-else />
			</BaSkeleton>
		</div>

		<!-- 框架程序集 -->
		<div v-perm="'sysServer/assembly'" class="ba-card">
			<h4 class="ba-card-title">{{ t('sysServer.cardAssembly') }}</h4>
			<vxe-grid v-if="viewAssemblies.length" :loading="loading" :data="viewAssemblies" :columns="asmColumns" :row-config="{ keyField: 'name' }" />
			<BaEmpty v-else />
		</div>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'SysServer' })

import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Refresh } from '@element-plus/icons-vue'
import BaEmpty from '@/components/BaEmpty.vue'
import BaSkeleton from '@/components/BaSkeleton.vue'
import * as serverApi from '@/api/sys/server'
import type { ServerRuntimeInfo, ServerHardwareInfo, ServerAssemblyInfo, ServerNodeInfo } from '@/api/sys/server'
import { useUserStore } from '@/stores/user'
import { useMenuStore } from '@/stores/menu'

const { t } = useI18n()
const userStore = useUserStore()
const menuStore = useMenuStore()

/** 与 v-perm 同一判据(超管 999 直通):无 nodes 权限时不把默认视图停在会空白的快照模式。 */
function hasPerm(key: string): boolean {
	return userStore.user?.accountType === 999 || menuStore.permissions.includes(key)
}

const loading = ref(false)
/** 数据源(批 AT D1 双通道):snapshot=各实例自报聚合(可看任意节点);live=本实例即时三端点。 */
const mode = ref<'snapshot' | 'live'>(hasPerm('sysServer/nodes') ? 'snapshot' : 'live')

// 快照通道
const nodes = ref<ServerNodeInfo[]>([])
const selectedId = ref('')
const selectedNode = computed(() => nodes.value.find(n => n.instanceId === selectedId.value) ?? null)

// 即时通道
const liveRuntime = ref<ServerRuntimeInfo | null>(null)
const liveHardware = ref<ServerHardwareInfo | null>(null)
const liveAssemblies = ref<ServerAssemblyInfo[]>([])

// 详情区数据源(两条通道共用同一套渲染)
const viewRuntime = computed(() => (mode.value === 'snapshot' ? selectedNode.value?.runtime ?? null : liveRuntime.value))
const viewHardware = computed(() => (mode.value === 'snapshot' ? selectedNode.value?.hardware ?? null : liveHardware.value))
const viewAssemblies = computed(() => (mode.value === 'snapshot' ? selectedNode.value?.assemblies ?? [] : liveAssemblies.value))

const nodeColumns = computed(() => [
	{ field: 'isSelf', title: t('sysServer.colSelf'), width: 90, sortable: true, slots: { default: 'cell_self' } },
	{ field: 'nodeTag', title: t('sysServer.colNode'), minWidth: 130, sortable: true },
	{ field: 'hostName', title: t('sysServer.colHost'), minWidth: 120, sortable: true },
	{ field: 'pid', title: t('sysServer.colPid'), width: 80, sortable: true },
	{ field: 'uptime', title: t('sysServer.colUptime'), width: 110, sortable: true },
	{ field: 'cpuUsagePercent', title: t('sysServer.colCpu'), width: 90, sortable: true, slots: { default: 'cell_cpu' } },
	{ field: 'memoryUsagePercent', title: t('sysServer.colMem'), width: 100, sortable: true, slots: { default: 'cell_mem' } },
	{ field: 'diskMaxUsagePercent', title: t('sysServer.colDiskMax'), width: 110, sortable: true, slots: { default: 'cell_disk' } },
	{ field: 'gcGen0', title: t('sysServer.colGc'), width: 110, sortable: true, slots: { default: 'cell_gc' } },
	{ field: 'coreVersion', title: t('sysServer.colCoreVersion'), width: 120, sortable: true },
	{ field: 'reportAt', title: t('sysServer.colReportAt'), width: 150, sortable: true, slots: { default: 'cell_report' } }
])

const diskColumns = computed(() => [
	{ field: 'root', title: t('sysServer.colMountPoint'), minWidth: 140, sortable: true },
	{ field: 'name', title: t('sysServer.colName'), width: 120, sortable: true },
	{ field: 'isReady', title: t('sysServer.colReady'), width: 70, sortable: true },
	{ field: 'totalSize', title: t('sysServer.colTotal'), width: 120, sortable: true, slots: { default: 'cell_total' } },
	{ field: 'availableFreeSpace', title: t('sysServer.colAvailable'), width: 120, sortable: true, slots: { default: 'cell_free' } },
	{ field: 'usagePercent', title: t('sysServer.colUsage'), width: 100, sortable: true, slots: { default: 'cell_usage' } }
])

const asmColumns = computed(() => [
	{ field: 'name', title: t('sysServer.colAssembly'), minWidth: 220, sortable: true, showOverflow: 'tooltip' as const },
	{ field: 'version', title: t('sysServer.colVersion'), width: 140, sortable: true }
])

/** 字节 → 可读(页面局部,无共享工具需求)。 */
function fmtBytes(v: number | null): string {
	if (v == null) return '—'
	const units = ['B', 'KB', 'MB', 'GB', 'TB']
	let i = 0
	let n = v
	while (n >= 1024 && i < units.length - 1) {
		n /= 1024
		i++
	}
	return `${n.toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

/** 百分比渲染(null → 破折号;非 Linux 或采集失败为 null)。 */
function percent(v: number | null | undefined): string {
	return v != null ? `${v}%` : '—'
}

/** 选中行高亮(点击行即切换详情区渲染对象)。 */
function rowClassName({ row }: { row: ServerNodeInfo }): string {
	return row.instanceId === selectedId.value ? 'ba-row-active' : ''
}

function onCellClick({ row }: { row: ServerNodeInfo }): void {
	selectedId.value = row.instanceId
}

function onModeChange(): void {
	void fetchAll()
}

async function fetchAll(): Promise<void> {
	loading.value = true
	try {
		if (mode.value === 'snapshot') {
			// 无 nodes 权限不请求(v-perm 只摘 DOM,拦不住请求;无权限直连后端必 403 弹窗)
			if (!hasPerm('sysServer/nodes')) return
			nodes.value = await serverApi.getServerNodes()
			// 选中项保持(刷新不跳);失效/首次时优先落到"本实例",否则取第一行
			if (!nodes.value.some(n => n.instanceId === selectedId.value)) {
				selectedId.value = (nodes.value.find(n => n.isSelf) ?? nodes.value[0])?.instanceId ?? ''
			}
		} else {
			/* 三卡各自判权 + 独立请求:无权限卡不请求(不产生 403 弹窗);
			 * 用 allSettled 而非 all——单卡失败(rejected)不拖死其余有权卡。 */
			const [r, h, a] = await Promise.allSettled([
				hasPerm('sysServer/runtime') ? serverApi.getServerRuntime() : Promise.resolve(null),
				hasPerm('sysServer/hardware') ? serverApi.getServerHardware() : Promise.resolve(null),
				hasPerm('sysServer/assembly') ? serverApi.getServerAssemblies() : Promise.resolve([])
			])
			if (r.status === 'fulfilled') liveRuntime.value = r.value
			if (h.status === 'fulfilled') liveHardware.value = h.value
			if (a.status === 'fulfilled') liveAssemblies.value = a.value
		}
	} finally {
		loading.value = false
	}
}

onMounted(() => {
	void fetchAll()
})
</script>

<style scoped>
.ba-page-header {
	align-items: flex-start;
}
.ba-actions {
	display: flex;
	gap: 8px;
	align-items: center;
}
.ba-hint {
	margin: 4px 0 0;
	color: #909399;
	font-size: 12px;
}
.ba-card-title {
	margin: 0 0 12px;
	font-size: 14px;
	font-weight: 600;
}
.ba-hw-summary {
	margin-bottom: 12px;
}
.ba-selected {
	margin: 8px 0 0;
	font-size: 12px;
	color: #606266;
}
:deep(.ba-row-active) {
	background: var(--el-color-primary-light-9);
}
</style>