/** 站点身份 API(批 AY,G24;契约 GET /api/app/info)。匿名只读,登录前即可取。 */
import service from './request'
import type { ApiResult } from '@/types/api'
import type { AppIdentity } from '@/config/brand'

/**
 * GET /api/app/info → {name, fullName, titleSuffix}。
 * 用 `__raw` + 手动解包(范式见 api/sys/notice.ts):启动期后台拉取,**失败不得弹错**打断首屏;
 * 空值字段由 `applyAppInfo` 保留构建期兜底。
 */
export async function getAppInfo(): Promise<AppIdentity | null> {
	const resp = (await service.get('/api/app/info', { __raw: true })) as unknown as import('axios').AxiosResponse<ApiResult<AppIdentity>>
	return resp?.data?.data ?? null
}