/** 菜单 API:GET /api/sysMenu/user → 当前用户导航树(超管全量/普通按角色裁剪,均剔按钮)。 */
import service from './request'
import type { MenuNode } from '@/types/api'

export async function getUserMenuTree(): Promise<MenuNode[]> {
	const data = await service.get('/api/sysMenu/user')
	return data as unknown as MenuNode[]
}
