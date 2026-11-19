<template>
	<el-skeleton v-if="showSkeleton" :animated="true" :count="1" class="ba-skeleton" :class="`is-${variant}`">
		<template #template>
			<!-- 卡片版式:标题条 + 若干文本行(通用占位,逐页定制版式仍归业务——框架给积木不给版式) -->
			<template v-if="variant === 'card'">
				<el-skeleton-item variant="h3" class="ba-skeleton__title" />
				<el-skeleton-item
					v-for="i in rows"
					:key="i"
					variant="text"
					class="ba-skeleton__row"
					:style="{ width: `${ROW_WIDTHS[(i - 1) % ROW_WIDTHS.length]}%` }"
				/>
			</template>
			<!-- 表格版式:行 × 4 列单元条 -->
			<template v-else>
				<div v-for="r in rows" :key="r" class="ba-skeleton__trow">
					<el-skeleton-item v-for="c in 4" :key="c" variant="text" class="ba-skeleton__cell" />
				</div>
			</template>
		</template>
	</el-skeleton>
	<!-- 非骨架期渲染真实内容(loading=false 或未过阈值) -->
	<slot v-else />
</template>

<script setup lang="ts">
/** 首屏骨架屏(批 BD #3,需求单「表格加载态与统一交互」2026-09-29):Element Plus `el-skeleton` 封装,
 * 定位"可选组件+指引"——内置**显示阈值 delay(缺省 300ms)**:加载未满阈值不渲染骨架,
 * 避免快接口"闪骨架"比"闪空"更噪(需求单 §3#3 的时序指引落地为组件缺省行为,不只靠文档)。
 * 用法:`<BaSkeleton :loading="isInitialLoading" variant="table" :rows="6"><真实表格/></BaSkeleton>`
 * (与 el-skeleton 同构:loading=true 出骨架,false 出默认插槽)。
 * 指引口径:只绑**首载态**(usePolling.isInitialLoading),轮询静默刷新不出骨架(刷新不清屏)。 */
import { computed, onScopeDispose, ref, watch } from 'vue'

const props = withDefaults(
	defineProps<{
		/** 是否加载中(建议绑 usePolling().isInitialLoading) */
		loading?: boolean
		/** 预置版式:card=标题+文本行 / table=行×4 列(逐页定制版式属业务,自建 el-skeleton 即可) */
		variant?: 'card' | 'table'
		/** 行数(card=文本行数 / table=行数) */
		rows?: number
		/** 显示阈值(毫秒):加载持续超过该时长才出骨架,0=立即;缺省 300(需求单时序指引) */
		delay?: number
	}>(),
	{ loading: false, variant: 'card', rows: 3, delay: 300 }
)

// 文本行宽伪随机序列(确定性:骨架不闪变;首行最宽的观感由序列轮转给出)
const ROW_WIDTHS = [92, 66, 84, 58, 74, 90, 62]

/** 已过显示阈值的加载态(loading=true 持续 delay 毫秒后才为 true) */
const delayedLoading = ref(false)
let timer: ReturnType<typeof setTimeout> | undefined

watch(
	() => props.loading,
	loading => {
		if (timer !== undefined) {
			clearTimeout(timer)
			timer = undefined
		}
		if (!loading) {
			delayedLoading.value = false
			return
		}
		if (props.delay <= 0) {
			delayedLoading.value = true
			return
		}
		timer = setTimeout(() => {
			delayedLoading.value = true
		}, props.delay)
	},
	{ immediate: true }
)

const showSkeleton = computed(() => props.loading && delayedLoading.value)

onScopeDispose(() => {
	if (timer !== undefined) {
		clearTimeout(timer)
	}
})
</script>

<style scoped>
.ba-skeleton {
	display: block;
}
.ba-skeleton__title {
	display: block;
	width: 32%;
	height: 18px;
	margin-bottom: 14px;
}
.ba-skeleton__row {
	display: block;
	height: 14px;
	margin-bottom: 10px;
}
.ba-skeleton__trow {
	display: flex;
	gap: 16px;
	margin-bottom: 14px;
}
.ba-skeleton__cell {
	flex: 1;
	height: 16px;
}
</style>
