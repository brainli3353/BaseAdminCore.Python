/** 站点身份合并判据(批 AZ,批 AY 收尾件)——**零依赖纯模块**:
 * 不 import vue、不读 import.meta、不碰 DOM ⇒ 可在 node 直接执行(仓内先例 `api/httpError.ts`:
 * 本仓无浏览器自动化,判据须能脱离 UI 跑)。`brand.ts` 只负责把它接到响应式状态与 document.title。 */

/** 后端站点身份快照(GET /api/app/info 的 data;字段可为 null=未配置) */
export interface AppIdentity {
	name?: string | null
	fullName?: string | null
	titleSuffix?: string | null
}

/** 本地品牌态(构建期兜底值) */
export interface BrandState {
	name: string
	fullName: string
	titleSuffix: string
	/** 后端是否**显式**给了 `titleSuffix`(含空串)——true 时各处标题一律用 `titleSuffix`;
	 * false(未配)时各呈现点用自己的兜底:浏览器标签用构建期 `VITE_BRAND_TITLE_SUFFIX`,
	 * 登录页大标题用**当前语言**的兜底(zh「管理台」/en「Admin」,批 BA)。 */
	titleSuffixConfigured: boolean
}

/**
 * 把后端身份合并进本地品牌态(不改动入参):
 * - `name` / `fullName`:**缺失或空串 → 保留本地兜底**——品牌名不允许被置空(空品牌等于页面没名字);
 * - `titleSuffix`:**缺失(null/undefined) → 保留兜底并置 `titleSuffixConfigured=false`;显式给值(含空串) → 采用并置 true**——
 *   空后缀是有意义配置("标题就只要品牌名"),与"没配"必须区分开(批 AZ 语义,批 BA 扩到登录页)。
 * 后端契约 `GET /api/app/info`:未配置的键输出 `null`,显式配空的键输出 `""` ⇒ 两者在 JSON 层可区分。
 */
export function mergeIdentity(prev: BrandState, info: AppIdentity | null | undefined): BrandState {
	if (!info) {
		return prev
	}
	const configured = info.titleSuffix !== null && info.titleSuffix !== undefined
	return {
		name: info.name ? info.name : prev.name,
		fullName: info.fullName ? info.fullName : prev.fullName,
		titleSuffix: configured ? info.titleSuffix! : prev.titleSuffix,
		titleSuffixConfigured: configured
	}
}

/**
 * 拼接带后缀的标题(批 BA)——纯函数,脱离 UI 可判:
 * - `configured=true`(后端显式配了,含空串) ⇒ 用配置值(空串=只有品牌名);
 * - `configured=false`(未配) ⇒ 用调用方给的**语言兜底**(登录页传 `t('login.brandSuffix')`)。
 */
export function composeTitle(name: string, titleSuffix: string, configured: boolean, fallbackSuffix: string): string {
	return name + (configured ? titleSuffix : fallbackSuffix)
}