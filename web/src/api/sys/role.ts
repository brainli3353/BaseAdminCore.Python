/** 角色管理 API(契约 /api/sysRole/*)。 */
import service from '../request'
import type { PageResult } from '@/types/api'

export interface RoleOutput {
	id: number | string
	name: string | null
	code: string | null
	remark: string | null
	/** 内置角色:前端禁用删除/授权入口 */
	sysFlag: boolean
	/** 数据范围(task_013):1 全部/2 本机构及下级/3 本机构/4 仅本人/5 自定义 */
	dataScope: number
}

export interface RoleQuery {
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
	/** 关键字:Name/Code 模糊 OR(批 UX,可空=不过滤) */
	keyword?: string | null
}

export const pageRole = (q: RoleQuery) =>
	service.get('/api/sysRole/page', { params: q }) as Promise<PageResult<RoleOutput>>

export const addRole = (d: { name: string; code: string; remark?: string; dataScope?: number }) =>
	service.post('/api/sysRole/add', d) as Promise<number | string>

export const updateRole = (d: { id: number | string; name: string; remark?: string; dataScope?: number }) =>
	service.post('/api/sysRole/update', d) as Promise<null>

export const deleteRole = (id: number | string) => service.post(`/api/sysRole/delete?id=${id}`) as Promise<null>

export const grantRoleMenu = (roleId: number | string, menuIds: (number | string)[]) =>
	service.post('/api/sysRole/grantMenu', { roleId, menuIds }) as Promise<null>

/** 角色已授权菜单 Id 集合(菜单树勾选态回读) */
export const getRoleMenus = (roleId: number | string) =>
	service.get(`/api/sysRole/menu?roleId=${roleId}`) as Promise<(number | string)[]>

/** 提交数据范围自定义机构集(批 BH):全量替换语义(空数组=清空;非自定义范围由前端传空集) */
export const grantRoleOrg = (roleId: number | string, orgIds: (number | string)[]) =>
	service.post('/api/sysRole/grantOrg', { roleId, orgIds }) as Promise<null>

/** 角色数据范围自定义机构 Id 集回读(与 grantRoleOrg 对偶) */
export const getRoleOrgs = (roleId: number | string) =>
	service.get(`/api/sysRole/org?roleId=${roleId}`) as Promise<(number | string)[]>

/** 提交角色接口黑名单:全量替换语义(空数组=解除全部禁用;变更即失效该角色全员权限缓存) */
export const grantRoleApi = (roleId: number | string, apiList: string[]) =>
	service.post('/api/sysRole/grantApi', { roleId, apiList }) as Promise<null>

/** 回读角色当前接口黑名单(权限标识列表;空集=未禁用任何接口) */
export const getRoleApis = (roleId: number | string) =>
	service.get(`/api/sysRole/api?roleId=${roleId}`) as Promise<string[]>

export const copyRole = (id: number | string) => service.post('/api/sysRole/copy', { id }) as Promise<number | string>

/** 字段权限(表-列授权)授权项:元素形如 "表名:列名"(如 "sys_user:Account") */
export type RoleTableItem = string

/** 角色已授权字段项回读结果(与 grantRoleTable 对偶) */
export interface RoleTableOutput {
	roleId: number | string
	items: RoleTableItem[]
}

/** 字段权限授权树:表 + 其列(服务端已排除系统表与审计字段) */
export interface TableColumnOutput {
	tableName: string
	tableComment: string | null
	columns: { columnName: string; columnComment: string | null }[]
}

/** 提交角色字段权限:全量替换语义(提交什么就是什么,空数组=清空) */
export const grantRoleTable = (roleId: number | string, items: RoleTableItem[]) =>
	service.post('/api/sysRole/grantTable', { roleId, items }) as Promise<null>

/** 回读角色当前已授权的「表:列」项(与 grantRoleTable 对偶) */
export const getRoleTable = (roleId: number | string) =>
	service.get(`/api/sysRole/table?roleId=${roleId}`) as Promise<RoleTableOutput>

/** 字段权限授权树数据源(GET,无参;返回数组) */
export const getAllTableColumn = () => service.get('/api/sysRole/allTableColumn') as Promise<TableColumnOutput[]>

/* ── 表级开关(受管表) ─────────────────────────── */

/** 表级开关回读项(GET /api/sysRole/tableScopes):全部可配置表 + 受管状态 */
export interface TableScopeOutput {
	tableName: string
	tableComment: string | null
	/** 是否受管:true=非超管用户按角色列白名单裁剪;授权会自动开启,本面板用于手动开/关 */
	enabled: boolean
	/** 已配置字段权限的角色数(>0 且 enabled=false 时前端提示"有授权但已停管") */
	grantedRoleCount: number
	/** 该表可配置列数 */
	columnCount: number
}

/** 切换表级开关入参(POST /api/sysRole/tableScope;tableName 与回读逐字一致) */
export interface TableScopeRequest {
	tableName: string
	enabled: boolean
}

/** 表级开关(受管表)回读:全部可配置表 + 受管状态 */
export const getTableScopes = () => service.get('/api/sysRole/tableScopes') as Promise<TableScopeOutput[]>

/** 切换表级开关:成功返回空;失败交全局拦截器统一提示 */
export const setTableScope = (d: TableScopeRequest) => service.post('/api/sysRole/tableScope', d) as Promise<null>
