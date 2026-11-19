<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('log.title') }}</h3>
				<p class="ba-sub">{{ t('log.sub') }}</p>
			</div>
		</div>

		<div class="ba-card">
			<!-- 无任一日志查询权限:整体空态。tab 分块按 page 键 v-if(同 sysDatabase hasPerm 先例:
				 v-perm 只摘 DOM 拦不住拉数,tab 场景须整块不渲染,未授权既不显示也不请求) -->
			<BaEmpty v-if="!canOp && !canLogin && !canEx && !canHttp && !canDiff" :message="t('log.noPerm')" />
			<el-tabs v-else v-model="activeTab">
				<!-- ── 操作日志 ─────────────────────────── -->
				<el-tab-pane v-if="canOp" :label="t('log.tabOp')" name="op">					<div class="search-row">
						<el-input v-model="opQuery.account" :placeholder="t('log.phAccountExact')" clearable class="search-input" @keyup.enter="opReload" />
						<el-input v-model="opQuery.controllerName" :placeholder="t('log.phControllerFuzzy')" clearable class="search-input" @keyup.enter="opReload" />
						<el-select v-model="opQuery.success" class="search-select">
							<el-option :label="t('log.optAllResult')" :value="OPT_ALL" />
							<el-option :label="t('log.optSuccess')" :value="true" />
							<el-option :label="t('log.optFail')" :value="false" />
						</el-select>
						<el-date-picker
							v-model="opQuery.range"
							type="daterange"
							value-format="YYYY-MM-DD HH:mm:ss"
							:default-time="defaultTime"
							:start-placeholder="t('log.phStartDate')"
							:end-placeholder="t('log.phEndDate')"
							clearable
							class="search-date"
						/>
						<el-button type="primary" @click="opReload">{{ t('common.search') }}</el-button>
						<el-button @click="opReset">{{ t('common.reset') }}</el-button>
					</div>
					<vxe-grid
						:loading="opLoading"
						:data="opRows"
						:columns="opColumns"
						:pager-config="opPager"
						:row-config="{ keyField: 'id' }"
						:sort-config="{ remote: true }"
						@page-change="opOnPageChange"
						@sort-change="opOnSortChange"
					>
						<template #cell_success="{ row }">
							<span class="st" :class="row.success ? 'st-ok' : 'st-off'">{{ row.success ? t('log.optSuccess') : t('log.optFail') }}</span>
						</template>
						<!-- 操作列:详情(请求参数/返回结果;批 AZ 参照口径,按钮权限键 sysLogOp/detail) -->
						<template #op_ops="{ row }">
							<el-button v-perm="'sysLogOp/detail'" link type="primary" size="small" @click="openOpDetail(row)">
								{{ t('log.btnDetail') }}
							</el-button>
						</template>
					</vxe-grid>
				</el-tab-pane>

				<!-- ── 登录日志 ─────────────────────────── -->
				<el-tab-pane v-if="canLogin" :label="t('log.tabLogin')" name="login">
					<div class="search-row">
						<el-input v-model="loginQuery.account" :placeholder="t('log.phAccountExact')" clearable class="search-input" @keyup.enter="loginReload" />
						<el-select v-model="loginQuery.status" class="search-select">
							<el-option :label="t('log.optAllResult')" :value="OPT_ALL" />
							<el-option :label="t('log.optSuccess')" :value="true" />
							<el-option :label="t('log.optFail')" :value="false" />
						</el-select>
						<el-select v-model="loginQuery.loginType" :placeholder="t('log.phLoginType')" class="search-select">
							<el-option :label="t('common.all')" :value="OPT_ALL" />
							<el-option :label="t('log.loginTypeLogin')" value="login" />
							<el-option :label="t('log.loginTypeLogout')" value="logout" />
						</el-select>
						<el-date-picker
							v-model="loginQuery.range"
							type="daterange"
							value-format="YYYY-MM-DD HH:mm:ss"
							:default-time="defaultTime"
							:start-placeholder="t('log.phStartDate')"
							:end-placeholder="t('log.phEndDate')"
							clearable
							class="search-date"
						/>
						<el-button type="primary" @click="loginReload">{{ t('common.search') }}</el-button>
						<el-button @click="loginReset">{{ t('common.reset') }}</el-button>
					</div>
					<vxe-grid
						:loading="loginLoading"
						:data="loginRows"
						:columns="loginColumns"
						:pager-config="loginPager"
						:row-config="{ keyField: 'id' }"
						:sort-config="{ remote: true }"
						@page-change="loginOnPageChange"
						@sort-change="loginOnSortChange"
					>
						<template #cell_status="{ row }">
							<span class="st" :class="row.status ? 'st-ok' : 'st-off'">{{ row.status ? t('log.optSuccess') : t('log.optFail') }}</span>
						</template>
					</vxe-grid>
				</el-tab-pane>

				<!-- ── 异常日志 ─────────────────────────── -->
				<el-tab-pane v-if="canEx" :label="t('log.tabEx')" name="ex">
					<div class="search-row">
						<el-input v-model="exQuery.account" :placeholder="t('log.phAccountExact')" clearable class="search-input" @keyup.enter="exReload" />
						<el-input v-model="exQuery.controllerName" :placeholder="t('log.phControllerFuzzy')" clearable class="search-input" @keyup.enter="exReload" />
						<el-input v-model="exQuery.remoteIp" :placeholder="t('log.phRemoteIpExact')" clearable class="search-input" @keyup.enter="exReload" />
						<el-select v-model="exQuery.logLevel" :placeholder="t('log.phLogLevel')" class="search-select">
							<el-option :label="t('common.all')" :value="OPT_ALL" />
							<el-option v-for="lv in logLevelOptions" :key="lv" :label="lv" :value="lv" />
						</el-select>
						<el-date-picker
							v-model="exQuery.range"
							type="daterange"
							value-format="YYYY-MM-DD HH:mm:ss"
							:default-time="defaultTime"
							:start-placeholder="t('log.phStartDate')"
							:end-placeholder="t('log.phEndDate')"
							clearable
							class="search-date"
						/>
						<el-button type="primary" @click="exReload">{{ t('common.search') }}</el-button>
						<el-button @click="exReset">{{ t('common.reset') }}</el-button>
					</div>
					<vxe-grid
						:loading="exLoading"
						:data="exRows"
						:columns="exColumns"
						:pager-config="exPager"
						:row-config="{ keyField: 'id' }"
						:sort-config="{ remote: true }"
						@page-change="exOnPageChange"
						@sort-change="exOnSortChange"
					>
						<template #row_ops="{ row }">
							<el-button v-perm="'sysLogEx/detail'" link type="primary" size="small" @click="openDetail(row)">
								{{ t('log.btnDetail') }}
							</el-button>
						</template>
					</vxe-grid>
				</el-tab-pane>

				<!-- ── Http 出站日志 ─────────────────────────── -->
				<el-tab-pane v-if="canHttp" :label="t('log.tabHttp')" name="http">
					<div class="search-row">
						<el-input v-model="httpQuery.account" :placeholder="t('log.phAccountExact')" clearable class="search-input" @keyup.enter="httpReload" />
						<el-input v-model="httpQuery.url" :placeholder="t('log.phUrlFuzzy')" clearable class="search-input" @keyup.enter="httpReload" />
						<el-select v-model="httpQuery.httpMethod" class="search-select">
							<el-option :label="t('log.optAllMethod')" :value="OPT_ALL" />
							<el-option v-for="m in HTTP_METHODS" :key="m" :label="m" :value="m" />
						</el-select>
						<el-select v-model="httpQuery.statusCode" class="search-select">
							<el-option :label="t('log.optAllStatus')" :value="OPT_ALL" />
							<el-option v-for="c in HTTP_STATUS_CODES" :key="c" :label="String(c)" :value="c" />
						</el-select>
						<el-date-picker
							v-model="httpQuery.range"
							type="daterange"
							value-format="YYYY-MM-DD HH:mm:ss"
							:default-time="defaultTime"
							:start-placeholder="t('log.phStartDate')"
							:end-placeholder="t('log.phEndDate')"
							clearable
							class="search-date"
						/>
						<el-button type="primary" @click="httpReload">{{ t('common.search') }}</el-button>
						<el-button @click="httpReset">{{ t('common.reset') }}</el-button>
					</div>
					<vxe-grid
						:loading="httpLoading"
						:data="httpRows"
						:columns="httpColumns"
						:pager-config="httpPager"
						:row-config="{ keyField: 'id' }"
						:sort-config="{ remote: true }"
						@page-change="httpOnPageChange"
						@sort-change="httpOnSortChange"
					>
						<!-- 状态列:带异常/无响应/4xx-5xx 一律显红(与操作/登录日志 st-ok/st-off 同口径) -->
						<template #http_status="{ row }">
							<span class="st" :class="httpStatusBad(row) ? 'st-off' : 'st-ok'">{{ row.statusCode ?? '—' }}</span>
						</template>
						<template #http_elapsed="{ row }">{{ row.elapsedMs ?? '—' }}</template>
						<template #http_ops="{ row }">
							<el-button v-perm="'sysLogHttp/detail'" link type="primary" size="small" @click="openHttpDetail(row)">
								{{ t('log.btnDetail') }}
							</el-button>
						</template>
					</vxe-grid>
				</el-tab-pane>

				<!-- ── 差异日志(批 CE,闭环 CC 批 D2) ─────────────────────────── -->
				<el-tab-pane v-if="canDiff" :label="t('log.tabDiff')" name="diff">
					<div class="search-row">
						<el-date-picker
							v-model="diffQuery.range"
							type="daterange"
							value-format="YYYY-MM-DD HH:mm:ss"
							:default-time="defaultTime"
							:start-placeholder="t('log.phStartDate')"
							:end-placeholder="t('log.phEndDate')"
							clearable
							class="search-date"
						/>
						<el-button type="primary" @click="diffReload">{{ t('common.search') }}</el-button>
						<el-button @click="diffReset">{{ t('common.reset') }}</el-button>
					</div>
					<vxe-grid
						:loading="diffLoading"
						:data="diffRows"
						:columns="diffColumns"
						:pager-config="diffPager"
						:row-config="{ keyField: 'id' }"
						:sort-config="{ remote: true }"
						@page-change="diffOnPageChange"
						@sort-change="diffOnSortChange"
					>
						<!-- 操作类型:INSERT/UPDATE/DELETE 三色(参照 logdiff row_diffType 同口径) -->
						<template #diff_type="{ row }">
							<el-tag v-if="row.diffType === 'INSERT'" type="primary">{{ row.diffType }}</el-tag>
							<el-tag v-else-if="row.diffType === 'UPDATE'" type="success">{{ row.diffType }}</el-tag>
							<el-tag v-else type="danger">{{ row.diffType ?? '—' }}</el-tag>
						</template>
						<template #diff_elapsed="{ row }">{{ row.elapsed ?? '—' }}</template>
						<template #diff_ops="{ row }">
							<el-button v-perm="'sysLogDiff/detail'" link type="primary" size="small" @click="openDiffDetail(row)">
								{{ t('log.btnDetail') }}
							</el-button>
						</template>
					</vxe-grid>
				</el-tab-pane>
			</el-tabs>
		</div>

		<!-- 操作日志详情对话框(请求参数/返回结果两大字段;批 AZ 参照口径) -->
		<el-dialog v-model="opDetail.visible" :title="t('log.opDetailTitle')" width="760px" destroy-on-close>
			<p v-if="opDetail.data" class="dialog-meta">
				{{ opDetail.data.controllerName }}/{{ opDetail.data.actionName }} · {{ opDetail.data.httpMethod }} ·
				{{ opDetail.data.remoteIp }} · {{ t('log.labelElapsed') }} {{ opDetail.data.elapsedMs }}ms ·
				{{ opDetail.data.account }} · {{ opDetail.data.createTime }} ·
				{{ opDetail.data.success ? t('log.optSuccess') : t('log.optFail') }}
			</p>
			<div v-ba-loading="opDetail.loading">
				<h4 class="pre-title">{{ t('log.detailRequestParam') }}</h4>
				<pre class="log-pre">{{ opDetail.data?.requestParam || t('log.empty') }}</pre>
				<h4 class="pre-title">{{ t('log.detailReturnResult') }}</h4>
				<pre class="log-pre">{{ opDetail.data?.returnResult || t('log.empty') }}</pre>
			</div>
			<template #footer>
				<el-button @click="opDetail.visible = false">{{ t('log.btnClose') }}</el-button>
			</template>
		</el-dialog>

		<!-- 异常详情对话框 -->
		<el-dialog v-model="detail.visible" :title="t('log.detailTitle')" width="760px" destroy-on-close>
			<p v-if="detail.data" class="dialog-meta">
				{{ detail.data.controllerName }}/{{ detail.data.actionName }} · {{ detail.data.httpMethod }} ·
				{{ detail.data.account }} · {{ detail.data.createTime }} · traceId={{ detail.data.traceId }}
			</p>
			<div v-ba-loading="detail.loading">
				<h4 class="pre-title">{{ t('log.detailRequestParam') }}</h4>
				<pre class="log-pre">{{ detail.data?.requestParam || t('log.empty') }}</pre>
				<h4 class="pre-title">{{ t('log.detailReturnResult') }}</h4>
				<pre class="log-pre">{{ detail.data?.returnResult || t('log.empty') }}</pre>
				<h4 class="pre-title">{{ t('log.detailException') }}</h4>
				<pre class="log-pre log-pre-ex">{{ detail.data?.exception || t('log.empty') }}</pre>
			</div>
			<template #footer>
				<el-button @click="detail.visible = false">{{ t('log.btnClose') }}</el-button>
			</template>
		</el-dialog>

		<!-- Http 日志详情对话框 -->
		<el-dialog v-model="httpDetail.visible" :title="t('log.httpDetailTitle')" width="760px" destroy-on-close>
			<p v-if="httpDetail.data" class="dialog-meta">
				{{ httpDetail.data.httpMethod }} {{ httpDetail.data.requestUrl }} · {{ t('common.status') }} {{ httpDetail.data.statusCode ?? '—' }} ·
				{{ t('log.labelElapsed') }} {{ httpDetail.data.elapsedMs ?? '—' }}ms · {{ httpDetail.data.account }} · {{ httpDetail.data.createTime }} ·
				traceId={{ httpDetail.data.traceId }}
			</p>
			<div v-ba-loading="httpDetail.loading">
				<h4 class="pre-title">{{ t('log.detailRequestHeaders') }}</h4>
				<pre class="log-pre">{{ httpDetail.data?.requestHeaders || t('log.empty') }}</pre>
				<h4 class="pre-title">{{ t('log.detailRequestBody') }}</h4>
				<pre class="log-pre">{{ httpDetail.data?.requestBody || t('log.empty') }}</pre>
				<h4 class="pre-title">{{ t('log.detailResponseBody') }}</h4>
				<pre class="log-pre">{{ httpDetail.data?.responseBody || t('log.empty') }}</pre>
				<h4 class="pre-title">{{ t('log.detailException') }}</h4>
				<pre class="log-pre log-pre-ex">{{ httpDetail.data?.exception || t('log.empty') }}</pre>
			</div>
			<template #footer>
				<el-button @click="httpDetail.visible = false">{{ t('log.btnClose') }}</el-button>
			</template>
		</el-dialog>

		<!-- 差异日志详情对话框(四大字段:SQL/参数/操作前/操作后;批 CE) -->
		<el-dialog v-model="diffDetail.visible" :title="t('log.diffDetailTitle')" width="760px" destroy-on-close>
			<p v-if="diffDetail.data" class="dialog-meta">
				{{ diffDetail.data.businessData }} · {{ diffDetail.data.diffType }} ·
				{{ t('log.labelElapsed') }} {{ diffDetail.data.elapsed ?? '—' }}ms ·
				{{ diffDetail.data.createUserName }} · {{ diffDetail.data.createTime }}
			</p>
			<div v-ba-loading="diffDetail.loading">
				<h4 class="pre-title">{{ t('log.diffLabelSql') }}</h4>
				<pre class="log-pre">{{ diffDetail.data?.sql || t('log.empty') }}</pre>
				<h4 class="pre-title">{{ t('log.diffLabelParameters') }}</h4>
				<pre class="log-pre">{{ diffDetail.data?.parameters || t('log.empty') }}</pre>
				<h4 class="pre-title">{{ t('log.diffLabelBefore') }}</h4>
				<pre class="log-pre">{{ diffDetail.data?.beforeData || t('log.empty') }}</pre>
				<h4 class="pre-title">{{ t('log.diffLabelAfter') }}</h4>
				<pre class="log-pre">{{ diffDetail.data?.afterData || t('log.empty') }}</pre>
			</div>
			<template #footer>
				<el-button @click="diffDetail.visible = false">{{ t('log.btnClose') }}</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
