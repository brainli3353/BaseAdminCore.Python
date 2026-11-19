/** 认证 API(契约:POST /api/auth/login 一阶段 / POST /api/auth/login/otp 二阶段 / GET me / POST logout)。
 * 二阶段成功经响应头透传 X-Refresh-Token 与 X-Password-Expired(data=token 形状不变)。
 * 批 BB:开关关直登同一形态——data=token 字符串经同响应头透传,与二阶段前端判别一致。 */
import service from './request'
import type { ApiResult, LoginChallenge, LoginTokenResult, UserInfo } from '@/types/api'

/** 一阶段:账号密码初验 → 挑战凭据;开关关直登 → 令牌(LoginTokenResult,经 __raw 响应头取 refresh/到期) */
export async function postLogin(account: string, password: string): Promise<LoginChallenge | LoginTokenResult> {
	const resp = (await service.post('/api/auth/login', { account, password }, { __raw: true })) as unknown as import('axios').AxiosResponse<ApiResult<string | LoginChallenge>>
	const data = resp.data.data
	if (typeof data === 'string') {
		return {
			accessToken: data,
			refreshToken: (resp.headers['x-refresh-token'] as string) || null,
			passwordExpired: resp.headers['x-password-expired'] === 'true',
		}
	}
	return data as LoginChallenge
}

/** 二阶段:OTP 校验 → 令牌(读 __raw 响应头取 refresh 与到期标志) */
export async function postLoginOtp(challengeId: string, code: string): Promise<LoginTokenResult> {
	const resp = (await service.post('/api/auth/login/otp', { challengeId, code }, { __raw: true })) as unknown as import('axios').AxiosResponse<ApiResult<string>>
	const accessToken = resp.data.data
	const refreshToken = (resp.headers['x-refresh-token'] as string) || null
	const passwordExpired = resp.headers['x-password-expired'] === 'true'
	return { accessToken, refreshToken, passwordExpired }
}

/** 当前用户信息(含按钮权限键集合) */
export async function getMe(): Promise<UserInfo> {
	const data = await service.get('/api/auth/me')
	return data as unknown as UserInfo
}

/** 登出(当前 access token 入黑名单;失败静默——会话本地已清) */
export async function postLogout(): Promise<void> {
	try {
		await service.post('/api/auth/logout')
	} catch {
		/* 网络/令牌失效场景不阻塞本地登出 */
	}
}

/** 自助改密(批 A 1.11;成功触发 TokenVersion++ 全端强制下线) */
export async function postUpdatePassword(oldPassword: string, newPassword: string): Promise<void> {
	await service.post('/api/sysUser/updatePassword', { oldPassword, newPassword })
}
