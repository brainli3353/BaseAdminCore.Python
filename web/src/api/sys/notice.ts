/** 通知公告 API(契约 /api/sysNotice/*,仅管理面 page/add/update/delete/public)。 */
import service from '../request'
import type { ApiResult, PageResult } from '@/types/api'
import { i18n } from '@/i18n'

export interface NoticeOutput {
	id: number | string
	title: string
	content: string
	/** 1 通知 / 2 公告 / 3 系统升级(与后端 NoticeTypeEnum 取值一一对应) */
	type: number
	publicUserId: number | string
	publicUserName: string | null
	publicOrgId: number | string
	publicOrgName: string | null
	publicTime: string | null
	cancelTime: string | null
	/** 0 草稿 / 1 已发布 */
	status: number
	createTime: string | null
}

export interface NoticeQuery {
	/** 标题模糊 */
	title?: string | null
	/** 0 不过滤 / 非 0 精确 */
	type?: number
	pageIndex?: number
	pageSize?: number
	orderBy?: string
	desc?: boolean
	/** 创建时间范围起(批 UX B1d,CreateTime 闭区间——草稿 PublicTime 恒 null 故取创建时间;可空=不过滤) */
	startDate?: string | null
	/** 创建时间范围止(批 UX B1d,CreateTime 闭区间;可空=不过滤) */
	endDate?: string | null
}

export const pageNotice = (q: NoticeQuery) =>
	service.get('/api/sysNotice/page', { params: q }) as Promise<PageResult<NoticeOutput>>

/** 恒草稿,发布人快照服务端自填。 */
export const addNotice = (d: { title: string; content: string; type: number }) =>
	service.post('/api/sysNotice/add', d) as Promise<number | string>

/** 部分更新,仅发布人本人可改。 */
export const updateNotice = (d: {
	id: number | string
	title?: string
	content?: string
	type?: number
}) => service.post('/api/sysNotice/update', d) as Promise<null>

/** 软删+级联删接收行;已发布禁删。 */
export const deleteNotice = (id: number | string) =>
	service.post(`/api/sysNotice/delete?id=${id}`) as Promise<null>

/** 发布并广播在线接收人;userIds 空/缺省=全租户,重发幂等。 */
export const publicNotice = (id: number | string, userIds?: Array<number | string>) =>
	service.post('/api/sysNotice/public', { id, userIds }) as Promise<null>

/* ── 自读面(登录即可,后端豁免 [MenuPerm];供登录后未读弹窗/收件箱使用) ───────────── */

/** 公告类型 → i18n 键映射(与后端 NoticeTypeEnum 对齐:1 通知 / 2 公告 / 3 系统升级)。
 * WHY 存键不存文案:api 层拿不到 useI18n 组合式,统一走 i18n.global 与视图同词表
 * (键复用 sysNotice 段 typeNotice/typeAnnouncement/typeUpgrade,zh/en 对称;切语言即时生效,不写死中文)。 */
const NOTICE_TYPE_LABEL_KEYS: Record<number, string> = {
	1: 'sysNotice.typeNotice',
	2: 'sysNotice.typeAnnouncement',
	3: 'sysNotice.typeUpgrade'
}

/** 类型标签;未知取值容错为「类型 N」(后端扩充枚举值时前端不误标、不崩)。 */
export function noticeTypeLabel(type: number): string {
	const key = NOTICE_TYPE_LABEL_KEYS[type]
	return key ? i18n.global.t(key) : i18n.global.t('sysNotice.typeFallback', { type })
}

/** 本人未读公告(后端已按升级提示开关 sys_upgrade 过滤「系统升级」类型,前端不再二次过滤)。
 * WHY 静默 + __raw:该请求是"登录进入主布局后自动拉取",失败不得弹错打断登录;
 * __raw 使 HTTP 200 + 业务失败(code≠0)也不走全局拦截器弹错(范式见 api/auth.ts)。
 * 网络/非 2xx 仍可能由全局拦截器提示(本件不改 request.ts)——已由调用侧 try/catch 兜底为静默。 */
export async function unReadNoticeList(): Promise<NoticeOutput[]> {
	try {
		const resp = (await service.get('/api/sysNotice/unReadList', { __raw: true })) as unknown as import('axios').AxiosResponse<ApiResult<NoticeOutput[]>>
		return resp.data?.code === 0 ? (resp.data.data ?? []) : []
	} catch (e) {
		console.debug('[notice] 未读公告拉取失败(静默,不打断登录):', e)
		return []
	}
}

/** 标记本人已读(后端入参为 query 参数 ?id=,非 body);失败静默(下次登录仍会提示)。 */
export async function setNoticeRead(id: number | string): Promise<void> {
	try {
		await service.post(`/api/sysNotice/setRead?id=${id}`, undefined, { __raw: true })
	} catch (e) {
		/* 静默:标记失败不打断用户,未读状态保留 */
		console.debug('[notice] 标记已读失败(静默):', e)
	}
}
