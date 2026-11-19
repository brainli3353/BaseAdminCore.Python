/** 菜单图标映射:种子 Icon 字段当前为空(只存不用),前端按菜单名静态映射 EP 图标;
 * 缺失回退 'Menu'。ElementPlusIconsVue 已在 main.ts 全局注册为组件。 */
const NAME_ICON_MAP: Record<string, string> = {
	dashboard: 'Odometer',
	user: 'User',
	role: 'Collection',
	menu: 'Grid',
	sysOrg: 'OfficeBuilding',
	sysPos: 'Postcard',
	sysDict: 'Notebook',
	sysFile: 'Folder',
	sysJob: 'Timer',
	sysTenant: 'Connection',
	sysConfig: 'Setting',
	log: 'Document',
	openAccess: 'Link',
	onlineUser: 'Monitor',
	sysNotice: 'Bell',
	sysMessage: 'ChatDotSquare'
}

export function menuIcon(name: string | null | undefined): string {
	if (name && NAME_ICON_MAP[name]) {
		return NAME_ICON_MAP[name]
	}
	return 'Menu'
}
