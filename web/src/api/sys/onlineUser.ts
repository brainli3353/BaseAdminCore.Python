/** 在线用户 API(契约 /api/onlineUser/*,无分页,list 直出 List)。 */
import service from '../request'

export interface OnlineUserInfo {
	/** SignalR ConnectionId */
	connectionId: string
	userId: number | string
	tenantId: number | string
	account: string
	realName: string | null
	/** 上线时间 */
	time: string
	/** 优先 X-Forwarded-For */
	ip: string | null
	/** UA 解析 */
	browser: string | null
	os: string | null
}

/** 在线列表(当前租户;超管全量)。 */
export const listOnline = () => service.get('/api/onlineUser/list') as Promise<OnlineUserInfo[]>

/** 单连接强制下线(推送 forceOffline + 服务端注销双保险)。 */
export const forceOffline = (connectionId: string) =>
	service.post(`/api/onlineUser/forceOffline?connectionId=${encodeURIComponent(connectionId)}`) as Promise<null>
