/** 流水号配置 API(契约 /api/sysSerial/*,批 W 后端/批 BW 前端补齐)。
 * 取号端点(nextSeqNo/globalNextSeqNo)会真实消耗序列;preview 不消耗。 */
import service from '../request'
import type { PageResult } from '@/types/api'

export interface SerialOutput {
	id: number | string
	seq: number
	expy: string
	type: string | null
	resetInterval: number
	formater: string | null
	min: number
	orderNo: number
	max: number
	status: number
	remark: string | null
}

export interface SerialQuery {
	/** Type 精确 */
	type?: string | null
	/** Status 精确(0 启用/1 停用) */
	status?: number | null
	/** Type/Formater 关键字模糊(空白视为无过滤) */
	keyword?: string | null
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
	/** 创建时间范围起(批 UX B1d,CreateTime 闭区间;可空=不过滤) */
	startDate?: string | null
	/** 创建时间范围止(批 UX B1d,CreateTime 闭区间;可空=不过滤) */
	endDate?: string | null
}

export const pageSerial = (q: SerialQuery) =>
	service.get('/api/sysSerial/page', { params: q }) as Promise<PageResult<SerialOutput>>

export const detailSerial = (id: number | string) =>
	service.get('/api/sysSerial/detail', { params: { id } }) as Promise<SerialOutput>

/** add → 新配置行 Id;Type 未注册/同租户已建 → 400。 */
export const addSerial = (d: {
	type: string
	resetInterval: number
	formater: string
	min?: number
	max?: number
	orderNo?: number
	status?: number
	remark?: string | null
}) => service.post('/api/sysSerial/add', d) as Promise<number | string>

/** 只改配置列;Seq/Expy 运行时状态不可改。 */
export const updateSerial = (d: {
	id: number | string
	type: string
	resetInterval: number
	formater: string
	min?: number
	max?: number
	orderNo?: number
	status?: number
	remark?: string | null
}) => service.put('/api/sysSerial/update', d) as Promise<void>

/** 物理删;序列状态随配置作废。 */
export const deleteSerial = (id: number | string) =>
	service.delete('/api/sysSerial/delete', { params: { id } }) as Promise<void>

/** 0 启用/1 停用;停用后取号拒绝。 */
export const setSerialStatus = (id: number | string, status: number) =>
	service.post('/api/sysSerial/setStatus', null, { params: { id, status } }) as Promise<void>

/** 本租户取号(消耗序列)。 */
export const nextSeqNo = (type: string) => service.post('/api/sysSerial/nextSeqNo', { type }) as Promise<string>

/** 全局取号(跨租户共享默认租户行,消耗序列)。 */
export const globalNextSeqNo = (type: string) =>
	service.post('/api/sysSerial/globalNextSeqNo', { type }) as Promise<string>

/** 预览渲染(不消耗序列)。 */
export const previewSerial = (d: { formater: string; seq?: number; max?: number }) =>
	service.post('/api/sysSerial/preview', d) as Promise<string>

/** 已注册类型列表(text=显示名,value=类型标识)。 */
export const typeListSerial = () => service.get('/api/sysSerial/typeList') as Promise<Array<{ text: string; value: string }>>

/** 可用插槽列表(模板提示用)。 */
export const slotListSerial = () => service.get('/api/sysSerial/slotList') as Promise<string[]>
