/** 服务器监控 API(批 Y 4.14,契约 /api/sysServer 三控制器端点)。全部只读。 */
import service from '../request'

/* ── 运行时信息 ─────────────────────────────── */
export interface ServerRuntimeInfo {
	/** 进程 Id */
	pid: number
	processName: string
	/** ISO 时间串 */
	startTime: string
	/** "3d 07:12:45" */
	uptime: string
	dotNetVersion: string
	osDescription: string
	hostName: string
	/** 工作集(字节) */
	workingSetBytes: number
	privateMemoryBytes: number
	/** 托管堆(字节) */
	managedMemoryBytes: number
	gcGen0: number
	gcGen1: number
	gcGen2: number
	isServerGC: boolean
	/** Linux 下 Process.Threads 语义受限,不可用为 null */
	threadCount: number | null
	processorCount: number
}

export const getServerRuntime = () =>
	service.get('/api/sysServer/runtime') as Promise<ServerRuntimeInfo>

/* ── 硬件/系统信息 ─────────────────────────────── */
export interface ServerDiskInfo {
	/** 挂载点/盘符根 */
	root: string
	name: string
	isReady: boolean
	/** 字节 */
	totalSize: number
	availableFreeSpace: number
	/** 0-100 */
	usagePercent: number | null
}

export interface ServerHardwareInfo {
	/** /proc/cpuinfo model name;非 Linux null */
	cpuModelName: string | null
	/** /proc/stat 双采样 delta;非 Linux 或采样失败 null */
	cpuUsagePercent: number | null
	processorCount: number
	/** 字节;非 Linux null */
	memoryTotalBytes: number | null
	/** 字节 */
	memoryAvailableBytes: number | null
	/** 0-100 */
	memoryUsagePercent: number | null
	disks: ServerDiskInfo[]
}

export const getServerHardware = () =>
	service.get('/api/sysServer/hardware') as Promise<ServerHardwareInfo>

/* ── 框架程序集清单 ─────────────────────────────── */
export interface ServerAssemblyInfo {
	name: string
	version: string
	fullName: string
}

export const getServerAssemblies = () =>
	service.get('/api/sysServer/assembly') as Promise<ServerAssemblyInfo[]>

/* ── 集群节点(批 AT:各实例自报快照聚合) ─────────────── */
/** 一个实例的监控行:平铺字段供节点表;runtime/hardware/assemblies 供详情区(读一次、不错配)。 */
export interface ServerNodeInfo {
	/** {NodeTag}:{Pid}:{GUID} —— 与定时任务集群视图同一实例标识,可对号 */
	instanceId: string
	/** 运维标签(JobCluster:NodeTag,缺省机器名) */
	nodeTag: string
	hostName: string
	pid: number
	startedAt: string | null
	uptime: string
	dotNetVersion: string
	osDescription: string
	workingSetBytes: number
	managedMemoryBytes: number
	isServerGC: boolean
	gcGen0: number
	gcGen1: number
	gcGen2: number
	cpuUsagePercent: number | null
	processorCount: number
	memoryTotalBytes: number | null
	memoryUsagePercent: number | null
	/** 可报告磁盘数(已按文件系统类型裁剪,不含 proc/tmpfs 等伪 FS) */
	diskCount: number
	/** 最满那块盘的占用率(%) */
	diskMaxUsagePercent: number | null
	/** AdminCore.Core 程序集版本(多实例滚动发布时确认是否同版本) */
	coreVersion: string
	assemblyCount: number
	/** 本次快照上报时刻(粒度＝上报周期,缺省 30s) */
	reportAt: string
	/** 是否本进程(端点在哪个实例执行,那个实例即 true) */
	isSelf: boolean
	runtime: ServerRuntimeInfo | null
	hardware: ServerHardwareInfo | null
	assemblies: ServerAssemblyInfo[]
}

export const getServerNodes = () =>
	service.get('/api/sysServer/nodes') as Promise<ServerNodeInfo[]>
