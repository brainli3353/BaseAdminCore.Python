/**
 * 表格列自定义组合式(批 A 4.12):
 * 用户级列设置(显示/隐藏、列宽、固定、顺序)持久化,gridId=视图标识(如 "sys/user")。
 * 维护本地列定义副本,设置面板直接改副本,保存时序列化四类状态字典提交;
 * 加载时按字典还原列态。无配置/加载失败 → 回退默认列(不阻塞页面)。
 */
import { ref, type Ref } from 'vue'
import * as columnApi from '@/api/sys/columnCustom'

/** 列定义(本仓 vxe-grid columns 子集,settings 面板只认这些字段) */
export interface ColumnDef {
	field?: string
	title?: string
	width?: number
	minWidth?: number
	fixed?: 'left' | 'right' | '' | null
	slots?: Record<string, string>
	[key: string]: unknown
}

export function useColumnCustom(gridId: string, defaultColumns: ColumnDef[]) {
	/** 本地列副本(设置面板唯一可变源) */
	const localColumns: Ref<ColumnDef[]> = ref(clone(defaultColumns))
	/** 是否加载过个性化配置 */
	const customized = ref(false)

	/** 从服务端加载本人列配置并应用到本地副本(无配置/失败 → 保持默认) */
	async function load(): Promise<void> {
		try {
			const data = await columnApi.getColumnCustom(gridId)
			if (!data) {
				return
			}
			applyCustom(data)
			customized.value = true
		} catch {
			/* 加载失败回退默认列,不阻塞列表 */
		}
	}

	function applyCustom(data: columnApi.ColumnCustomOutput): void {
		const cols = localColumns.value
		// 顺序:sortData 序号排序(无序号保持原位)
		if (data.sortData) {
			const order = data.sortData
			const indexed = cols
				.map((c, i) => ({ c, i, s: c.field ? (order[c.field] ?? -1) : -1 }))
				.sort((a, b) => {
					if (a.s < 0 && b.s < 0) return a.i - b.i
					if (a.s < 0) return 1
					if (b.s < 0) return -1
					return a.s - b.s
				})
				.map((x) => x.c)
			cols.splice(0, cols.length, ...indexed)
		}
		for (const c of cols) {
			if (!c.field) {
				continue
			}
			if (data.visibleData && c.field in data.visibleData) {
				;(c as Record<string, unknown>).visible = data.visibleData[c.field]
			}
			if (data.resizableData && c.field in data.resizableData) {
				c.width = data.resizableData[c.field]
			}
			if (data.fixedData && c.field in data.fixedData) {
				const f = data.fixedData[c.field]
				c.fixed = f === 'none' ? '' : (f as 'left' | 'right')
			}
		}
	}

	/** 收集本地副本为四类状态字典(field 为键;操作列等无 field 列不参与) */
	function collect(): columnApi.StoreColumnCustomPayload {
		const visibleData: Record<string, boolean> = {}
		const resizableData: Record<string, number> = {}
		const fixedData: Record<string, string> = {}
		const sortData: Record<string, number> = {}
		localColumns.value.forEach((c, i) => {
			if (!c.field) {
				return
			}
			visibleData[c.field] = (c as Record<string, unknown>).visible !== false
			if (typeof c.width === 'number') {
				resizableData[c.field] = c.width
			}
			if (c.fixed === 'left' || c.fixed === 'right') {
				fixedData[c.field] = c.fixed
			}
			sortData[c.field] = i
		})
		return { gridId, visibleData, resizableData, fixedData, sortData }
	}

	/** 保存(整体覆盖);返回是否成功 */
	async function save(): Promise<boolean> {
		try {
			await columnApi.storeColumnCustom(collect())
			customized.value = true
			return true
		} catch {
			return false
		}
	}

	/** 上移/下移(顺序设置) */
	function move(index: number, dir: -1 | 1): void {
		const cols = localColumns.value
		const j = index + dir
		if (j < 0 || j >= cols.length) {
			return
		}
		;[cols[index], cols[j]] = [cols[j], cols[index]]
	}

	/** 重置(服务端物理删 + 本地还原默认) */
	async function reset(): Promise<boolean> {
		try {
			await columnApi.resetColumnCustom(gridId)
			localColumns.value = clone(defaultColumns)
			customized.value = false
			return true
		} catch {
			return false
		}
	}

	/** 把本地副本推给 vxe-grid(loadColumn) */
	function applyToGrid(grid: { loadColumn(cols: ColumnDef[]): void } | null): void {
		grid?.loadColumn(localColumns.value)
	}

	function clone(cols: ColumnDef[]): ColumnDef[] {
		return cols.map((c) => ({ ...c }))
	}

	return { localColumns, customized, load, save, reset, move, applyToGrid }
}
