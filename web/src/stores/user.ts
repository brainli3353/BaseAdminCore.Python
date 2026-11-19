/** 用户会话状态:令牌落地(token.ts)+ 当前用户信息。
 * 登录编排(两阶段)在登录页完成,本 store 只负责会话事实与登出。 */
import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'
import { clearTokens, getAccessToken, setTokens } from '@/utils/token'
import { stopRealtime } from '@/utils/realtime'
import type { UserInfo } from '@/types/api'

export const useUserStore = defineStore('user', {
	state: () => ({
		user: null as UserInfo | null,
		/** 登录二阶段返回的密码到期标志 → 进入工作台前强制改密门 */
		passwordExpired: false
	}),
	getters: {
		isLoggedIn(): boolean {
			return !!getAccessToken()
		}
	},
	actions: {
		setUser(user: UserInfo) {
			this.user = user
		},
		/** 二阶段成功后调用:落地双令牌 */
		setSession(accessToken: string, refreshToken: string | null, passwordExpired = false) {
			setTokens(accessToken, refreshToken)
			this.passwordExpired = passwordExpired
		},
		/** 拉取当前用户(含权限键集合);失败抛错由调用方处理 */
		async fetchMe() {
			this.user = await authApi.getMe()
			return this.user
		},
		/** 登出:服务端黑名单(尽力)+ 本地清会话 */
		async logout() {
			await authApi.postLogout()
			this.reset()
		},
		reset() {
			clearTokens()
			this.user = null
			this.passwordExpired = false
			// 批 CL G31:会话终结(登出/401 失效/强踢)即断开实时通道
			stopRealtime()
		}
	}
})
