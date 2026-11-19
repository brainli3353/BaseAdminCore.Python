/** 用户表格列配置(批 A 4.12):本人列设置存取,自助端点无按钮权限。 */
import service from '../request'

/** 表格列配置输出(后端 ColumnCustomOutput,无配置时 data=null) */
export interface ColumnCustomOutput {
	userId: number | string
	gridId: string
	fixedData?: Record<string, string> | null
	resizableData?: Record<string, number> | null
	sortData?: Record<string, number> | null
	visibleData?: Record<string, boolean> | null
}

/** 保存入参(四类状态字典整体覆盖;null=不设置该项) */
export interface StoreColumnCustomPayload {
	gridId: string
	fixedData?: Record<string, string> | null
	resizableData?: Record<string, number> | null
	sortData?: Record<string, number> | null
	visibleData?: Record<string, boolean> | null
}

/** 取本人指定表格的列配置(无配置 → data null) */
export function getColumnCustom(gridId: string): Promise<ColumnCustomOutput | null> {
	return service.get('/api/sysColumnCustom/detail', { params: { gridId } }) as Promise<ColumnCustomOutput | null>
}

/** 保存本人指定表格的列配置(业务键 upsert,整体覆盖) */
export function storeColumnCustom(payload: StoreColumnCustomPayload): Promise<void> {
	return service.post('/api/sysColumnCustom/store', payload) as Promise<void>
}

/** 重置(物理删)本人指定表格的列配置 */
export function resetColumnCustom(gridId: string): Promise<void> {
	return service.post('/api/sysColumnCustom/reset', { gridId }) as Promise<void>
}
