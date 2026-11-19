/** 用户管理 API(契约 /api/sysUser/*)。 */
import service from '../request'
import type { PageResult } from '@/types/api'

export interface UserOutput {
	id: number | string
	account: string | null
	realName: string | null
	/** 0 正常 / 1 停用 */
	status: number
	/** 999 超管 / 777 普通 */
	accountType: number
	orgId: number | string | null
	posId: number | string | null
}

export interface UserQuery {
	account?: string | null
	pageIndex?: number
	pageSize?: number
	orgId?: number | string | null
	orderBy?: string
	desc?: boolean
	/** 状态精确过滤:0 正常 / 1 停用(批 UX,可空=不过滤) */
	status?: number | null
}

export interface AddUserInput {
	account: string
	password: string
	realName: string
	status?: number
	roleIds?: (number | string)[]
	orgId?: number | string | null
	posId?: number | string | null
}

export interface UpdateUserInput {
	id: number | string
	account: string
	realName: string
	status?: number
	orgId?: number | string | null
	posId?: number | string | null
}

export const pageUser = (q: UserQuery) =>
	service.get('/api/sysUser/page', { params: q }) as Promise<PageResult<UserOutput>>

export const addUser = (d: AddUserInput) => service.post('/api/sysUser/add', d) as Promise<number | string>

export const updateUser = (d: UpdateUserInput) => service.post('/api/sysUser/update', d) as Promise<null>

export const deleteUser = (id: number | string) => service.post(`/api/sysUser/delete?id=${id}`) as Promise<null>

export const grantUserRole = (userId: number | string, roleIds: (number | string)[]) =>
	service.post('/api/sysUser/grantRole', { userId, roleIds }) as Promise<null>

/** 回读用户现有角色 Id 集(分配角色对话框回显,全量替换口径下防误清)。 */
export const getUserRoleIds = (userId: number | string) =>
	service.get(`/api/sysUser/roleIds?userId=${userId}`) as Promise<(number | string)[]>

export const resetUserPwd = (userId: number | string, newPassword: string) =>
	service.post('/api/sysUser/resetPwd', { userId, newPassword }) as Promise<null>

export const unlockUserLogin = (account: string) =>
	service.post('/api/sysUser/unlockLogin', { account }) as Promise<null>

/** 导出用户列表（返回 Blob，前端触发下载）。 */
export const exportUser = (q: Omit<UserQuery, 'pageIndex' | 'pageSize'>) =>
	service.get('/api/sysUser/export', { params: q, responseType: 'blob' }) as unknown as Promise<Blob>