/** 「全部」哨兵：该查询条件为 null ＝ 不带此筛选（业务语义，运行时必须保持 null）。
 *  批 B6：EP 按需后 `el-option.value` 的 prop 类型不再含 null ⇒ 只收口类型、不改值（改成 '' 会让"全部"变成"按空串筛选"）。 */
const OPT_ALL = null as unknown as string | number
	defineOptions({ name: 'Log' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import BaEmpty from '@/components/BaEmpty.vue'
import * as logsApi from '@/api/sys/logs'
import type { SysLogOpOutput, SysLogOpDetailOutput, SysLogLoginOutput, SysLogExOutput, SysLogExDetailOutput, SysLogHttpOutput, SysLogHttpDetailOutput, SysLogDiffOutput, SysLogDiffDetailOutput } from '@/api/sys/logs'
import { usePaged } from '@/composables/usePaged'
import { useMenuStore } from '@/stores/menu'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const menuStore = useMenuStore()
const userStore = useUserStore()

/** 与 v-perm 同口径(超管直通):tab 分块按 page 键 v-if——未授权 tab 既不显示也不拉数(批 CC D1)。 */
function hasPerm(key: string): boolean {
	return userStore.user?.accountType === 999 || menuStore.permissions.includes(key)
}
const canOp = hasPerm('sysLogOp/page')
const canLogin = hasPerm('sysLogLogin/page')
const canEx = hasPerm('sysLogEx/page')
const canHttp = hasPerm('sysLogHttp/page')
const canDiff = hasPerm('sysLogDiff/page')

type DateRange = [string, string] | null
/** 范围选择默认时刻:起 00:00:00,止 23:59:59(后端闭区间) */
const defaultTime: [Date, Date] = [new Date(2000, 0, 1, 0, 0, 0), new Date(2000, 0, 1, 23, 59, 59)]

const activeTab = ref('op')

/* ── 操作日志 ─────────────────────────────── */
const opQuery = reactive({
	account: '',
	controllerName: '',
	success: null as boolean | null,
	range: null as DateRange,
	orderBy: '' as string,
	desc: false as boolean
})
const {
	loading: opLoading,
	rows: opRows,
	pager: opPager,
	fetchPage: opFetch,
	reload: opReload,
	onPageChange: opOnPageChange
} = usePaged<SysLogOpOutput>(q =>
	logsApi.pageLogOp({
		account: opQuery.account || null,
		controllerName: opQuery.controllerName || null,
		success: opQuery.success,
		startTime: opQuery.range?.[0] ?? null,
		endTime: opQuery.range?.[1] ?? null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: opQuery.orderBy || undefined,
		desc: opQuery.orderBy ? opQuery.desc : undefined
	})
)

function opReset(): void {
	Object.assign(opQuery, { account: '', controllerName: '', success: null, range: null, orderBy: '', desc: false })
	opReload()
}

function opOnSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	opQuery.orderBy = order ? property : ''
	opQuery.desc = order === 'desc'
	opReload()
}

const opColumns = computed(() => [
	{ field: 'controllerName', title: t('log.colController'), minWidth: 130, sortable: true, showOverflow: 'tooltip' as const },
	{ field: 'actionName', title: t('log.colAction'), minWidth: 110, sortable: true },
	{ field: 'httpMethod', title: t('log.colMethod'), width: 80, sortable: true },
	{ field: 'remoteIp', title: t('log.colRemoteIp'), width: 130, sortable: true },
	{ field: 'elapsedMs', title: t('log.colElapsed'), width: 100, sortable: true },
	{ field: 'account', title: t('log.colAccount'), width: 110, sortable: true },
	{ field: 'success', title: t('log.colResult'), width: 90, sortable: true, slots: { default: 'cell_success' } },
	{ field: 'createTime', title: t('log.colTime'), width: 170, sortable: true },
	{ title: t('common.operations'), width: 90, fixed: 'right' as const, slots: { default: 'op_ops' } }
])

/** 操作日志详情对话框(请求参数/返回结果;批 AZ 参照口径,按钮权限键 sysLogOp/detail) */
const opDetail = reactive({
	visible: false,
	loading: false,
	data: null as SysLogOpDetailOutput | null
})

async function openOpDetail(row: SysLogOpOutput): Promise<void> {
	opDetail.visible = true
	opDetail.loading = true
	opDetail.data = null
	try {
		opDetail.data = await logsApi.logOpDetail(row.id)
	} finally {
		opDetail.loading = false
	}
}

/* ── 登录日志 ─────────────────────────────── */
const loginQuery = reactive({
	account: '',
	status: null as boolean | null,
	loginType: null as string | null,
	range: null as DateRange,
	orderBy: '' as string,
	desc: false as boolean
})
const {
	loading: loginLoading,
	rows: loginRows,
	pager: loginPager,
	fetchPage: loginFetch,
	reload: loginReload,
	onPageChange: loginOnPageChange
} = usePaged<SysLogLoginOutput>(q =>
	logsApi.pageLogLogin({
		account: loginQuery.account || null,
		status: loginQuery.status,
		loginType: loginQuery.loginType,
		startTime: loginQuery.range?.[0] ?? null,
		endTime: loginQuery.range?.[1] ?? null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: loginQuery.orderBy || undefined,
		desc: loginQuery.orderBy ? loginQuery.desc : undefined
	})
)

function loginReset(): void {
	Object.assign(loginQuery, { account: '', status: null, loginType: null, range: null, orderBy: '', desc: false })
	loginReload()
}

function loginOnSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	loginQuery.orderBy = order ? property : ''
	loginQuery.desc = order === 'desc'
	loginReload()
}

