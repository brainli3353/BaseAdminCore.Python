<template>
	<div class="app-shell" :class="{ collapsed: appStore.sidebarCollapsed }">
		<aside class="app-sidebar">
			<Sidebar />
		</aside>
		<div class="app-body">
			<Topbar />
			<TagView />
			<main class="app-content">
				<router-view v-slot="{ Component }">
					<!-- 批 CJ/CK:keep-alive 缓存已开页签的组件——切走再切回不重新挂载(不重取数/不重置表单分页);
					     include 由 tabs store 动态推导,关闭页签即移出列表=缓存失效。
					     ★ 嵌套顺序=transition 在外、keep-alive 在内(Vue 文档规范序):
					     反序(keep-alive 包 transition)+ mode="out-in" 实测缓存恒失效(每切必重挂载,
					     批 CK 无头浏览器二分复现,vue 3.5.4x+vue-router 4.6.4 生产构建) -->
					<transition name="fade-slide" mode="out-in">
						<keep-alive :include="cachedViews" :max="30">
							<component :is="Component" :key="viewKey" />
						</keep-alive>
					</transition>
				</router-view>
			</main>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useTabsStore } from '@/stores/tabs'
import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'
import TagView from './TagView.vue'

const appStore = useAppStore()
const route = useRoute()
const router = useRouter()
const tabsStore = useTabsStore()

/** 批 CJ:keep-alive 缓存组件名单 = 已开页签 ∩ meta.keepAlive!==false。
 * 推导:页签 name(=菜单名,批 AO)首字母大写 PascalCase,与视图 SFC 的
 * defineOptions name 约定一致(见各视图 index.vue 头部);
 * 旧持久化页签无 name 字段 → 不入缓存(降级=原行为)。 */
const cachedViews = computed(() =>
	tabsStore.tabs
		.filter(t => !!t.name && router.resolve(t.path).meta.keepAlive !== false)
		.map(t => (t.name as string).charAt(0).toUpperCase() + (t.name as string).slice(1))
		// 手动刷新窗口期临时移出 include:先让 keep-alive 丢弃旧实例,再由 viewKey 变化重建
		.filter(n => !tabsStore.refreshing[n])
)

/** 手动刷新序号(右键「刷新当前」/页签刷新图标):序号变化 ⇒ 组件重新挂载并重新取数 */
const viewKey = computed(() => `${route.path}#${tabsStore.refreshSeq[route.path] ?? 0}`)
</script>

<style scoped>
.app-shell {
	display: flex;
	height: 100vh;
	overflow: hidden;
}

.app-sidebar {
	width: var(--ba-sidebar-w);
	flex-shrink: 0;
	transition: width 0.22s ease;
	overflow: hidden;
}
.app-shell.collapsed .app-sidebar {
	width: var(--ba-sidebar-w-collapsed);
}

.app-body {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	background: var(--ba-bg);
}

.app-content {
	flex: 1;
	overflow: auto;
	padding: var(--ba-content-padding);
}

.fade-slide-enter-active,
.fade-slide-leave-active {
	transition:
		opacity 0.16s ease,
		transform 0.16s ease;
}
.fade-slide-enter-from {
	opacity: 0;
	transform: translateY(6px);
}
.fade-slide-leave-to {
	opacity: 0;
}
</style>
