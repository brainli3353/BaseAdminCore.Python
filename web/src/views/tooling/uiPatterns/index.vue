<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('uiPatterns.title') }}</h3>
				<p class="ba-sub">{{ t('uiPatterns.sub') }}</p>
			</div>
		</div>

		<!-- #2 三态占位:loading / empty / error 不再塌缩 -->
		<div class="ba-card ba-card-padded">
			<h4 class="demo-card-title">{{ t('uiPatterns.secThreeState') }}</h4>
			<p class="ba-hint">{{ t('uiPatterns.threeStateHint') }}</p>
			<el-radio-group v-model="threeState" size="small">
				<el-radio-button value="loading">{{ t('uiPatterns.stateLoading') }}</el-radio-button>
				<el-radio-button value="empty">{{ t('uiPatterns.stateEmpty') }}</el-radio-button>
				<el-radio-button value="error">{{ t('uiPatterns.stateError') }}</el-radio-button>
			</el-radio-group>
			<BaEmpty
				class="demo-empty"
				:state="threeState"
				:message="threeState === 'error' ? t('uiPatterns.inlineErrorDemo') : undefined"
				@retry="simulateRetry"
			/>
		</div>

		<!-- #1 分区加载遮罩:v-ba-loading -->
		<div class="ba-card ba-card-padded">
			<h4 class="demo-card-title">{{ t('uiPatterns.secMask') }}</h4>
			<p class="ba-hint">{{ t('uiPatterns.maskHint') }}</p>
			<el-switch v-model="maskOn" />
			<div v-ba-loading="maskOn" class="demo-mask-box">
				{{ t('uiPatterns.maskDemoContent') }}
			</div>
		</div>

		<!-- #3 首屏骨架屏:BaSkeleton(card/table 版式,300ms 阈值内建) -->
		<div class="ba-card ba-card-padded">
			<h4 class="demo-card-title">{{ t('uiPatterns.secSkeleton') }}</h4>
			<p class="ba-hint">{{ t('uiPatterns.skeletonHint') }}</p>
			<el-switch v-model="skeletonOn" />
			<div class="grid2">
				<div>
					<p class="ba-hint">{{ t('uiPatterns.skeletonCard') }}</p>
					<BaSkeleton :loading="skeletonOn" variant="card" :rows="3">
						<div class="ba-hint">{{ t('uiPatterns.skeletonReal') }}</div>
					</BaSkeleton>
				</div>
				<div>
					<p class="ba-hint">{{ t('uiPatterns.skeletonTable') }}</p>
					<BaSkeleton :loading="skeletonOn" variant="table" :rows="4">
						<div class="ba-hint">{{ t('uiPatterns.skeletonReal') }}</div>
					</BaSkeleton>
				</div>
			</div>
		</div>

		<!-- #4 轮询首载/刷新分离:usePolling -->
		<div class="ba-card ba-card-padded">
			<h4 class="demo-card-title">{{ t('uiPatterns.secPolling') }}</h4>
			<p class="ba-hint">{{ t('uiPatterns.pollingHint') }}</p>
			<div class="demo-actions">
				<el-button size="small" :loading="isRefreshing" @click="refresh">{{ t('uiPatterns.pollingManual') }}</el-button>
				<el-button size="small" @click="togglePolling">
					{{ pollingPaused ? t('uiPatterns.pollingResume') : t('uiPatterns.pollingPause') }}
				</el-button>
				<el-tag v-if="isInitialLoading" type="warning" size="small">{{ t('uiPatterns.pollingInitial') }}</el-tag>
				<el-tag v-else-if="isRefreshing" type="info" size="small">{{ t('uiPatterns.pollingRefreshing') }}</el-tag>
			</div>
			<BaEmpty v-if="isInitialLoading" state="loading" class="demo-empty" />
			<p v-else class="ba-hint">{{ t('uiPatterns.pollingTicks', { n: tickCount }) }}</p>
		</div>

		<!-- #5 行内错误:错误≠空,含原因与重试 -->
		<div class="ba-card ba-card-padded">
			<h4 class="demo-card-title">{{ t('uiPatterns.secInlineError') }}</h4>
			<p class="ba-hint">{{ t('uiPatterns.inlineErrorHint') }}</p>
			<div class="ba-inline-error">
				<el-icon><WarningFilled /></el-icon>
				<span>{{ t('uiPatterns.inlineErrorDemo') }}</span>
				<el-button link type="primary" size="small" @click="inlineRetryCount++">
					{{ t('uiPatterns.inlineErrorRetry') }}{{ inlineRetryCount > 0 ? ` ×${inlineRetryCount}` : '' }}
				</el-button>
			</div>
		</div>

		<!-- #6 pending 计数:能力 opt-in,默认不挂任何进度效果 -->
		<div class="ba-card ba-card-padded">
			<h4 class="demo-card-title">{{ t('uiPatterns.secPending') }}</h4>
			<p class="ba-hint">{{ t('uiPatterns.pendingHint') }}</p>
			<div class="demo-actions">
				<el-button size="small" @click="firePendingDemo">{{ t('uiPatterns.pendingFire') }}</el-button>
				<el-tag size="small" type="primary">{{ t('uiPatterns.pendingNow', { n: pendingCount }) }}</el-tag>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'UiPatterns' })

