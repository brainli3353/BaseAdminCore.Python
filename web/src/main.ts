import { createApp, type ObjectDirective } from 'vue'
import { createPinia } from 'pinia'
// 批 B6：不再 `app.use(ElementPlus)` 全量注册——模板里的 `<el-*>` 改由 vite 端
// `unplugin-vue-components` 按需解析（见 vite.config.ts）。但 **v-loading 指令**本是
// `app.use(ElementPlus)` 的注册副作用，按需后必须显式补装配（实测全仓 9 处使用，
// 不补则**编译期无错、运行时静默失效**）；实测本仓 `$message` 类全局属性 **0 处** ⇒ 无其他插件副作用要补。
import { ElLoadingDirective } from 'element-plus'
import 'element-plus/dist/index.css'
// EP 官方暗色变量(html.dark 时生效)
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
// vxe 4.x 双包:基座 vxe-pc-ui + 表格 vxe-table
import VxeUI from 'vxe-pc-ui'
import 'vxe-pc-ui/lib/style.css'
import VxeUITable from 'vxe-table'
import 'vxe-table/lib/style.css'

import App from './App.vue'
import router from './router'
import { setupGuard } from './router/guard'
import { i18n } from './i18n'
import { vPerm } from './directives/permission'
import { vBaLoading } from './directives/baLoading'
import { useAppStore } from './stores/app'
import { getAppInfo } from './api/app'
import { applyAppInfo, applyDocumentTitle } from './config/brand'

import './styles/tokens.css'
import './styles/dark.css'
import './styles/base.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
// 守卫须在 pinia 安装后装配(其内取 store;早于 app.use(pinia) 会因无 pinia 上下文启动即崩)
setupGuard(router)
app.use(router)
app.use(i18n)
// app.use(ElementPlus) 已移除（批 B6：组件按需解析；语言包不受影响——App.vue 根上已有
// `<el-config-provider :locale="elLocale">`，实测确认）
app.use(VxeUI)
app.use(VxeUITable)
app.directive('perm', vPerm)
// v-loading（批 B6 补装）：原随 `app.use(ElementPlus)` 自动注册，按需后必须显式装配。
app.directive('loading', ElLoadingDirective as unknown as ObjectDirective)
// v-ba-loading(批 BD #1):分区加载遮罩统一约定(EP v-loading 委托 + 文案缺省绑 common.loading)
app.directive('ba-loading', vBaLoading)

// EP 图标全局注册(侧边栏/按钮按名解析)
for (const [name, component] of Object.entries(ElementPlusIconsVue)) {
	app.component(name, component)
}

// 持久化主题在挂载前应用(防首屏闪烁)
const appStore = useAppStore()
void appStore.isDark

// 站点身份(批 AY,G24):先按构建期兜底落标题,再异步拉运行期身份覆盖品牌/标题。
// 不 await、不弹错(不要因后端未就绪挡住首屏);成功时响应式状态变化会自动重渲染消费点。
applyDocumentTitle()
void getAppInfo()
	.then(applyAppInfo)
	.catch(() => {
		/* 后端不可达:保留构建期品牌;后续登录失败会给出明确提示 */
	})

app.mount('#app')
