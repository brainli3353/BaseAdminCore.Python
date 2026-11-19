/** v-ba-loading 分区加载遮罩(批 BD #1,需求单「表格加载态与统一交互」2026-09-29):
 * 统一约定件——在 Element Plus `v-loading` 之上只补两件框架缺省:
 * ① 遮罩文案缺省绑 i18n `common.loading`(业务不必在每个容器上重复写
 *    `element-loading-text="..."` 这类逐元素属性——22 个 sys 页/下游 12 视图的重复实证);
 * ② 其余行为(遮罩/旋转圈/主题色/开合时机)**全部委托 EP 原指令**——不重造遮罩实现,零平行机制。
 *
 * 用法(与 v-loading 同签名):
 * - `v-ba-loading="loading"`(布尔开合,最常用);
 * - `v-ba-loading="{ text: '自定义文案' }"`(对象选项:EP LoadingOptions,未给 text 用缺省);
 * - 细粒度覆写仍可用 EP 原生属性:`element-loading-background` 等照常生效(本指令不覆盖已写死的属性)。
 *
 * 实现说明:布尔值路径经"补缺省属性 + 委托"实现(EP 原指令对布尔绑定会回读
 * `element-loading-text` 属性,见 EP loading/src/directive.ts getProp 回退链);对象路径在
 * 委托前把缺省合并进 binding.value。文案在指令钩子时刻解析——切语言后下一次开合即新语言,
 * 长时间挂着的遮罩不实时跟随(可接受;分区遮罩生命周期以秒计)。
 *
 * 配套约定:遮罩容器须有内容高度(空分区改用 BaEmpty/BaSkeleton 三态件,见指南 §48)。 */
import { ElLoadingDirective, type LoadingOptions } from 'element-plus'
import type { Directive, ObjectDirective } from 'vue'
import { i18n } from '@/i18n'

export type BaLoadingValue = boolean | LoadingOptions

/** EP 原指令按 ObjectDirective 视角取钩子(Vue 的 Directive 是"对象|函数"联合类型,直接点 .mounted 会 TS2339);
 * EP 根未导出 LoadingBinding 类型,委托侧统一按本仓值类型断言(运行时同一对象,行为不变)。 */
const epLoading = ElLoadingDirective as unknown as ObjectDirective<HTMLElement, BaLoadingValue>

/** 对象选项路径:未显式给 text 时补 i18n 缺省(消费方显式值永远优先) */
function withTextDefault(value: LoadingOptions): LoadingOptions {
	return { text: i18n.global.t('common.loading'), ...value }
}

/** 布尔路径:缺省文案落为 element-loading-text 属性(EP 回读链的取值位),不覆盖消费方已写死的属性 */
function ensureDefaultAttrs(el: HTMLElement): void {
	if (!el.hasAttribute('element-loading-text')) {
		el.setAttribute('element-loading-text', i18n.global.t('common.loading'))
	}
}

export const vBaLoading: Directive<HTMLElement, BaLoadingValue> = {
	mounted(el, binding, vnode, prevVnode) {
		if (binding.value && typeof binding.value === 'object') {
			epLoading.mounted?.(el, { ...binding, value: withTextDefault(binding.value) }, vnode, prevVnode)
			return
		}
		ensureDefaultAttrs(el)
		epLoading.mounted?.(el, binding, vnode, prevVnode)
	},
	updated(el, binding, vnode, prevVnode) {
		if (binding.value && typeof binding.value === 'object') {
			epLoading.updated?.(el, { ...binding, value: withTextDefault(binding.value) }, vnode, prevVnode)
			return
		}
		ensureDefaultAttrs(el)
		epLoading.updated?.(el, binding, vnode, prevVnode)
	},
	unmounted(el, binding, vnode, prevVnode) {
		epLoading.unmounted?.(el, binding, vnode, prevVnode)
	}
}