const loginColumns = computed(() => [
	{ field: 'account', title: t('log.colAccount'), width: 120, sortable: true },
	{ field: 'remoteAddr', title: 'IP', width: 130, sortable: true },
	{ field: 'browser', title: t('log.colBrowser'), width: 120, sortable: true },
	{ field: 'os', title: t('log.colOs'), width: 120, sortable: true },
	{ field: 'status', title: t('log.colResult'), width: 90, sortable: true, slots: { default: 'cell_status' } },
	{ field: 'message', title: t('log.colMessage'), minWidth: 140, sortable: true, showOverflow: 'tooltip' as const },
	{ field: 'loginType', title: t('log.colLoginType'), width: 100, sortable: true },
	{ field: 'createTime', title: t('log.colTime'), width: 170, sortable: true }
])

/* ── 异常日志 ─────────────────────────────── */
/** 后端 SysLogEx.LogLevel 落 Microsoft.Extensions.Logging.LogLevel 枚举名串(批 UX)。 */
const logLevelOptions = ['Trace', 'Information', 'Warning', 'Error', 'Critical', 'None']
const exQuery = reactive({
	account: '',
	controllerName: '',
	remoteIp: '',
	logLevel: null as string | null,
	range: null as DateRange,
	orderBy: '' as string,
	desc: false as boolean
})
const {
	loading: exLoading,
	rows: exRows,
	pager: exPager,
	fetchPage: exFetch,
	reload: exReload,
	onPageChange: exOnPageChange
} = usePaged<SysLogExOutput>(q =>
	logsApi.pageLogEx({
		account: exQuery.account || null,
		controllerName: exQuery.controllerName || null,
		remoteIp: exQuery.remoteIp || null,
		logLevel: exQuery.logLevel,
		startTime: exQuery.range?.[0] ?? null,
		endTime: exQuery.range?.[1] ?? null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: exQuery.orderBy || undefined,
		desc: exQuery.orderBy ? exQuery.desc : undefined
	})
)

