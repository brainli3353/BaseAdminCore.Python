/** 动态菜单/路由:后端菜单树(/api/sysMenu/user)→ vue-router 动态路由 + 侧边栏数据。
 * 组件解析约定(框架通用件):菜单 name 逐级拼路径,组件固定落 views/<拼接路径>/index.vue——
 * 顶级菜单 views/dashboard/index.vue;目录子菜单 views/<目录Name>/<菜单Name>/index.vue
 * (按种子目录名,2026-09-30 六目录:sys/config/monitor/logAudit/messageCenter/tooling)。
 * 文件缺失时回退"建设中"占位页(下游业务 fork 后按约定补视图即可,框架不阻塞)。 */
import { defineStore } from 'pinia'
import type { RouteComponent, RouteRecordRaw } from 'vue-router'
import * as menuApi from '@/api/menu'
import type { MenuNode } from '@/types/api'

const viewModules = import.meta.glob('../views/**/*.vue')

function resolveView(path: string): () => Promise<RouteComponent> {
	const key = `../views/${path}/index.vue`
	return (viewModules[key] as (() => Promise<RouteComponent>) | undefined) ?? buildPlaceholder()
}

function buildPlaceholder(): () => Promise<RouteComponent> {
	// .vue 模块命名空间 → 组件类型断言(SFC default 即组件)
	return () => import('@/views/placeholder/index.vue') as unknown as Promise<RouteComponent>
}

/** 递归按 orderNo 稳定排序(服务端已排,此处防御性再排) */
function sortTree(nodes: MenuNode[]): MenuNode[] {
	return [...nodes].sort((a, b) => a.orderNo - b.orderNo).map(n => ({ ...n, children: sortTree(n.children) }))
}

function toRoutes(nodes: MenuNode[], parentPath = ''): RouteRecordRaw[] {
	return sortTree(nodes)
		.filter(n => n.type !== 3 && !!n.name) // 剔按钮(双保险:服务端已剔)
		.map(n => {
			const name = n.name as string // 上方 filter 已剔空名
			const path = parentPath ? `${parentPath}/${name}` : `/${name}`
			if (n.type === 1) {
				// 目录:无 component 透传记录,仅承载子路由(布局由顶层 / 路由统一提供);
				// 运行时合法,类型上 vue-router 未收录该形态 → 显式断言
				return { path, name, meta: { title: n.title ?? '', icon: n.icon ?? '' }, children: toRoutes(n.children, path) } as RouteRecordRaw
			}
			return {
				path,
				name,
				component: resolveView(path.replace(/^\//, '')),
				// keepAlive 由菜单管理配置(sys_menu.IsKeepAlive)决定:
				// 1=缓存(切走再切回保留表单/分页/滚动),0=不缓存(每次切回重新挂载并重新取数)。
				// 页签关闭即从 keep-alive include 列表移出、组件缓存即时失效。
				meta: { title: n.title ?? '', icon: n.icon ?? '', keepAlive: n.isKeepAlive !== 0 }
			}
		})
}

export const useMenuStore = defineStore('menu', {
	state: () => ({
		loaded: false,
		/** 侧边栏导航树(目录+菜单) */
		menus: [] as MenuNode[],
		/** 按钮权限键集合(驱动 v-perm 显隐;超管前端直通) */
		permissions: [] as string[]
	}),
	actions: {
		/** 登录后调用:拉导航树 → 注册动态路由(挂为布局根路由 'root' 的子) */
		async load(router: import('vue-router').Router, permissions: string[]) {
			const tree = await menuApi.getUserMenuTree()
			this.menus = sortTree(tree)
			this.permissions = permissions
			for (const route of toRoutes(tree)) {
				router.addRoute('root', route)
			}
			this.loaded = true
		},
		reset() {
			this.loaded = false
			this.menus = []
			this.permissions = []
		}
	}
})
