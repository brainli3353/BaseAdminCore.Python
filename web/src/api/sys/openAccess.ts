/** 开放接口凭据 API(契约 /api/sysOpenAccess/*;generateSignature 管理调试端点,后续迭代)。
 * AccessSecret 仅 add/resetSecret 响应一次性返回,分页不回显。 */
import service from '../request'
import type { PageResult } from '@/types/api'

export interface OpenAccessOutput {
	id: number | string
	accessKey: string
	bindUserId: number | string
	bindUserAccount: string | null
	bindTenantId: number | string
	bindTenantName: string | null
	createTime: string | null
	updateTime: string | null
}

/** add 响应:data=记录,accessSecret=服务端自动生成的 22 字符密钥(仅本次返回)。 */
export interface AddOpenAccessResult {
	data: OpenAccessOutput
	accessSecret: string
}

export interface OpenAccessQuery {
	/** 模糊 */
	accessKey?: string | null
	pageIndex?: number
	pageSize?: number
	/** 创建时间范围起(批 UX B1d,CreateTime 闭区间;可空=不过滤) */
	startDate?: string | null
	/** 创建时间范围止(批 UX B1d,CreateTime 闭区间;可空=不过滤) */
	endDate?: string | null
}

export const pageOpenAccess = (q: OpenAccessQuery) =>
	service.get('/api/sysOpenAccess/page', { params: q }) as Promise<PageResult<OpenAccessOutput>>

/** accessKey 必填唯一;secret 不接受入参,服务端自动生成。 */
export const addOpenAccess = (d: {
	accessKey: string
	bindUserId: number | string
	bindTenantId: number | string
}) => service.post('/api/sysOpenAccess/add', d) as Promise<AddOpenAccessResult>

/** 仅可改绑定用户/租户;AccessKey/AccessSecret 不可改。 */
export const updateOpenAccess = (d: {
	id: number | string
	bindUserId: number | string
	bindTenantId: number | string
}) => service.post('/api/sysOpenAccess/update', d) as Promise<null>

/** 软删。 */
export const deleteOpenAccess = (id: number | string) =>
	service.post(`/api/sysOpenAccess/delete?id=${id}`) as Promise<null>

/** 重置密钥:data=新密钥(string),旧密钥即时失效。 */
export const resetOpenAccessSecret = (id: number | string) =>
	service.post(`/api/sysOpenAccess/resetSecret?id=${id}`) as Promise<string>
