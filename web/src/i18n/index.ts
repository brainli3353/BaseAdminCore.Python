import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import enUS from './en-US'

/** 首屏语言:读 vueuse useLocalStorage 的持久化形态(JSON 字符串,如 "\"en-US\""),非法/缺失回落 zh-CN。
 * WHY:store(app.ts)用 useLocalStorage,写盘时做了 JSON 序列化,这里必须按同形态容错解析才能与 store 首屏同值;
 * 不把 pinia 引进来(避免 i18n ←→ store 循环依赖),故就地读 key。 */
function initialLocale(): 'zh-CN' | 'en-US' {
	try {
		const raw = localStorage.getItem('baseadmin.lang')
		if (!raw) return 'zh-CN'
		const v = JSON.parse(raw)
		return v === 'en-US' || v === 'zh-CN' ? v : 'zh-CN'
	} catch {
		return 'zh-CN'
	}
}

export const i18n = createI18n({
	legacy: false,
	// 硬编码 zh-CN 会导致刷新后首屏语言与持久化不一致(store 已是 en-US 而 i18n 仍是中文)
	locale: initialLocale(),
	fallbackLocale: 'en-US',
	messages: { 'zh-CN': zhCN, 'en-US': enUS }
})
