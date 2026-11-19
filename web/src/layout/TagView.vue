<template>
	<div v-if="tabsStore.tabs.length" class="tagbar">
		<div class="tagbar-list">
			<div
				v-for="tab in tabsStore.tabs"
				:key="tab.path"
				class="tag"
				:class="{ active: route.path === tab.path }"
				@click="go(tab.path)"
				@contextmenu.prevent="openContextMenu($event, tab.path)"
			>
				<span class="tag-dot" />
				<span class="tag-title">{{ menuTitle(tab.name, tab.title) }}</span>
				<el-icon
					v-if="route.path === tab.path"
					class="tag-refresh"
					:title="t('layout.refreshTab')"
					@click.stop="refreshTab(tab.path)"
				>
					<Refresh />
				</el-icon>
				<el-icon
					v-if="tabsStore.tabs.length > 1"
					class="tag-close"
					@click.stop="close(tab.path)"
				>
					<Close />
				</el-icon>
			</div>
		</div>
		<span class="tagbar-clear" @click="closeOthers(route.path)">
			{{ t('layout.closeTabs') }}
		</span>

		<!-- 页签右键菜单(对齐源仓:刷新当前 / 关闭当前 / 关闭其他 / 关闭左侧 / 关闭右侧 / 关闭全部) -->
		<teleport to="body">
			<ul
				v-if="contextMenu.visible"
				class="tag-context"
				:style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
				@click.stop
				@contextmenu.prevent
			>
				<li class="tag-context-item" @click="onRefresh">
					<el-icon><Refresh /></el-icon>
					<span>{{ t('layout.refreshTab') }}</span>
				</li>
				<li class="tag-context-item" @click="onCloseCurrent">
					<el-icon><Close /></el-icon>
					<span>{{ t('layout.closeCurrent') }}</span>
				</li>
				<li class="tag-context-divider" />
				<li class="tag-context-item" @click="onCloseOthers">
					<el-icon><CircleClose /></el-icon>
					<span>{{ t('layout.closeOthers') }}</span>
				</li>
				<li class="tag-context-item" @click="onCloseLeft">
					<el-icon><ArrowLeft /></el-icon>
					<span>{{ t('layout.closeLeft') }}</span>
				</li>
				<li class="tag-context-item" @click="onCloseRight">
					<el-icon><ArrowRight /></el-icon>
					<span>{{ t('layout.closeRight') }}</span>
				</li>
				<li class="tag-context-divider" />
				<li class="tag-context-item" @click="onCloseAll">
					<el-icon><Delete /></el-icon>
					<span>{{ t('layout.closeAll') }}</span>
				</li>
			</ul>
		</teleport>
	</div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
	ArrowLeft,
	ArrowRight,
	CircleClose,
	Close,
	Delete,
	Refresh
} from '@element-plus/icons-vue'
import { useTabsStore } from '@/stores/tabs'
import { menuTitle } from '@/utils/menuTitle'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const tabsStore = useTabsStore()

interface ContextMenuState {
	visible: boolean
	x: number
	y: number
	currentPath: string
}

const contextMenu = reactive<ContextMenuState>({
	visible: false,
	x: 0,
	y: 0,
	currentPath: ''
})

/** 菜单尺寸(用于贴边翻转,避免超出视口) */
const MENU_W = 150
const MENU_H = 232

function go(path: string): void {
	if (path !== route.path) {
		router.push(path)
	}
}

function close(path: string): void {
	const next = tabsStore.remove(path)
	if (path === route.path) {
		if (next) {
			router.push(next.path)
		} else {
			router.push('/')
		}
	}
}

function closeOthers(keep: string): void {
	tabsStore.closeOthers(keep)
	if (route.path !== keep) {
		router.push(keep)
	}
}

/**
 * 刷新指定页签:临时移出 keep-alive include 丢弃旧实例 → 递增 key 触发重新挂载 →
 * 恢复 include(缓存重新建立)。非当前页签先切过去再刷新(与源仓右键「刷新当前」同语义)。
 */
async function refreshTab(path: string): Promise<void> {
	if (path !== route.path) {
		await router.push(path)
	}
	const tab = tabsStore.tabs.find(t => t.path === path)
	const name = tab?.name
	const componentName = name ? name.charAt(0).toUpperCase() + name.slice(1) : ''
	if (componentName) {
		tabsStore.beginRefresh(componentName)
		await nextTick()
	}
	tabsStore.bumpRefresh(path)
	await nextTick()
	if (componentName) {
		tabsStore.endRefresh(componentName)
	}
}

function openContextMenu(event: MouseEvent, path: string): void {
	event.preventDefault()
	contextMenu.currentPath = path
	contextMenu.x = Math.min(event.clientX, window.innerWidth - MENU_W - 8)
	contextMenu.y = Math.min(event.clientY, window.innerHeight - MENU_H - 8)
	contextMenu.visible = true
}

