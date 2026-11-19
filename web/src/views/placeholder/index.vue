<template>
	<div class="ba-page">
		<el-empty :description="t('nav.placeholder')" />
	</div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>
