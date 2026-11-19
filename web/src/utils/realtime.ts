/** 全局实时通道(原生 WebSocket,等价 SignalR 四消息面)——登录态生命周期 + 服务端消息订阅。
 * 服务端契约(/ws?token=,消息 {kind,data}):
 * - onlineUserList(在线列表变动,载荷=全量列表)
 * - forceOffline(强制下线,提示文案)
 * - publicNotice(通知公告发布推送)
 * - receiveMessage(站内消息)
 * 降级:首连失败静默,REST 查询面不受影响;自动重连。 */
import { ElMessage, ElNotification } from 'element-plus'
import { i18n } from '@/i18n'
import { getAccessToken } from '@/utils/token'
import { useUserStore } from '@/stores/user'
import router from '@/router'

export interface OnlineUserListPayload {
	realName?: string
	online: boolean
	userList: unknown[]
}

interface RealtimeMessage {
	kind: string
	data: unknown
}

let ws: WebSocket | null = null
let starting = false
let reconnectTimer: number | null = null
const listListeners = new Set<(m: OnlineUserListPayload) => void>()

export function onOnlineUserList(fn: (m: OnlineUserListPayload) => void): () => void {
	listListeners.add(fn)
	return () => {
		listListeners.delete(fn)
	}
}

export function realtimeState(): boolean {
	return ws !== null && ws.readyState === WebSocket.OPEN
}

export function startRealtime(): void {
	if (ws || starting) return
	const token = getAccessToken()
	if (!token) return
	starting = true

	const userStore = useUserStore()
	const t = (key: string, params?: Record<string, unknown>) =>
		i18n.global.t(key, params ?? {}) as string

	const scheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
	const socket = new WebSocket(`${scheme}//${window.location.host}/ws?token=${encodeURIComponent(token)}`)

	socket.onmessage = (event: MessageEvent) => {
		let msg: RealtimeMessage
		try {
			msg = JSON.parse(String(event.data)) as RealtimeMessage
		} catch {
			return
		}
		if (msg.kind === 'onlineUserList') {
			for (const fn of listListeners) fn(msg.data as OnlineUserListPayload)
		} else if (msg.kind === 'force_offline' || msg.kind === 'forceOffline') {
			const payload = msg.data as { message?: string } | null
			stopRealtime()
			ElMessage.error(t('realtime.forceOffline', { msg: payload?.message ?? '' }))
			userStore.reset()
			void router.push({ path: '/login', replace: true })
		} else if (msg.kind === 'public_notice' || msg.kind === 'publicNotice') {
			const payload = msg.data as { title?: string } | null
			ElNotification({
				title: t('realtime.noticeTitle'),
				message: payload?.title ?? '',
				type: 'warning',
				duration: 8000
			})
		} else if (msg.kind === 'receive_message' || msg.kind === 'receiveMessage') {
			const payload = msg.data as { title?: string; message?: string } | null
			ElNotification({
				title: t('realtime.messageTitle'),
				message: payload?.message ?? payload?.title ?? '',
				type: 'info',
				duration: 8000
			})
		}
	}

	socket.onopen = () => {
		ws = socket
		starting = false
	}

	socket.onclose = () => {
		if (ws === socket) ws = null
		starting = false
		if (getAccessToken() && !reconnectTimer) {
			reconnectTimer = window.setTimeout(() => {
				reconnectTimer = null
				startRealtime()
			}, 5000)
		}
	}

	socket.onerror = () => {
		console.warn('[realtime] socket error, realtime degraded')
	}
}

export function stopRealtime(): void {
	starting = false
	if (reconnectTimer !== null) {
		window.clearTimeout(reconnectTimer)
		reconnectTimer = null
	}
	if (ws) {
		const socket = ws
		ws = null
		socket.close()
	}
	listListeners.clear()
}
