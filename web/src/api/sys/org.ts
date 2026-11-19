/** 机构管理 API(契约 /api/sysOrg/*)。 */
import service from '../request'
import type { PageResult } from '@/types/api'

export interface OrgOutput {
	/** G33:后端 long id 经 JSON 出口为 string(读侧兼容 number,故并集) */
	id: number | string
	pid: number | string
	name: string | null
	code: string | null
	sort: number
	remark: string | null
	status: number
	children: OrgOutput[]
	/** 非超管视角下范围外机构=true(选择器禁用,防越权挂靠) */
	disabled: boolean
}

export interface OrgQuery {
	name?: string | null
	pageIndex?: number
	pageSize?: number
}

export const pageOrg = (q: OrgQuery) =>
	service.get('/api/sysOrg/page', { params: q }) as Promise<PageResult<OrgOutput>>

/** 机构全树(递归;叶子 Children 为空列表) */
export const getOrgTree = () => service.get('/api/sysOrg/tree') as Promise<OrgOutput[]>

export const addOrg = (d: { pid: number | string; name: string; code?: string; sort?: number; remark?: string; status?: number }) =>
	service.post('/api/sysOrg/add', d) as Promise<number | string>

export const updateOrg = (d: { id: number | string; pid: number | string; name: string; code?: string; sort?: number; remark?: string; status?: number }) =>
	service.post('/api/sysOrg/update', d) as Promise<null>

export const deleteOrg = (id: number | string) => service.post(`/api/sysOrg/delete?id=${id}`) as Promise<null>
