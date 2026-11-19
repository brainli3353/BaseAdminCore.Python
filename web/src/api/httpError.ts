/** HTTP 错误分类纯函数(缺陷修复 t29):**零依赖**是刻意的——
 * 本仓无浏览器自动化(无 chromium/playwright),判据必须能脱离 UI 直接执行校验
 * (`npx esbuild src/api/httpError.ts --bundle --format=esm` 后 node 断言即可)。
 */

/** 该 401 是否属"**凭据错误**"(应把后端 msg/errCode 提示给用户),而非"会话失效"(清会话回登录页)。
 *
 * 判据(两条任一命中即凭据错误):
 * ① 请求指向**匿名认证入口** `/auth/login*`(登录/OTP 失败本身就是 401,提示是用户唯一反馈);
 * ② 当前**没有** access token——没会话就不可能是"会话过期",只能是这次请求被拒。
 *
 * WHY 需要分类:修前 `request.ts` 把 401 一律按"会话失效"处理(清会话＋跳登录页＋reject,**从不弹提示**),
 * 于是"登录页输错密码"表现为**毫无提示**(缺陷实测:`{code:1,msg:"账号或密码错误",errCode:"auth.login_failed"}`
 * 被静默丢弃,而前端词表 `err.auth_login_failed` 其实中英齐备)。
 *
 * @param url 请求 URL(axios config.url;可含 baseURL 前缀)
 * @param hasAccessToken 调用时是否持有 access token
 */
export function isCredentialError401(url: string | undefined, hasAccessToken: boolean): boolean {
	const isAuthEntry = typeof url === 'string' && url.includes('/auth/login')
	return isAuthEntry || !hasAccessToken
}