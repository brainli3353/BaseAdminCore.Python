/** 多语言 API(批 AL 6.6,契约 /api/sysLocalization)。只读:受支持语言与当前解析结果(前端/运维的单一事实源)。 */
import service from '../request'

/* ── 类型 ─────────────────────────────── */
/** 语言解析结果输出(后端 ILocalizationService 的对外快照) */
export interface LocalizationCulturesOutput {
	/** 缺省语言(配置 Localization:DefaultCulture) */
	defaultCulture: string
	/** 受支持语言集(配置 Localization:SupportedCultures) */
	supported: string[]
	/** 当前请求解析到的语言(优先级 ?lang= > Accept-Language > 缺省;后端 BatchAL 用例锁定,批 BP D2 注释对齐) */
	current: string
}

/* ── 端点 ─────────────────────────────── */
/** GET /api/sysLocalization/cultures → {defaultCulture, supported[], current} */
export function getCultures() {
	return service.get('/api/sysLocalization/cultures') as Promise<LocalizationCulturesOutput>
}