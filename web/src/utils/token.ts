/** 令牌持久化:localStorage(刷新不丢;登出/失效即清)。
 * 双 JWT 口径(批 N 6.4):access 短时效 + refresh 长时效,两者同签名密钥同 claim 集,
 * access 过期后前端直接把 Authorization 切换到 refresh 继续调用(无 refresh 端点)。 */
const ACCESS_KEY = 'baseadmin.accessToken'
const REFRESH_KEY = 'baseadmin.refreshToken'

export function getAccessToken(): string | null {
	return localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken(): string | null {
	return localStorage.getItem(REFRESH_KEY)
}

export function setTokens(accessToken: string, refreshToken: string | null): void {
	localStorage.setItem(ACCESS_KEY, accessToken)
	if (refreshToken) {
		localStorage.setItem(REFRESH_KEY, refreshToken)
	}
}

export function clearTokens(): void {
	localStorage.removeItem(ACCESS_KEY)
	localStorage.removeItem(REFRESH_KEY)
}
