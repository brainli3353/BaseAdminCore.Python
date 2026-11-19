/** 站内消息 API(契约 /api/sysMessage/*,仅 sendUser/sendAll 两个发送端点,无列表)。 */
import service from '../request'

export interface MessageInput {
	/** 0 消息 / 1 成功 / 2 警告 / 3 错误 */
	messageType: number
	title: string
	message: string
	sendUserId: number | string
	receiveUserIds: Array<number | string>
}

/** 单播在线接收人 + 逐接收人落消息日志。 */
export const sendMessageToUsers = (d: MessageInput) =>
	service.post('/api/sysMessage/sendUser', d) as Promise<null>

/** 广播全部在线连接(不落日志);receiveUserIds 传空数组。 */
export const sendMessageToAll = (d: MessageInput) =>
	service.post('/api/sysMessage/sendAll', d) as Promise<null>
