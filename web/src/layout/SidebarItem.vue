<template>
	<!-- 目录:子菜单(种子 type=1) -->
	<el-sub-menu v-if="item.type === 1 && item.children.length" :index="itemPath">
		<template #title>
			<el-icon><component :is="menuIcon(item.icon || item.name)" /></el-icon>
			<span>{{ menuTitle(item.name, item.title) }}</span>
		</template>
		<SidebarItem v-for="child in item.children" :key="child.id" :item="child" :base-path="itemPath" />
	</el-sub-menu>
	<!-- 菜单:路由项(种子 type=2) -->
	<el-menu-item v-else :index="itemPath">
		<el-icon><component :is="menuIcon(item.icon || item.name)" /></el-icon>
		<template #title>{{ menuTitle(item.name, item.title) }}</template>
	</el-menu-item>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { MenuNode } from '@/types/api'
import { menuIcon } from '@/utils/icons'
import { menuTitle } from '@/utils/menuTitle'

const props = withDefaults(defineProps<{ item: MenuNode; basePath?: string }>(), { basePath: '' })

const itemPath = computed(() =>
	props.basePath ? `${props.basePath}/${props.item.name}` : `/${props.item.name}`
)
</script>