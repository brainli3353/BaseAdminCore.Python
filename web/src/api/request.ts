/** 统一请求客户端(axios):
 * ① 请求拦截:Authorization: Bearer <access token> + Accept-Language(当前 i18n locale)
 * ② 响应拦截:ApiResult 解包(code=0 取 data;code!==0 弹错+reject)
 * ③ 401 双 JWT 切换(批 N 6.4):access 过期 → 切 refresh(同签名密钥同 claim,无 refresh 端点)
 *    原请求自动重试一次;refresh 也 401(到期/TokenVersion++ 强制失效)→ 清会话回登录页。
 * ③b 401 分类(缺陷修复 t29):**凭据错误**(登录/OTP 端点,或未持 token 的匿名请求)→ **弹后端 msg/errCode 本地化文案**
 *    且**不**清会话、**不**跳转;只有"已持 token 的普通 API 401"才算会话失效走上面的清会话回登录页。
 *    判据抽在零依赖纯模块 `api/httpError.ts`(本仓无浏览器自动化,判据需可脱离 UI 执行)。
 * ④ 文件下载等非标响应:config.__raw=true 时不解包,原样返回 AxiosResponse。
 * ⑤ pending 计数(批 BD,需求单「表格加载态与统一交互」2026-09-29 #6):只暴露**能力**不挂**默认效果**——
 *    导出只读 `pendingCount` 供消费方自决(页头汇总指示/顶条进度等);本框架默认不接任何全局进度呈现
 *    (10–30s 轮询面挂常显进度条=全天闪动的新噪声,该行为属 opt-in,验收判据"默认行为不变")。 */
