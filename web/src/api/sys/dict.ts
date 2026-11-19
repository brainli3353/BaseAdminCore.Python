/** 字典 API(契约双组:/api/sysDictType + /api/sysDictData)。 */
import service from '../request'
import type { PageResult } from '@/types/api'

export interface DictTypeOutput {
	id: number | string
	name: string | null
	code: string | null
	isEnum: boolean
	isEnable: boolean
	remark: string | null
}

export interface DictDataOutput {
	id: number | string
	dictTypeId: number | string
	code: string | null
	value: string | null
	label: string | null
	/** EP tag 类型:1 primary 2 success 3 warning 4 danger 5 info */
	tagType: number
	styleSetting: string | null
	classSetting: string | null
	orderNo: number
	isEnum: boolean
	isEnable: boolean
	extData: string | null
	remark: string | null
}

export const pageDictType = (q: { pageIndex?: number; pageSize?: number; orderBy?: string; desc?: boolean; keyword?: string | null }) =>
	service.get('/api/sysDictType/page', { params: q }) as Promise<PageResult<DictTypeOutput>>

export const addDictType = (d: { name: string; code: string; isEnum?: boolean; remark?: string }) =>
	service.post('/api/sysDictType/add', d) as Promise<number | string>

export const updateDictType = (d: { id: number | string; name: string; isEnum?: boolean; remark?: string }) =>
	service.put('/api/sysDictType/update', d) as Promise<null>

export const deleteDictType = (id: number | string) =>
	service.delete(`/api/sysDictType/delete?id=${id}`) as Promise<null>

export const pageDictData = (q: {
	dictTypeId?: number | string | null
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
	/** 关键字:Label/Value 模糊 OR(批 UX,可空=不过滤) */
	keyword?: string | null
}) =>
	service.get('/api/sysDictData/page', { params: q }) as Promise<PageResult<DictDataOutput>>

export const listDictData = (params: { typeId?: number | string | null; code?: string | null }) =>
	service.get('/api/sysDictData/list', { params }) as Promise<DictDataOutput[]>

export const addDictData = (d: {
	dictTypeId: number | string
	code: string
	value: string
	label: string
	tagType?: number
	orderNo?: number
	isEnum?: boolean
	remark?: string
}) => service.post('/api/sysDictData/add', d) as Promise<number | string>

export const updateDictData = (d: {
	id: number | string
	code: string
	value: string
	label: string
	tagType?: number
	orderNo?: number
	isEnum?: boolean
	remark?: string
}) => service.put('/api/sysDictData/update', d) as Promise<null>

export const deleteDictData = (id: number | string) =>
	service.delete(`/api/sysDictData/delete?id=${id}`) as Promise<null>

export const updateDictDataStatus = (id: number | string, isEnable: boolean) =>
	service.put('/api/sysDictData/updateStatus', { id, isEnable }) as Promise<null>