function closeContextMenu(): void {
	contextMenu.visible = false
}

function onRefresh(): void {
	const path = contextMenu.currentPath
	closeContextMenu()
	void refreshTab(path)
}

function onCloseCurrent(): void {
	const path = contextMenu.currentPath
	closeContextMenu()
	close(path)
}

function onCloseOthers(): void {
	const keep = contextMenu.currentPath
	closeContextMenu()
	closeOthers(keep)
}

function onCloseLeft(): void {
	const keep = contextMenu.currentPath
	closeContextMenu()
	tabsStore.closeLeft(keep)
	ensureActiveTabExists(keep)
}

function onCloseRight(): void {
	const keep = contextMenu.currentPath
	closeContextMenu()
	tabsStore.closeRight(keep)
	ensureActiveTabExists(keep)
}

function onCloseAll(): void {
	closeContextMenu()
	tabsStore.closeAll()
	if (route.path !== '/') {
		router.push('/')
	}
}

/** 批量关闭后若当前页签已被移除,落到保留页签(keep) */
function ensureActiveTabExists(keep: string): void {
	if (route.path !== keep && !tabsStore.tabs.some(t => t.path === route.path)) {
		router.push(keep)
	}
}

function handleDocumentClick(): void {
	closeContextMenu()
}

function handleKeydown(event: KeyboardEvent): void {
	if (event.key === 'Escape') {
		closeContextMenu()
	}
}

watch(
	() => route.path,
	() => closeContextMenu()
)

document.addEventListener('click', handleDocumentClick)
document.addEventListener('keydown', handleKeydown)
window.addEventListener('resize', handleDocumentClick)

onBeforeUnmount(() => {
	document.removeEventListener('click', handleDocumentClick)
	document.removeEventListener('keydown', handleKeydown)
	window.removeEventListener('resize', handleDocumentClick)
})
</script>

<style scoped>
.tagbar {
	height: var(--ba-tagbar-h);
	flex-shrink: 0;
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 0 12px;
	background: var(--ba-bg-elevated);
	border-bottom: 1px solid var(--ba-border);
}

.tagbar-list {
	display: flex;
	align-items: center;
	gap: 6px;
	overflow-x: auto;
	flex: 1;
	min-width: 0;
	scrollbar-width: none;
}
.tagbar-list::-webkit-scrollbar {
	display: none;
}

.tag {
	display: flex;
	align-items: center;
	gap: 6px;
	height: 26px;
	padding: 0 10px;
	border-radius: 13px;
	border: 1px solid var(--ba-border);
	background: var(--ba-bg-elevated);
	font-size: 12px;
	color: var(--ba-text-secondary);
	cursor: pointer;
	white-space: nowrap;
	transition: all 0.15s ease;
	user-select: none;
}
.tag:hover {
	border-color: var(--ba-border-strong);
	color: var(--ba-text);
}
.tag.active {
	background: var(--ba-brand-soft);
	border-color: var(--ba-brand-soft-border);
	color: var(--ba-brand);
	font-weight: 500;
}
.tag-dot {
	width: 6px;
	height: 6px;
	border-radius: 50%;
	background: var(--ba-text-disabled);
}
.tag.active .tag-dot {
	background: var(--ba-brand);
}
.tag-refresh,
.tag-close {
	font-size: 11px;
	color: var(--ba-text-tertiary);
	border-radius: 50%;
	padding: 1px;
}
.tag-refresh:hover {
	color: var(--ba-brand);
	background: var(--ba-brand-soft);
}
.tag-close:hover {
	color: var(--ba-danger);
	background: rgb(239 68 68 / 12%);
}

.tagbar-clear {
	font-size: 12px;
	color: var(--ba-text-tertiary);
	cursor: pointer;
	padding: 2px 8px;
	border-radius: var(--ba-radius-sm);
	flex-shrink: 0;
}
.tagbar-clear:hover {
	color: var(--ba-text);
	background: var(--ba-bg-hover);
}

.tag-context {
	position: fixed;
	z-index: 3000;
	min-width: 140px;
	margin: 0;
	padding: 4px 0;
	list-style: none;
	background: var(--ba-bg-elevated);
	border: 1px solid var(--ba-border);
	border-radius: var(--ba-radius);
	box-shadow: 0 6px 20px rgb(0 0 0 / 12%);
	user-select: none;
}
.tag-context-item {
	display: flex;
	align-items: center;
	gap: 8px;
	height: 32px;
	padding: 0 14px;
	font-size: 13px;
	color: var(--ba-text);
	cursor: pointer;
	transition: background 0.15s ease;
}
.tag-context-item:hover {
	background: var(--ba-bg-hover);
}
.tag-context-item .el-icon {
	font-size: 15px;
	color: var(--ba-text-secondary);
}
.tag-context-divider {
	height: 1px;
	margin: 4px 0;
	list-style: none;
	background: var(--ba-border);
}
</style>