import axios, { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { computed, ref, type ComputedRef } from 'vue'
import { ElMessage } from 'element-plus'
import { i18n } from '@/i18n'
import type { ApiResult } from '@/types/api'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/utils/token'
import { isCredentialError401 } from './httpError'

/** 大整数安全解析(契约 §4):雪花 Id 为 19 位,> 2^53,JSON.parse 成 number 会静默丢精度。
 * 解析前把「字符串外、长度 >=16 的纯整数」加引号变为 string;字符串内部/浮点/科学计数不动。
 * 状态机扫描,保证 JSON 字符串内的数字序列不被误伤。 */
function safeParse(text: unknown): unknown {
	if (typeof text !== 'string' || !text) {
		return text
	}
	let out = ''
	let inString = false
	let escaped = false
	for (let i = 0; i < text.length; i++) {
		const ch = text[i]
		if (inString) {
			out += ch
			if (escaped) {
				escaped = false
			} else if (ch === '\\') {
				escaped = true
			} else if (ch === '"') {
				inString = false
			}
			continue
		}
		if (ch === '"') {
			inString = true
			out += ch
			continue
		}
		if (ch >= '0' && ch <= '9') {
			let j = i
			let num = ''
			while (j < text.length && text[j] >= '0' && text[j] <= '9') {
				num += text[j]
				j++
			}
			const prev = out[out.length - 1]
			const next = j < text.length ? text[j] : undefined
			const isFloatPart = prev === '.' || next === '.' || next === 'e' || next === 'E'
			out += num.length >= 16 && !isFloatPart ? `"${num}"` : num
			i = j - 1
			continue
		}
		out += ch
	}
	return JSON.parse(out)
}

/** 错误码 → 本地化文案(批 AQ):命中 `err.<错误码去点>` 时用前端 i18n 覆盖后端 msg
 * (切换语言后新响应即时为新语言);未命中/无 errCode 时回落后端 msg(兼容存量)。 */
function localizeError(candidate: unknown, fallback: string): string {
	const code = (candidate as { errCode?: unknown } | null | undefined)?.errCode
	if (typeof code === 'string' && code) {
		const key = 'err.' + code.replace(/\./g, '_')
		if (i18n.global.te(key)) {
			return i18n.global.t(key)
		}
	}
	return fallback
}

declare module 'axios' {
	/** service.post/get 第三参(AxiosRequestConfig)侧声明:__raw 在请求发出前即可携带 */
	export interface AxiosRequestConfig {
		/** 不解包 ApiResult,原样返回响应(读取响应头/二进制时使用) */
		__raw?: boolean
	}
	export interface InternalAxiosRequestConfig {
		/** 401 重试标记(防循环) */
		__retried?: boolean
	}
}

const service = axios.create({
	baseURL: '',
	timeout: 30000,
	// 大整数保真:字符串响应先经 safeParse 再走默认逻辑(Blob/二进制不受影响)
	transformResponse: [
		data => {
			if (typeof data === 'string' && data) {
				try {
					return safeParse(data)
				} catch {
					return data
				}
			}
			return data
		}
	]
})

/** 全局 pending 计数(批 BD #6):请求拦截 +1,响应(成功/失败)入口 −1,天然平衡。
 * 平衡性说明(漏算即假象,逐条路径核对):
 * - 401 切 refresh 重试:重试请求重走请求拦截 +1,原请求失败路径自身 −1,重试响应再 −1 ⇒ 净 0;
 * - __raw 分支(文件下载/读响应头):同是一次真实往返,同样计数;
 * - 业务失败(code!==0)/凭据 401/终局 401/超时/网络错误:全部经响应拦截两个入口,均计数;
 * - Math.max(0,…) 兜底:防未来新增早退路径漏减出现负数。 */
const pendingInternal = ref(0)
export const pendingCount: ComputedRef<number> = computed(() => pendingInternal.value)

service.interceptors.request.use((config: InternalAxiosRequestConfig) => {
	// 当前语言随每个请求带给后端(后端按 BCP-47 前缀匹配 zh/en;取自 i18n 全局 locale,
	// 与 Topbar 切换后的值同源,保证切换即时生效——不必等后端下发语言)
	config.headers['Accept-Language'] = i18n.global.locale.value
	const token = getAccessToken()
	if (token) {
		config.headers.Authorization = `Bearer ${token}`
	}
	// pending 计数(批 BD #6):每发出一次计 1(含 401 重试的第二次发出——重放也走本拦截器)
	pendingInternal.value++
	return config
})

service.interceptors.response.use(
	(response: AxiosResponse) => {
		// pending 计数(批 BD #6):响应入口先归还名额,再走解包/弹错分支(任何早退路径都已平衡)
		pendingInternal.value = Math.max(0, pendingInternal.value - 1)
		const config = response.config as InternalAxiosRequestConfig
		if (config.__raw) {
			return response
		}
		const res = response.data as ApiResult | null
		if (res === null || typeof res !== 'object' || !('code' in res)) {
			return response
		}
		if (res.code === 0) {
			return res.data as never
		}
		// HTTP 200 + 业务失败:统一弹错(如模型校验 400 业务码、MenuPerm 403 业务码)
		const failMsg = localizeError(res, res.msg || '操作失败')
		ElMessage.error(failMsg)
		return Promise.reject(new Error(failMsg))
	},
	async (error: AxiosError<ApiResult>) => {
		// pending 计数(批 BD #6):失败入口同样先归还名额(含 401 重试——重试请求自身已重新 +1)
		pendingInternal.value = Math.max(0, pendingInternal.value - 1)
		const status = error.response?.status
		const config = error.config as InternalAxiosRequestConfig | undefined

		// 401 + 未重试 + 持有 refresh → 切换令牌重试原请求(单请求粒度,不维护请求队列:
		// 管理台并发写操作少,并发 401 各自重试语义正确——refresh 同 claim,幂等重放安全)
		if (status === 401 && config && !config.__retried) {
			const refresh = getRefreshToken()
			if (refresh && refresh !== getAccessToken()) {
				config.__retried = true
				setTokens(refresh, getRefreshToken())
				return service(config)
			}
		}

		if (status === 401) {
			// 凭据错误(登录/OTP 失败,或未持会话的匿名请求):后端 msg/errCode 是用户**唯一**反馈,必须弹出来。
			// WHY 单独一支:修前 401 一律走下面的"会话失效"分支 ⇒ 登录页输错密码"毫无提示"(缺陷修复 t29)。
			if (isCredentialError401(config?.url, !!getAccessToken())) {
				const body = error.response?.data
				const credentialMsg = localizeError(
					body,
					((body && typeof body === 'object' && 'msg' in body && body.msg) || '登录失败') as string
				)
				ElMessage.error(credentialMsg)
				return Promise.reject(new Error(credentialMsg))
			}

			// 终局 401:会话彻底失效(未登录/refresh 到期/TokenVersion 强制下线)
			clearTokens()
			if (window.location.pathname !== '/login') {
				window.location.href = '/login'
			}
			return Promise.reject(error)
		}

		const res = error.response?.data
		const msg = localizeError(
			res,
			((res && typeof res === 'object' && 'msg' in res && res.msg) || error.message || '网络异常') as string
		)
		ElMessage.error(msg)
		return Promise.reject(new Error(msg))
	}
)

export default service
