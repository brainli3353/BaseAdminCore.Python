/** 分页列表共享组合式:统一 loading/rows/pager/查询参数/翻页/重置口径。 */
import { reactive, ref, type Ref } from 'vue'
import type { PageResult } from '@/types/api'

export interface PagedFetcher<T> {
	(q: Record<string, unknown>): Promise<PageResult<T>>
}

export function usePaged<T>(fetcher: PagedFetcher<T>, initialPageSize = 10) {
	const loading = ref(false)
	const rows = ref<T[]>([]) as Ref<T[]>
	const pager = reactive({
		total: 0,
		currentPage: 1,
		pageSize: initialPageSize,
		pageSizes: [10, 20, 50, 100]
	})
	/** 页面自有的查询字段(pageIndex/pageSize 由组合式注入) */
	const params = reactive<Record<string, unknown>>({})

	async function fetchPage(): Promise<void> {
		loading.value = true
		try {
			const res = await fetcher({
				...params,
				pageIndex: pager.currentPage,
				pageSize: pager.pageSize
			})
			rows.value = res.list
			pager.total = Number(res.total)
		} finally {
			loading.value = false
		}
	}

	/** 查询(回到第一页) */
	function reload(): void {
		pager.currentPage = 1
		void fetchPage()
	}

	/** 清空查询字段并回到第一页 */
	function resetQuery(): void {
		for (const k of Object.keys(params)) {
			params[k] = null
		}
		reload()
	}

	function onPageChange(p: { currentPage: number; pageSize: number }): void {
		pager.currentPage = p.currentPage
		pager.pageSize = p.pageSize
		void fetchPage()
	}

	return { loading, rows, pager, params, fetchPage, reload, resetQuery, onPageChange }
}
