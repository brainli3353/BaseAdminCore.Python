/** v-perm 按钮权限显隐:与后端 [MenuPerm] 同一份权限键数据("一处配置两端生效")。
 * 用法: v-perm="'sysUser/add'" 或 v-perm="['sysUser/add','sysUser/update']"(任一命中即显示)。
 * 超管(999)前端直通;权限键缺失/未授权 → 移除元素(后端 403 仍是最终裁决)。 */
import type { Directive } from 'vue'
import { useUserStore } from '@/stores/user'
import { useMenuStore } from '@/stores/menu'

export const vPerm: Directive<HTMLElement, string | string[]> = {
	mounted(el, binding) {
		const userStore = useUserStore()
		const menuStore = useMenuStore()
		const perms = Array.isArray(binding.value) ? binding.value : [binding.value]
		const isSuper = userStore.user?.accountType === 999
		const granted = isSuper || perms.some(p => menuStore.permissions.includes(p))
		if (!granted) {
			el.parentNode?.removeChild(el)
		}
	}
}
