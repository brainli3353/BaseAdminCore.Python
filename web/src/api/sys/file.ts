/** 文件管理 API(契约 /api/sysFile/*)。分页清单 GET /page(批 UX B1c 后端落地);
 * upload 登录即可(Authorization 由 request.ts 拦截器统一附加,令牌来自 @/utils/token getAccessToken)。 */
import service from '../request'
import type { PageResult } from '@/types/api'

export interface SysFileOutput {
	id: number | string
	fileMd5: string
	/** long,雪花口径不做算术,原样透传 */
	sizeKb: number | string
	fileName: string | null
	filePath: string | null
	suffix: string | null
	provider: string | null
	dataId: number | string | null
	url: string | null
}

/** 分页清单行输出(SysFilePageOutput):已脱敏——不含 filePath/provider。 */
export interface SysFilePageOutput {
	id: number | string
	fileMd5: string
	/** long,雪花口径不做算术,原样透传 */
	sizeKb: number | string
	fileName: string | null
	suffix: string | null
	dataId: number | string | null
	url: string | null
	createTime: string | null
}

export interface FilePageQuery {
	/** FileName 关键字模糊(空白视为无过滤) */
	fileName?: string | null
	pageIndex?: number
	pageSize?: number
	/** 创建时间范围(与日志域同口径,闭区间) */
	startDate?: string | null
	endDate?: string | null
}

/** 分页清单(按创建时间倒序,权限键 sysFile/page)。 */
export const pageFile = (q: FilePageQuery) =>
	service.get('/api/sysFile/page', { params: q }) as Promise<PageResult<SysFilePageOutput>>

/** multipart 上传:字段名 file;dataId 可选业务关联。 */
export const uploadFile = (file: File, dataId?: number | string | null) => {
	const fd = new FormData()
	fd.append('file', file)
	if (dataId !== undefined && dataId !== null) {
		fd.append('dataId', String(dataId))
	}
	return service.post('/api/sysFile/upload', fd) as Promise<SysFileOutput>
}

/** 软删记录 + 内容清理(幂等)。 */
export const deleteFile = (id: number | string) =>
	service.post(`/api/sysFile/delete?id=${id}`) as Promise<null>

/** 业务文件全集差集同步(契约外薄端点,管理页暂不消费)。 */
export const associateFiles = (dataId: number | string, fileIds: Array<number | string>) =>
	service.post('/api/sysFile/associate', { dataId, fileIds }) as Promise<null>