/** 交互模式示例页(批 BD,需求单「表格加载态与统一交互」2026-09-29 的一页示例):
 * 六件统一交互件(#1 v-ba-loading/#2 BaEmpty/#3 BaSkeleton/#4 usePolling/#5 ba-inline-error/#6 pendingCount)
 * 各一节,零后端依赖(除 #6 演示触发 auth/me),页面无按钮权限键。
 * 用法口径见 框架使用指南.md §48;本页同时是下游业务视图改造的对照样板。 */
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { WarningFilled } from '@element-plus/icons-vue'
import BaEmpty from '@/components/BaEmpty.vue'
import BaSkeleton from '@/components/BaSkeleton.vue'
import { usePolling } from '@/composables/usePolling'
import { pendingCount } from '@/api/request'
import { getMe } from '@/api/auth'

const { t } = useI18n()

function sleep(ms: number): Promise<void> {
	return new Promise(resolve => setTimeout(resolve, ms))
}

/* #2 三态:radio 切换;重试 = 回 loading 800ms 后再落 error(模拟仍失败的分块) */
const threeState = ref<'loading' | 'empty' | 'error'>('loading')
async function simulateRetry(): Promise<void> {
	threeState.value = 'loading'
	await sleep(800)
	threeState.value = 'error'
}
// 进页先落 loading 态,800ms 后落 empty(演示三态流转;重试按钮再走 loading→error)
setTimeout(() => {
	if (threeState.value === 'loading') {
		threeState.value = 'empty'
	}
}, 800)

/* #1 遮罩 */
const maskOn = ref(false)

/* #3 骨架 */
const skeletonOn = ref(false)

/* #4 轮询:3s 一轮,每轮模拟 400ms 取数;首载态/刷新态由组合式分离 */
const tickCount = ref(0)
const { isInitialLoading, isRefreshing, refresh, start, stop } = usePolling(
	async () => {
		await sleep(400)
		tickCount.value++
	},
	{ interval: 3000 }
)
const pollingPaused = ref(false)
function togglePolling(): void {
	if (pollingPaused.value) {
		start()
		pollingPaused.value = false
	} else {
		stop()
		pollingPaused.value = true
	}
}

/* #5 行内错误重试演示(仅计数,无真实请求) */
const inlineRetryCount = ref(0)

/* #6 pending 计数演示:触发 3 个并发真实请求(auth/me 登录即可,轻量) */
function firePendingDemo(): void {
	for (let i = 0; i < 3; i++) {
		setTimeout(() => {
			void getMe().catch(() => undefined)
		}, i * 150)
	}
}
</script>

<style scoped>
.demo-card-title {
	margin: 0 0 6px;
	font-size: 14px;
	font-weight: 600;
}
.demo-empty {
	margin-top: 16px;
	padding: 24px 0;
}
.demo-mask-box {
	margin-top: 12px;
	min-height: 96px;
	display: flex;
	align-items: center;
	justify-content: center;
	border: 1px dashed var(--ba-border-strong);
	border-radius: var(--ba-radius-sm);
	color: var(--ba-text-secondary);
}
.grid2 {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 24px;
	margin-top: 12px;
}
.demo-actions {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-top: 8px;
}
</style>
