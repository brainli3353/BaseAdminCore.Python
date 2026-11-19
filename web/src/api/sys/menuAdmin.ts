/** 菜单管理 API(契约 /api/sysMenu/*;管理端全量树含按钮,权限键 sysMenu/page)。 */
import service from '../request'
import type { MenuNode } from '@/types/api'

/** 管理端菜单全树(含按钮行) */
export const getFullMenuTree = () => service.get('/api/sysMenu/page') as Promise<MenuNode[]>

export const addMenu = (d: {
	pid: number | string
	name: string
	title: string
	type: number
	permission?: string
	orderNo?: number
	icon?: string
	/** 是否缓存: 0 不缓存 / 1 缓存(缺省 1) */
	isKeepAlive?: number
}) => service.post('/api/sysMenu/add', d) as Promise<number | string>

export const updateMenu = (d: {
	id: number | string
	pid: number | string
	name: string
	title: string
	type: number
	permission?: string
	orderNo?: number
	icon?: string
	/** 是否缓存: 0 不缓存 / 1 缓存(缺省不修改) */
	isKeepAlive?: number
}) => service.post('/api/sysMenu/update', d) as Promise<null>

export const deleteMenu = (id: number | string) => service.post(`/api/sysMenu/delete?id=${id}`) as Promise<null>

/** 菜单启停(批 CH G28:0 启用/1 停用;停用节点+整子树退出登录菜单树) */
export const setStatusMenu = (id: number | string, status: number) =>
	service.post(`/api/sysMenu/setStatus?id=${id}&status=${status}`) as Promise<null>
