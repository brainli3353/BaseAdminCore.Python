<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysMessage.title') }}</h3>
				<p class="ba-sub">{{ t('sysMessage.sub') }}</p>
			</div>
		</div>

		<!-- 发送卡 -->
		<div class="ba-card">
			<el-form ref="formRef" :model="form" :rules="rules" label-width="84px" class="send-form">
				<el-form-item :label="t('sysMessage.labelTitle')" prop="title">
					<el-input v-model="form.title" :placeholder="t('sysMessage.phTitle')" />
				</el-form-item>
				<el-form-item :label="t('sysMessage.labelContent')" prop="message">
					<el-input v-model="form.message" type="textarea" :rows="5" :placeholder="t('sysMessage.phContent')" />
				</el-form-item>
				<el-form-item :label="t('sysMessage.labelType')" prop="messageType">
					<el-select v-model="form.messageType" class="type-select">
						<el-option :label="t('sysMessage.typeMessage')" :value="0" />
						<el-option :label="t('sysMessage.typeSuccess')" :value="1" />
						<el-option :label="t('sysMessage.typeWarning')" :value="2" />
						<el-option :label="t('sysMessage.typeError')" :value="3" />
					</el-select>
				</el-form-item>
				<el-form-item :label="t('sysMessage.labelReceiver')">
					<el-select
						v-model="form.receiveUserIds"
						multiple
						filterable
						remote
						:remote-method="remoteSearch"
						:loading="userLoading"
						collapse-tags
						collapse-tags-tooltip
						:placeholder="t('sysMessage.phReceiver')"
						class="full-width"
					>
						<el-option v-for="u in userOptions" :key="String(u.id)" :label="userLabel(u)" :value="u.id" />
					</el-select>
					<!-- 接收人元数据加载失败:行内错误 + 重试(不再纯静默,失败原因可见) -->
					<div v-if="userErr" class="ba-inline-error">
						<span>{{ userErr }}</span>
						<el-button link type="primary" size="small" @click="retryUsers">{{ t('common.retry') }}</el-button>
					</div>
				</el-form-item>
				<el-form-item>
					<el-button v-perm="'sysMessage/sendUser'" type="primary" :loading="sending" @click="onSendUsers">
						{{ t('sysMessage.btnSendUsers') }}
					</el-button>
					<el-button v-perm="'sysMessage/sendAll'" type="warning" :loading="sending" @click="onSendAll">
						{{ t('sysMessage.btnSendAll') }}
					</el-button>
				</el-form-item>
			</el-form>
		</div>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'SysMessage' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import * as messageApi from '@/api/sys/message'
import * as userApi from '@/api/sys/user'
import type { UserOutput } from '@/api/sys/user'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const userStore = useUserStore()
const userOptions = ref<UserOutput[]>([])
const userLoading = ref(false)
/** 接收人元数据最近一次加载失败原因(空串=无错;行内错误呈现,可重试) */
const userErr = ref('')
/** 最近一次拉取的关键字(重试按它重放,不丢用户输入) */
let lastKeyword = ''
const sending = ref(false)

const formRef = ref<FormInstance>()
const form = reactive({
	title: '',
	message: '',
	messageType: 0,
	receiveUserIds: [] as Array<number | string>
})
const rules = computed<FormRules>(() => ({
	title: [{ required: true, message: t('sysMessage.ruleTitleRequired'), trigger: 'blur' }],
	message: [{ required: true, message: t('sysMessage.ruleContentRequired'), trigger: 'blur' }]
}))

function userLabel(u: UserOutput): string {
	return u.realName ? `${u.account}(${u.realName})` : `${u.account}`
}

async function loadUsers(keyword: string): Promise<void> {
	lastKeyword = keyword
	userLoading.value = true
	try {
		const res = await userApi.pageUser({ account: keyword || null, pageIndex: 1, pageSize: 50 })
		// 已选项必须保留在候选项里,否则换成别的关键词后端标签会退化成裸 id
		const selected = new Set(form.receiveUserIds.map(String))
		const merged = new Map<string, UserOutput>()
		for (const u of userOptions.value) {
			if (selected.has(String(u.id))) {
				merged.set(String(u.id), u)
			}
		}
		for (const u of res.list) {
			merged.set(String(u.id), u)
		}
		userOptions.value = [...merged.values()]
		userErr.value = ''
	} catch {
		/* 用户元数据加载失败不阻塞页面:行内错误呈现可重试(.ba-inline-error,六件套 #5) */
		userErr.value = t('common.loadError')
	} finally {
		userLoading.value = false
	}
}

/** 行内错误重试:按最近一次关键字重放拉取 */
function retryUsers(): void {
	void loadUsers(lastKeyword)
}

/** 接收人远程搜索(300ms 防抖:避免每敲一键打一次接口) */
let searchTimer: ReturnType<typeof setTimeout> | undefined
function remoteSearch(keyword: string): void {
	if (searchTimer) {
		clearTimeout(searchTimer)
	}
	searchTimer = setTimeout(() => void loadUsers(keyword), 300)
}

function currentUserId(): number | string | null {
	return userStore.user?.userId ?? null
}

async function onSendUsers(): Promise<void> {
	await formRef.value?.validate()
	if (form.receiveUserIds.length === 0) {
		ElMessage.warning(t('sysMessage.msgSelectReceiver'))
		return
	}
	const sendUserId = currentUserId()
	if (sendUserId === null) {
		ElMessage.error(t('sysMessage.msgNoLoginUser'))
		return
	}
	sending.value = true
	try {
		await messageApi.sendMessageToUsers({
			messageType: form.messageType,
			title: form.title,
			message: form.message,
			sendUserId,
			receiveUserIds: form.receiveUserIds
		})
		ElMessage.success(t('sysMessage.msgSentUsers'))
		Object.assign(form, { title: '', message: '' })
	} finally {
		sending.value = false
	}
}

async function onSendAll(): Promise<void> {
	await formRef.value?.validate()
	const sendUserId = currentUserId()
	if (sendUserId === null) {
		ElMessage.error(t('sysMessage.msgNoLoginUser'))
		return
	}
	try {
		await ElMessageBox.confirm(t('sysMessage.msgSendConfirm'), t('sysMessage.msgSendConfirmTitle'), { type: 'warning' })
	} catch {
		return
	}
	sending.value = true
	try {
		await messageApi.sendMessageToAll({
			messageType: form.messageType,
			title: form.title,
			message: form.message,
			sendUserId,
			receiveUserIds: []
		})
		ElMessage.success(t('sysMessage.msgSentAll'))
		Object.assign(form, { title: '', message: '' })
	} finally {
		sending.value = false
	}
}

onMounted(() => {
	// 首屏拉前 50 条让下拉可直接点选;后续随输入远程搜索(不再一次性取 200)
	void loadUsers('')
})
</script>

<style scoped>
.send-form {
	max-width: 640px;
}

.full-width {
	width: 100%;
}
.type-select {
	width: 160px;
}
</style>