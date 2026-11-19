<template>
	<el-config-provider :locale="elLocale">
		<router-view />
	</el-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import en from 'element-plus/es/locale/lang/en'

// EP 内置文案(分页/日期选择/弹窗按钮等)不和 vue-i18n 共享 locale,必须显式喂语言包,
// 否则切到 en-US 后业务文案是英文、EP 组件仍是中文(首屏与切换都受影响)
const { locale } = useI18n()
const elLocale = computed(() => (locale.value === 'en-US' ? en : zhCn))
</script>
