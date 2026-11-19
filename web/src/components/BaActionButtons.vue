<template>
	<div class="ba-action-buttons">
		<!-- 前 2 项直出 text 按钮(Element Plus link 类型,与既有页面操作列观感一致) -->
		<el-button
			v-for="item in directActions"
			:key="item.index"
			link
			:type="item.danger ? 'danger' : 'primary'"
			size="small"
			:disabled="item.disabled"
			@click="emit('select', item.index)"
		>
			{{ item.label }}
		</el-button>
		<!-- 第 3 项起折入"更多"(审单 B7:>3 收纳;此处 2 直出 + 其余收纳) -->
		<el-dropdown v-if="moreActions.length" trigger="click" @command="onMoreSelect">
			<el-button link type="primary" size="small">
				{{ moreLabel }}
			</el-button>
			<template #dropdown>
				<el-dropdown-menu>
					<el-dropdown-item
						v-for="item in moreActions"
						:key="item.index"
						:command="item.index"
						:disabled="item.disabled"
					>
						<span :class="{ 'ba-action-danger': item.danger }">{{ item.label }}</span>
					</el-dropdown-item>
				</el-dropdown-menu>
			</template>
		</el-dropdown>
	</div>
</template>

<script setup lang="ts">
/** 操作列收纳组件(批 UX·F0 公共件,审单 B7):操作区只暴露前 2 项直出,
 * 其余折 ElDropdown「更多」——`hidden` 项不渲染但保留原始下标。
 * emit `select(index)` 的 index = **原 actions 数组下标**(含 hidden 项),消费方按 actions 定义映射即可。
 * 用法:
 * `<BaActionButtons :actions="[{label:'编辑'},{label:'详情'},{label:'重置密码'},{label:'删除',danger:true}]" @select="onAction" />` */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

interface ActionItem {
	/** 按钮文案 */
	label: string
	/** 危险动作:直出为 danger 类型,收纳项标红 */
	danger?: boolean
	/** 隐藏(不渲染;不改变其余项 index) */
	hidden?: boolean
	/** 禁用(渲染但不可点;如系统内置行禁编辑语义) */
	disabled?: boolean
}

const props = defineProps<{ actions: ActionItem[] }>()
const emit = defineEmits<{ (e: 'select', index: number): void }>()

const { t, te } = useI18n()

/** "更多"文案:i18n 键 `common.more` 若已登记则用之,未登记回退中文
 * (F0 臂预算 ≤4 文件、不扩 i18n 两语文件;键补齐后本组件自动跟随,无需改码)。 */
const moreLabel = computed(() => (te('common.more') ? t('common.more') : '更多'))

/** 带原始下标的可见项 */
const visibleActions = computed(() =>
	props.actions.map((action, index) => ({ ...action, index })).filter(action => !action.hidden)
)
/** 前 2 项直出 */
const directActions = computed(() => visibleActions.value.slice(0, 2))
/** 第 3 项起折"更多" */
const moreActions = computed(() => visibleActions.value.slice(2))

function onMoreSelect(index: number): void {
	emit('select', index)
}
</script>

<style scoped>
.ba-action-buttons {
	display: inline-flex;
	align-items: center;
	gap: 8px;
	white-space: nowrap;
}
.ba-action-danger {
	color: var(--el-color-danger);
}
</style>