function exReset(): void {
	Object.assign(exQuery, { account: '', controllerName: '', remoteIp: '', logLevel: null, range: null, orderBy: '', desc: false })
	exReload()
}

function exOnSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	exQuery.orderBy = order ? property : ''
	exQuery.desc = order === 'desc'
	exReload()
}

const exColumns = computed(() => [
	{ field: 'controllerName', title: t('log.colController'), minWidth: 130, sortable: true },
	{ field: 'actionName', title: t('log.colAction'), minWidth: 110, sortable: true },
	{ field: 'httpMethod', title: t('log.colMethod'), width: 80, sortable: true },
	{ field: 'remoteIp', title: t('log.colRemoteIp'), width: 130, sortable: true },
	{ field: 'traceId', title: 'TraceId', minWidth: 150, sortable: true, showOverflow: 'tooltip' as const },
	{ field: 'account', title: t('log.colAccount'), width: 110, sortable: true },
	{ field: 'logLevel', title: t('log.colLogLevel'), width: 90, sortable: true },
	{ field: 'createTime', title: t('log.colTime'), width: 170, sortable: true },
	{ title: t('common.operations'), width: 90, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

/* ── 异常详情 ─────────────────────────────── */
const detail = reactive({
	visible: false,
	loading: false,
	data: null as SysLogExDetailOutput | null
})

async function openDetail(row: SysLogExOutput): Promise<void> {
	detail.data = null
	detail.visible = true
	detail.loading = true
	try {
		detail.data = await logsApi.logExDetail(row.id)
	} finally {
		detail.loading = false
	}
}

/* ── Http 出站日志 ─────────────────────────────── */
/** 方法下拉候选项(精确匹配;留空=不过滤) */
const HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
/** 状态码下拉候选项(只列常用码,精确匹配;其他码用地址栏/后端直查) */
const HTTP_STATUS_CODES = [200, 201, 204, 301, 302, 304, 400, 401, 403, 404, 409, 429, 500, 502, 503, 504]

const httpQuery = reactive({
	account: '',
	url: '',
	httpMethod: null as string | null,
	statusCode: null as number | null,
	range: null as DateRange,
	orderBy: '' as string,
	desc: false as boolean
})
const {
	loading: httpLoading,
	rows: httpRows,
	pager: httpPager,
	fetchPage: httpFetch,
	reload: httpReload,
	onPageChange: httpOnPageChange
} = usePaged<SysLogHttpOutput>(q =>
	logsApi.pageLogHttp({
		account: httpQuery.account || null,
		url: httpQuery.url || null,
		httpMethod: httpQuery.httpMethod,
		statusCode: httpQuery.statusCode,
		startTime: httpQuery.range?.[0] ?? null,
		endTime: httpQuery.range?.[1] ?? null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: httpQuery.orderBy || undefined,
		desc: httpQuery.orderBy ? httpQuery.desc : undefined
	})
)

function httpReset(): void {
	Object.assign(httpQuery, { account: '', url: '', httpMethod: null, statusCode: null, range: null, orderBy: '', desc: false })
	httpReload()
}

function httpOnSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	httpQuery.orderBy = order ? property : ''
	httpQuery.desc = order === 'desc'
	httpReload()
}

/** 状态列显红口径:带异常 / 未拿到响应(无状态码) / 4xx-5xx。 */
function httpStatusBad(row: SysLogHttpOutput): boolean {
	return row.hasException || row.statusCode == null || row.statusCode >= 400
}

const httpColumns = computed(() => [
	{ field: 'httpMethod', title: t('log.colMethod'), width: 80, sortable: true },
	{ field: 'requestUrl', title: t('log.colRequestUrl'), minWidth: 260, sortable: true, showOverflow: 'tooltip' as const },
	{ field: 'statusCode', title: t('common.status'), width: 90, sortable: true, slots: { default: 'http_status' } },
	{ field: 'elapsedMs', title: t('log.colElapsed'), width: 100, sortable: true, slots: { default: 'http_elapsed' } },
	{ field: 'account', title: t('log.colAccount'), width: 110, sortable: true },
	{ field: 'realName', title: t('log.colRealName'), width: 100, sortable: true },
	{ field: 'traceId', title: 'TraceId', minWidth: 150, sortable: true },
	{ field: 'createTime', title: t('log.colTime'), width: 170, sortable: true },
	{ title: t('common.operations'), width: 90, fixed: 'right' as const, slots: { default: 'http_ops' } }
])

/* ── Http 详情 ─────────────────────────────── */
const httpDetail = reactive({
	visible: false,
	loading: false,
	data: null as SysLogHttpDetailOutput | null
})

async function openHttpDetail(row: SysLogHttpOutput): Promise<void> {
	httpDetail.data = null
	httpDetail.visible = true
	httpDetail.loading = true
	try {
		httpDetail.data = await logsApi.logHttpDetail(row.id)
	} finally {
		httpDetail.loading = false
	}
}

/* ── 差异日志(批 CE,闭环 CC 批 D2:SqlSugar Aop.OnDiffLogEvent 自动落库,开关 DbSettings:EnableDiffLog) ── */
const diffQuery = reactive({
	range: null as DateRange,
	orderBy: '' as string,
	desc: false as boolean
})
const {
	loading: diffLoading,
	rows: diffRows,
	pager: diffPager,
	fetchPage: diffFetch,
	reload: diffReload,
	onPageChange: diffOnPageChange
} = usePaged<SysLogDiffOutput>(q =>
	logsApi.pageLogDiff({
		startTime: diffQuery.range?.[0] ?? null,
		endTime: diffQuery.range?.[1] ?? null,
		pageIndex: q.pageIndex as number,
		pageSize: q.pageSize as number,
		orderBy: diffQuery.orderBy || undefined,
		desc: diffQuery.orderBy ? diffQuery.desc : undefined
	})
)

function diffReset(): void {
	Object.assign(diffQuery, { range: null, orderBy: '', desc: false })
	diffReload()
}

function diffOnSortChange({ property, order }: { property: string; order: 'asc' | 'desc' | '' | null }): void {
	diffQuery.orderBy = order ? property : ''
	diffQuery.desc = order === 'desc'
	diffReload()
}

const diffColumns = computed(() => [
	{ field: 'createTime', title: t('log.colTime'), width: 170, sortable: true },
	{ field: 'businessData', title: t('log.colDiffBusiness'), minWidth: 150, sortable: true, showOverflow: 'tooltip' as const },
	{ field: 'diffType', title: t('log.colDiffType'), width: 110, sortable: true, slots: { default: 'diff_type' } },
	{ field: 'elapsed', title: t('log.colElapsed'), width: 100, sortable: true, slots: { default: 'diff_elapsed' } },
	{ field: 'createUserName', title: t('log.colRealName'), width: 100, sortable: true },
	{ title: t('common.operations'), width: 90, fixed: 'right' as const, slots: { default: 'diff_ops' } }
])

/** 差异详情对话框(四大字段 SQL/参数/操作前/操作后;按钮权限键 sysLogDiff/detail) */
const diffDetail = reactive({
	visible: false,
	loading: false,
	data: null as SysLogDiffDetailOutput | null
})

async function openDiffDetail(row: SysLogDiffOutput): Promise<void> {
	diffDetail.data = null
	diffDetail.visible = true
	diffDetail.loading = true
	try {
		diffDetail.data = await logsApi.logDiffDetail(row.id)
	} finally {
		diffDetail.loading = false
	}
}

onMounted(() => {
	/* 未授权 tab 不渲染也不拉数(v-perm 只摘 DOM,拦不住 mounted 拉数;批 CC D1 + 批 CE 补齐) */
	if (canOp) void opFetch()
	if (canLogin) void loginFetch()
	if (canEx) void exFetch()
	if (canHttp) void httpFetch()
	if (canDiff) void diffFetch()
})
</script>

<style scoped>
.search-row {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 14px;
	flex-wrap: wrap;
}
.search-input {
	width: 170px;
}
.search-select {
	width: 120px;
}
.search-date {
	width: 300px;
}

.dialog-meta {
	font-size: 12px;
	color: var(--ba-text-tertiary);
	margin: 0 0 10px;
	word-break: break-all;
}

.pre-title {
	margin: 12px 0 6px;
	font-size: 13px;
}

.log-pre {
	max-height: 200px;
	overflow: auto;
	background: rgb(0 0 0 / 4%);
	border-radius: 6px;
	padding: 10px 12px;
	font-size: 12px;
	line-height: 1.6;
	white-space: pre-wrap;
	word-break: break-all;
	margin: 0;
}
.log-pre-ex {
	max-height: 280px;
	color: #dc2626;
}

:deep(.st) {
	display: inline-block;
	padding: 2px 8px;
	border-radius: 10px;
	font-size: 12px;
}
:deep(.st-ok) {
	background: rgb(16 185 129 / 12%);
	color: #059669;
}
:deep(.st-off) {
	background: rgb(239 68 68 / 10%);
	color: #dc2626;
}
</style>