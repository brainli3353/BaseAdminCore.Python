import { reactive } from 'vue'
import { mergeIdentity, type AppIdentity } from './brandIdentity'

/** 站点身份单点(批 AY,G24;批 AZ 补"显式空后缀"语义;批 BA 扩到登录页大标题)。
 * 优先序:**运行期** `/api/app/info`(后端 `App:Name`/`App:FullName`/`App:TitleSuffix`,env 可覆盖)
 *        > **构建期** Vite 变量(`VITE_BRAND_*`,未配 App 节时的兜底) > 本文件缺省字面量。
 * 响应式:`applyAppInfo` 覆盖后,侧栏/登录页等消费点自动重渲染;浏览器标题由 `applyDocumentTitle` 刷新。
 * 合并/拼接判据在零依赖纯模块 `brandIdentity.ts`(见该文件:`name/fullName` 空=保留兜底;
 * `titleSuffix` 显式空=无后缀;`titleSuffixConfigured`=后端是否显式给了后缀,未配则由各呈现点按自身兜底)。
 * 下游 fork 换名:改后端配置即可(不必重新构建前端产物);构建期变量仅作离线兜底。 */
const envName = import.meta.env.VITE_BRAND_NAME || 'BaseAdmin'
const envFullName = import.meta.env.VITE_BRAND_FULL_NAME || 'BaseAdminCore'
const envTitleSuffix = import.meta.env.VITE_BRAND_TITLE_SUFFIX || '管理台'

/** 站点身份(响应式状态;name=品牌名,fullName=全名,titleSuffix=标题后缀(空串=不加后缀),
 * titleSuffixConfigured=后端是否显式配了后缀——未配时浏览器标签用构建期兜底、登录页用语言兜底) */
export const brand = reactive({
	name: envName,
	fullName: envFullName,
	titleSuffix: envTitleSuffix,
	titleSuffixConfigured: false
})

export type { AppIdentity }
export { composeTitle } from './brandIdentity'

/** 应用后端身份(合并判据见 `brandIdentity.ts`),随后刷新浏览器标题 */
export function applyAppInfo(info: AppIdentity | null | undefined): void {
	const merged = mergeIdentity(brand, info)
	brand.name = merged.name
	brand.fullName = merged.fullName
	brand.titleSuffix = merged.titleSuffix
	brand.titleSuffixConfigured = merged.titleSuffixConfigured
	applyDocumentTitle()
}

/** 刷新浏览器标题 = 品牌名 + 标题后缀(titleSuffix 为空串时即品牌名本身;启动与身份覆盖后各调一次) */
export function applyDocumentTitle(): void {
	document.title = `${brand.name}${brand.titleSuffix}`
}

/** 品牌首字母(登录页/侧栏 logo 占位字符,随站点身份变化) */
export function brandInitial(): string {
	const name = brand.name?.trim()
	return name ? name.charAt(0).toUpperCase() : 'B'
}