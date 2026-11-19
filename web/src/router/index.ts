/** 路由:静态骨架(登录/布局根/404)+ 登录后动态挂载后端菜单路由。
 * 布局根路由 name='root',component=AppLayout;动态路由经 addRoute('root', ...) 挂为其子。 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

declare module 'vue-router' {
	interface RouteMeta {
		/** 公开页(登录/404):不挂登录门禁 */
		public?: boolean
		/** 页面标题(页签/侧边栏) */
		title?: string
		/** 菜单图标 */
		icon?: string
		/** 批 CJ:多页签 keep-alive 是否缓存该页组件(缺省 true;关闭页签即移出 include 列表、缓存失效) */
		keepAlive?: boolean
	}
}

export const staticRoutes: RouteRecordRaw[] = [
	{
		path: '/login',
		name: 'login',
		component: () => import('@/views/login/index.vue'),
		meta: { public: true }
	},
	{
		path: '/',
		name: 'root',
		component: () => import('@/layout/AppLayout.vue'),
		redirect: '/dashboard',
		children: []
	},
	{
		path: '/:pathMatch(.*)*',
		name: 'notFound',
		component: () => import('@/views/error/404.vue')
		// WHY 无 meta.public:catch-all 会匹配一切未知路径(含 / 重定向来的
		// /dashboard),带 public 会使未登录用户跳过登录门禁直接看到 404
		// (2026-09-16 测试版实测:首开未登录落地 404 而非登录页)
	}
]

export const router = createRouter({
	history: createWebHistory(),
	routes: staticRoutes
})

// WHY 不在此处 setupGuard:守卫内取 pinia store,须在 app.use(pinia) 之后调用
// (模块顶层早于 main.ts 主体执行,store 无 pinia 上下文 → 启动即抛 TypeError 白屏;
//  2026-09-16 测试版首开实证),改由 main.ts 在 pinia 安装后调用
export default router
