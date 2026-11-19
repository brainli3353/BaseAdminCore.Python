/** 多页签:已打开页面缓存(路径+标题),localStorage 持久化。 */
import { defineStore } from 'pinia'
import { useLocalStorage } from '@vueuse/core'

export interface TabItem {
	path: string
	title: string
	/** 菜单 name(批 AO:页签标题据此走 i18n;旧持久化数据无该字段 → 回退 title 原文) */
	name?: string
}

export const useTabsStore = defineStore('tabs', {
	state: () => ({
		tabs: useLocalStorage<TabItem[]>('baseadmin.tabs', []),
		/** 手动刷新信号:path → 递增序号(驱动 router-view key 变化,强制重新挂载) */
		refreshSeq: {} as Record<string, number>,
		/** 正在刷新的组件名(临时移出 keep-alive include,先清掉旧缓存实例) */
		refreshing: {} as Record<string, boolean>
	}),
	actions: {
		add(tab: TabItem) {
			if (!this.tabs.some(t => t.path === tab.path)) {
				this.tabs.push(tab)
			}
		},
		remove(path: string) {
			const idx = this.tabs.findIndex(t => t.path === path)
			if (idx >= 0) {
				this.tabs.splice(idx, 1)
				return this.tabs[Math.min(idx, this.tabs.length - 1)] ?? null
			}
			return null
		},
		closeOthers(keep: string) {
			this.tabs = this.tabs.filter(t => t.path === keep)
		},
		closeAll() {
			this.tabs = []
		},
		/** 关闭左侧页签(保留 keep 及其右侧;keep 不存在时不动) */
		closeLeft(keep: string) {
			const idx = this.tabs.findIndex(t => t.path === keep)
			if (idx > 0) {
				this.tabs = this.tabs.slice(idx)
			}
		},
		/** 关闭右侧页签(保留 keep 及其左侧;keep 不存在时不动) */
		closeRight(keep: string) {
			const idx = this.tabs.findIndex(t => t.path === keep)
			if (idx >= 0 && idx < this.tabs.length - 1) {
				this.tabs = this.tabs.slice(0, idx + 1)
			}
		},
		/** 标记刷新开始:组件名临时移出 keep-alive include(清旧缓存) */
		beginRefresh(name: string) {
			this.refreshing[name] = true
		},
		endRefresh(name: string) {
			delete this.refreshing[name]
		},
		/** 递增刷新序号:router-view 的 key 变化 ⇒ 组件重新挂载 */
		bumpRefresh(path: string) {
			this.refreshSeq[path] = (this.refreshSeq[path] ?? 0) + 1
		}
	}
})
