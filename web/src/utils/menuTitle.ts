/** 菜单导航标题本地化(批 AO,6.6 补):优先 i18n `menu.<name>`(键见 i18n/{zh-CN,en-US}.ts 的 menu 段),
 * 未录入的键回退后端菜单树中文标题——DB 数据不本地化(批 AL 不做面),故必须保底、不得返回空串。
 * WHY 用 `i18n.global` 而非 `useI18n()`:侧栏/页签/路由守卫在 store 与路由上下文里取标题,不在组件 setup 内。 */
import { i18n } from '@/i18n'

export function menuTitle(name: unknown, fallback?: string | null): string {
	if (typeof name === 'string' && name) {
		const key = `menu.${name}`
		if (i18n.global.te(key)) {
			return i18n.global.t(key)
		}
	}
	return fallback ?? ''
}