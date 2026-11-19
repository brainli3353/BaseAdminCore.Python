<template>
	<div class="ba-empty-tip" :class="`is-${state}`">
		<!-- 加载态:spinner + common.loading(复用既有键,需求单 #2 口径) -->
		<template v-if="state === 'loading'">
			<el-icon class="ba-empty-spin"><Loading /></el-icon>
			<span>{{ message || t('common.loading') }}</span>
		</template>
		<!-- 错误态:必须可区分于空态(文案含原因;给 @retry 监听才出重试入口) -->
		<template v-else-if="state === 'error'">
			<el-icon><WarningFilled /></el-icon>
			<span class="ba-empty-error-text">{{ message || t('common.loadError') }}</span>
			<el-button v-if="hasRetry" link type="primary" size="small" @click="emit('retry')">
				{{ t('common.retry') }}
			</el-button>
		</template>
		<!-- 空态 -->
		<template v-else>
			<span>{{ message || t('common.noData') }}</span>
		</template>
	</div>
</template>

<script setup lang="ts">
/** 三态空态占位(批 BD #2,需求单「表格加载态与统一交互」2026-09-29——本单最高优先):
 * 禁止"加载中"与"暂无数据"共用一个空态文案(三态塌缩两态——下游 12 视图 `{{ xxxErr || t('common.noData') }}`
 * 与框架 sys 列表页同病实证);空插槽显式接 state,消费方一行换掉塌缩写法:
 * `<BaEmpty :state="loading ? 'loading' : err ? 'error' : 'empty'" :message="err" @retry="refresh" />`
 * 文案缺省:loading→common.loading / empty→common.noData / error→common.loadError(或 message 传入原因)。 */
import { computed, useAttrs } from 'vue'
import { useI18n } from 'vue-i18n'
import { Loading, WarningFilled } from '@element-plus/icons-vue'

withDefaults(
	defineProps<{
		/** 三态之一:loading=加载中 / empty=真没数据 / error=加载失败(区别于空) */
		state?: 'loading' | 'empty' | 'error'
		/** 覆写文案(error 态传失败原因;缺省按 state 取 i18n 键) */
		message?: string
	}>(),
	{ state: 'empty', message: undefined }
)

const emit = defineEmits<{ (e: 'retry'): void }>()

// 仅当消费方监听 @retry 才渲染重试按钮(无监听时不出一个点了没反应的按钮)
const attrs = useAttrs()
const hasRetry = computed(() => !!attrs.onRetry)

const { t } = useI18n()
</script>

<style scoped>
.ba-empty-spin {
	margin-right: 6px;
	animation: ba-empty-rotate 1.2s linear infinite;
}
.ba-empty-error-text {
	color: var(--ba-danger);
}
@keyframes ba-empty-rotate {
	to {
		transform: rotate(360deg);
	}
}
</style>
