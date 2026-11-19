/** 应用外壳状态:主题(亮/暗,持久化)/侧边栏折叠/语言,全部持久化。
 * 主题 = useDark(html.dark class,与 EP 官方暗色变量选择器一致)+ vxe 主题同步 + 本框架令牌覆盖(dark.css)。 */
import { watch } from 'vue'
import { defineStore } from 'pinia'
import { useDark, useLocalStorage, useToggle } from '@vueuse/core'
import VxeUI from 'vxe-pc-ui'

export const useAppStore = defineStore('app', () => {
	const sidebarCollapsed = useLocalStorage('baseadmin.sidebarCollapsed', false)
	const lang = useLocalStorage<'zh-CN' | 'en-US'>('baseadmin.lang', 'zh-CN')
	// WHY 不写 attribute:'dark':useDark 非 class 模式只写 html[dark="dark"],不会生成 .dark,
	// 而 EP 暗色变量与 dark.css 都以 html.dark 为选择器 ⇒ 切主题无视觉变化。
	const isDark = useDark({ storageKey: 'baseadmin.theme' })
	const toggleDark = useToggle(isDark)
	watch(isDark, dark => VxeUI.setTheme(dark ? 'dark' : 'light'), { immediate: true })

	const toggleSidebar = () => {
		sidebarCollapsed.value = !sidebarCollapsed.value
	}
	const setLang = (l: 'zh-CN' | 'en-US') => {
		lang.value = l
	}

	return { sidebarCollapsed, lang, isDark, toggleDark, toggleSidebar, setLang }
})
