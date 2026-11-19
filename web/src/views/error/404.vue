<template>
	<div class="notfound">
		<div class="nf-code">404</div>
		<p class="nf-text">{{ t('nav.notFound') }}</p>
		<el-button type="primary" @click="router.replace('/')">{{ t('nav.backHome') }}</el-button>
	</div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
const router = useRouter()
const { t } = useI18n()
</script>

<style scoped>
.notfound {
	height: 100vh;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 12px;
	background: var(--ba-bg);
}
.nf-code {
	font-size: 96px;
	font-weight: 800;
	line-height: 1;
	background: linear-gradient(135deg, #6366f1, #4338ca);
	-webkit-background-clip: text;
	background-clip: text;
	color: transparent;
}
.nf-text {
	color: var(--ba-text-secondary);
	margin: 0 0 8px;
}
</style>
