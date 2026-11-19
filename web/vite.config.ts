import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
// 批 B6：Element Plus **组件**按需解析——模板里的 `<el-*>` 由此自动引入对应组件，替代 main.ts 的
// `app.use(ElementPlus)` 全量注册（改造前实测 ep-vendor 1,138.29 kB / gzip 356.54 kB）。
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// 开发代理:前端只认同源 /api 与 /hubs——浏览器侧无跨域;
// 生产由 .NET Web.Entry 同源托管 dist(MapStaticAssets + SPA 回退),代理配置零参与。
const API_TARGET = 'http://127.0.0.1:5090'

export default defineConfig({
	plugins: [
		vue(),
		// 只按需 **JS 组件**：`importStyle: false` 是关键——样式仍由 main.ts 全量引入的
		// `element-plus/dist/index.css` 提供，避免与 resolver 注入的按样式重复打包；
		// 也避免 `ElMessage`/`ElLoading` 等**函数式 API**（不在模板里，resolver 覆盖不到）缺样式。
		// 图标不在本列：`menuIcon()` 返回**字符串图标名**，靠 main.ts 全局注册解析（见 src/utils/icons.ts）。
		Components({ resolvers: [ElementPlusResolver({ importStyle: false })], dts: 'src/components.d.ts' })
	],
	resolve: {
		alias: {
			'@': fileURLToPath(new URL('./src', import.meta.url))
		}
	},
	server: {
		port: 5173,
		proxy: {
			'/api': { target: API_TARGET, changeOrigin: true },
			'/hubs': { target: API_TARGET, changeOrigin: true, ws: true }
		}
	},
	build: {
		outDir: 'dist',
		chunkSizeWarningLimit: 1600,
		rollupOptions: {
			output: {
				// 大依赖分片:vite8(rolldown)manualChunks 仅支持函数形式——按包根归属 chunk
				manualChunks(id: string): string | undefined {
					const m = id.match(/node_modules\/(?:\.pnpm\/[^/]+\/node_modules\/)?(@[^/]+\/[^/]+|[^/@]+)/)
					if (!m) return undefined
					const pkg = m[1]
					if (pkg === 'vue' || pkg === 'vue-router' || pkg === 'pinia' || pkg === 'vue-i18n') return 'vue-vendor'
					if (pkg === 'element-plus' || pkg.startsWith('@element-plus/')) return 'ep-vendor'
					if (pkg === 'vxe-table' || pkg === 'vxe-pc-ui') return 'vxe-vendor'
					return undefined
				}
			}
		}
	}
})
