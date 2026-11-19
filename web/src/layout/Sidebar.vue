<template>
	<div class="sidebar-inner">
		<div class="brand">
			<div class="brand-logo">{{ brandInitial() }}</div>
			<span v-show="!appStore.sidebarCollapsed" class="brand-text">{{ brand.name }}</span>
		</div>
		<el-menu
			:default-active="route.path"
			:collapse="appStore.sidebarCollapsed"
			:collapse-transition="false"
			router
			class="side-menu"
		>
			<SidebarItem v-for="item in menuStore.menus" :key="item.id" :item="item" />
		</el-menu>
	</div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { brand, brandInitial } from '@/config/brand'
import { useAppStore } from '@/stores/app'
import { useMenuStore } from '@/stores/menu'
import SidebarItem from './SidebarItem.vue'

const route = useRoute()
const appStore = useAppStore()
const menuStore = useMenuStore()
</script>

<style scoped>
.sidebar-inner {
	height: 100%;
	display: flex;
	flex-direction: column;
	background: var(--ba-nav-bg);
}

.brand {
	height: var(--ba-topbar-h);
	display: flex;
	align-items: center;
	gap: 10px;
	padding: 0 16px;
	flex-shrink: 0;
}
.brand-logo {
	width: 30px;
	height: 30px;
	border-radius: 8px;
	background: linear-gradient(135deg, #6366f1, #4f46e5);
	color: #fff;
	font-weight: 700;
	font-size: 16px;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}
.brand-text {
	color: #f9fafb;
	font-size: 15px;
	font-weight: 600;
	letter-spacing: 0.3px;
	white-space: nowrap;
}

.side-menu {
	--el-menu-bg-color: transparent;
	--el-menu-text-color: var(--ba-nav-text);
	--el-menu-active-color: #a5b4fc;
	--el-menu-hover-bg-color: var(--ba-nav-bg-active);
	--el-menu-item-height: 42px;
	border-right: none;
	flex: 1;
	overflow-y: auto;
	overflow-x: hidden;
	padding: 6px 8px 16px;
}
.side-menu .el-menu-item,
.side-menu .el-sub-menu__title {
	border-radius: var(--ba-radius);
	margin: 2px 0;
}
.side-menu .el-menu-item.is-active {
	background: rgb(79 70 229 / 22%);
	color: var(--ba-nav-text-active);
	font-weight: 500;
}
.side-menu .el-menu-item.is-active .el-icon {
	color: var(--ba-brand-hover);
}
.side-menu .el-sub-menu .el-menu {
	background: transparent !important;
}
</style>
