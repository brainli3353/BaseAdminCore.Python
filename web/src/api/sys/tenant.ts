/** 租户管理 API(契约 /api/sysTenant/*)。 */
import service from '../request'
import type { PageResult } from '@/types/api'

export interface TenantOutput {
	id: number | string
	name: string | null
	plan: string | null
	/** 0 启用 / 1 停用 */
	status: number
	/** null=永久有效 */
	expirationTime: string | null
	orderNo: number
	remark: string | null
	/** 租户独立库库名(展示用;未配置独立库时为 null) */
	dbName: string | null
	/** 是否已配置独立库连接串:true=数据落独立库 / false=落主库 */
	hasConnection: boolean
	createTime: string | null
}

/** 租户独立库初始化结果(建表/种子数据计数)。 */
export interface InitTenantDbOutput {
	tenantId: number | string
	configId: string
	tableCount: number
	seedCount: number
	/** 实际落库的库名,可为 null */
	database: string | null
}

export interface TenantQuery {
	name?: string | null
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
	/** 状态精确过滤:0 启用 / 1 停用(批 UX,可空=不过滤) */
	status?: number | null
	/** 创建时间范围起(批 UX B1d,CreateTime 闭区间;YYYY-MM-DD HH:mm:ss,可空=不过滤) */
	startDate?: string | null
	/** 创建时间范围止(批 UX B1d,CreateTime 闭区间;YYYY-MM-DD HH:mm:ss,可空=不过滤) */
	endDate?: string | null
}

export const pageTenant = (q: TenantQuery) =>
	service.get('/api/sysTenant/page', { params: q }) as Promise<PageResult<TenantOutput>>

export const addTenant = (d: {
	name: string
	plan?: string
	expirationTime?: string | null
	orderNo?: number
	remark?: string
	/** 租户独立库连接串:留空/不传=落主库;启用连接串加密时填密文 */
	connection?: string
	/** 库名(展示用) */
	dbName?: string
}) => service.post('/api/sysTenant/add', d) as Promise<number | string>

export const updateTenant = (d: {
	id: number | string
	name?: string
	plan?: string
	expirationTime?: string | null
	orderNo?: number
	remark?: string
	/** 租户独立库连接串:部分更新语义,仅在实际填写时提交,不传=不修改 */
	connection?: string
	/** 库名(展示用) */
	dbName?: string
}) => service.post('/api/sysTenant/update', d) as Promise<null>

export const deleteTenant = (id: number | string) =>
	service.post(`/api/sysTenant/delete?id=${id}`) as Promise<null>

export const setTenantStatus = (id: number | string, status: number) =>
	service.post('/api/sysTenant/setStatus', { id, status }) as Promise<null>

/** 初始化该租户的独立库(建表/初始化种子数据);需先配置连接串。 */
export const initTenantDb = (id: number | string) =>
	service.post(`/api/sysTenant/initDb?id=${id}`) as Promise<InitTenantDbOutput>
