<template>
	<div class="ba-page">
		<!-- 欢迎横幅 -->
		<div class="hero">
			<div class="hero-main">
				<h2 class="hero-title">
					{{ greeting }}, {{ userStore.user?.realName || userStore.user?.account }}
				</h2>
				<p class="hero-sub">{{ today }}</p>
			</div>
			<div class="hero-avatar">{{ avatarChar }}</div>
		</div>

		<!-- 模块快捷入口(后端菜单树驱动) -->
		<div class="module-grid">
			<div
				v-for="m in moduleEntries"
				:key="m.path"
				class="module-card"
				@click="router.push(m.path)"
			>
				<div class="module-icon">
					<el-icon :size="20"><component :is="menuIcon(m.name)" /></el-icon>
				</div>
				<span class="module-title">{{ menuTitle(m.name, m.title) }}</span>
			</div>
			<BaEmpty v-if="!moduleEntries.length" :message="t('common.noData')" class="grid-empty" />
		</div>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'Dashboard' })

import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import BaEmpty from '@/components/BaEmpty.vue'
import { useUserStore } from '@/stores/user'
import { useMenuStore } from '@/stores/menu'
import { menuIcon } from '@/utils/icons'
import { menuTitle } from '@/utils/menuTitle'

const router = useRouter()
const { t, d } = useI18n()
const userStore = useUserStore()
const menuStore = useMenuStore()

const greeting = computed(() => {
	const h = new Date().getHours()
	if (h < 6) return t('dash.greetLateNight')
	if (h < 9) return t('dash.greetMorning')
	if (h < 12) return t('dash.greetForenoon')
	if (h < 14) return t('dash.greetNoon')
	if (h < 18) return t('dash.greetAfternoon')
	return t('dash.greetEvening')
})

const today = computed(() =>
	d(new Date(), { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
)

const avatarChar = computed(() =>
	(userStore.user?.realName || userStore.user?.account || '?').slice(0, 1).toUpperCase()
)

/** 展平菜单树为入口卡片:顶级菜单 + 一级目录下的菜单(剔按钮) */
const moduleEntries = computed(() => {
	const entries: { name: string | null; title: string; path: string }[] = []
	// 剔 dashboard 自身:工作台页不应出现指向自己的入口卡(自引用视觉断裂)
	for (const node of menuStore.menus) {
		if (node.name === 'dashboard') continue
		if (node.type === 2) {
			entries.push({ name: node.name, title: node.title ?? '', path: `/${node.name}` })
		} else if (node.type === 1) {
			for (const child of node.children) {
				if (child.type === 2) {
					entries.push({ name: child.name, title: child.title ?? '', path: `/${node.name}/${child.name}` })
				}
			}
		}
	}
	return entries
})
</script>

<style scoped>
.hero {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 24px 28px;
	border-radius: var(--ba-radius-lg);
	background:
		radial-gradient(ellipse 60% 120% at 100% 0%, rgb(99 102 241 / 25%), transparent 60%),
		linear-gradient(135deg, #4f46e5, #4338ca);
	color: #fff;
	box-shadow: var(--ba-shadow);
}
.hero-title {
	margin: 0 0 6px;
	font-size: 20px;
	font-weight: 700;
}
.hero-sub {
	margin: 0;
	font-size: 13px;
	color: rgb(255 255 255 / 75%);
}
.hero-avatar {
	width: 52px;
	height: 52px;
	border-radius: 50%;
	background: rgb(255 255 255 / 18%);
	backdrop-filter: blur(6px);
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 20px;
	font-weight: 700;
}

.module-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
	gap: 12px;
}
.module-card {
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	gap: 10px;
	padding: 18px;
	background: var(--ba-bg-elevated);
	border: 1px solid var(--ba-border);
	border-radius: var(--ba-radius-lg);
	box-shadow: var(--ba-shadow-sm);
	cursor: pointer;
	transition: all 0.18s ease;
}
.module-card:hover {
	transform: translateY(-2px);
	border-color: var(--ba-brand-soft-border);
	box-shadow: var(--ba-shadow);
}
.module-icon {
	width: 38px;
	height: 38px;
	border-radius: 10px;
	background: var(--ba-brand-soft);
	color: var(--ba-brand);
	display: flex;
	align-items: center;
	justify-content: center;
}
.module-title {
	font-size: 13px;
	font-weight: 500;
	color: var(--ba-text);
}
.grid-empty {
	grid-column: 1 / -1;
}
</style>
