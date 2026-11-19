/** 全局守卫:登录门禁 + 动态路由懒加载 + 页签登记 + 路由进度条。 */
import type { Router } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { getAccessToken } from '@/utils/token'
import { useUserStore } from '@/stores/user'
import { useMenuStore } from '@/stores/menu'
import { useTabsStore } from '@/stores/tabs'
import { startRealtime } from '@/utils/realtime'

NProgress.configure({ showSpinner: false })

export function setupGuard(router: Router): void {
	const userStore = useUserStore()
	const menuStore = useMenuStore()
	const tabsStore = useTabsStore()

	router.beforeEach(async to => {
		NProgress.start()

		const loggedIn = !!getAccessToken()

		// 公开页(登录/404):已登录访问登录页 → 回首页
		if (to.meta.public) {
			if (loggedIn && to.path === '/login') {
				return { path: '/' }
			}
			return true
		}

		// 未登录 → 登录页(带回跳)
		if (!loggedIn) {
			return { path: '/login', query: { redirect: to.fullPath } }
		}

		// 已登录但动态路由未挂载:拉用户信息(权限键)+ 菜单树 → addRoute 后重解析
		if (!menuStore.loaded) {
			try {
				const me = await userStore.fetchMe()
				await menuStore.load(router, me.permissions)
				// 批 CL G31:登录态首次验证成功=实时通道挂载点(幂等;登出/401 失效经 user.reset 断开)
				startRealtime()
			} catch {
				userStore.reset()
				return { path: '/login' }
			}
			// WHY 按 fullPath 重解析,禁止 {...to} 展开:动态路由挂载前 to 已被
			// catch-all 匹配(name=notFound+旧 params),展开会把"按名导航到 404"
			// 原样回传 → 登录后 /dashboard 永远 404(2026-09-16 测试版 e2e 实证)
			return { path: to.fullPath, replace: true }
		}

		// 页签登记(带标题的非公开页);name 供页签标题走 i18n(批 AO)
		if (to.meta.title && to.path !== '/') {
			tabsStore.add({ path: to.path, title: to.meta.title as string, name: (to.name as string) || undefined })
		}
		return true
	})

	router.afterEach(() => {
		NProgress.done()
	})
}
