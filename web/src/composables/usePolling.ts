/** 轮询共享组合式(批 BD #4,需求单「表格加载态与统一交互」2026-09-29):
 * 把"定时刷新面"的**首载态**与**刷新态**分离,收敛业务视图各自手写的
 * `onMounted → refresh → setInterval → onBeforeUnmount 清 timer` + `loading` 防重入模板
 * (下游 IntelCore 12 个情报视图同构实证,详见需求单 §3#4)。
 *
 * 三态口径(与 BaEmpty/BaSkeleton 配套,见指南 §48):
 * - `isInitialLoading`:首次取数尚未落定——驱动骨架屏/分区加载占位,让等待期可区分于"暂无数据";
 * - `isRefreshing`:非首次的在途刷新——可绑刷新按钮小圈;`silentRefresh: true` 时保持恒 false
 *   (数据整体替换的静默轮询,刷新按钮每 10–30s 闪小圈=无反馈价值的新噪声,需求单 §2 实证);
 * - 错误:fn 内自管(逐分区 err ref + 三态展示);组合式统一吞掉 fn 的拒绝,
 *   不向全局抛未处理 rejection(定时器路径无人接盘),此为**显式契约**而非无说明吞异常。
 *
 * 防重入:上一轮未落定时跳过本轮 tick(等价手写 `if (loading.value) return`)。
 * 卸载自清:在组件 setup 作用域内调用时经 onScopeDispose 自动 stop;setup 外调用(如模块级)
 * 不注册清理钩子,须自行 stop。 */
import { getCurrentScope, onScopeDispose, ref, type Ref } from 'vue'

export interface UsePollingOptions {
	/** 轮询间隔(毫秒);interval 到点即触发,上一轮未落定则跳过该轮 */
	interval: number
	/** 建后立即跑第一轮(首载),默认 true;false 时首载由首个 interval tick 或手动 refresh() 驱动 */
	immediate?: boolean
	/** 刷新期完全静默(不置 isRefreshing),适合"数据整体替换"的自动轮询;默认 false */
	silentRefresh?: boolean
}

export interface UsePollingReturn {
	/** 首次取数尚未落定(只在前端等待期出现一次,失败落定同样置 false——错误态由 fn 内展示) */
	isInitialLoading: Ref<boolean>
	/** 非首次的在途刷新(silentRefresh 时恒 false;手动 refresh 亦置位) */
	isRefreshing: Ref<boolean>
	/** 手动触发一轮(页头刷新按钮);防重入同 tick */
	refresh: () => Promise<void>
	/** 停止轮询(清 timer;组件卸载自动调用,页面上也可手动暂停) */
	stop: () => void
	/** (重新)启动轮询 timer;重复调用幂等 */
	start: () => void
}

export function usePolling(fn: () => Promise<void> | void, options: UsePollingOptions): UsePollingReturn {
	const { interval, immediate = true, silentRefresh = false } = options

	const isInitialLoading = ref(false)
	const isRefreshing = ref(false)
	let timer: ReturnType<typeof setInterval> | undefined
	let running = false
	/** 首轮是否已落定(落定后 isInitialLoading 不再置位,后续刷新走 isRefreshing) */
	let settledOnce = false

	/** 一轮取数:防重入 + 首载/刷新态分派 + 统一吞错(错误态由 fn 内三态口径自管) */
	async function tick(): Promise<void> {
		if (running) {
			return
		}
		running = true
		if (!settledOnce) {
			isInitialLoading.value = true
		} else if (!silentRefresh) {
			isRefreshing.value = true
		}
		try {
			await fn()
		} catch {
			/* 显式契约:业务错误态在 fn 内自管(逐分区 err ref);组合式不向全局抛 */
		} finally {
			running = false
			settledOnce = true
			isInitialLoading.value = false
			isRefreshing.value = false
		}
	}

	function stop(): void {
		if (timer !== undefined) {
			clearInterval(timer)
			timer = undefined
		}
	}

	function start(): void {
		if (timer === undefined) {
			timer = setInterval(() => {
				void tick()
			}, interval)
		}
	}

	if (immediate) {
		void tick()
	}
	start()

	// 仅在组件 setup / effect 作用域内注册清理钩子;模块级调用(无作用域)须自行 stop
	if (getCurrentScope()) {
		onScopeDispose(stop)
	}

	return { isInitialLoading, isRefreshing, refresh: tick, stop, start }
}
