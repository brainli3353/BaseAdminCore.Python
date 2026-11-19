<template>
	<header class="topbar">
		<div class="topbar-left">
			<el-icon class="icon-btn" @click="appStore.toggleSidebar()">
				<component :is="appStore.sidebarCollapsed ? 'Expand' : 'Fold'" />
			</el-icon>
			<el-breadcrumb separator="/" class="crumb">
				<el-breadcrumb-item v-for="(c, i) in crumbs" :key="i">{{ c }}</el-breadcrumb-item>
			</el-breadcrumb>
		</div>
		<div class="topbar-right">
			<el-tooltip :content="appStore.isDark ? t('layout.lightMode') : t('layout.darkMode')" placement="bottom">
				<el-icon class="icon-btn" @click="appStore.toggleDark()">
					<component :is="appStore.isDark ? 'Sunny' : 'Moon'" />
				</el-icon>
			</el-tooltip>
			<el-tooltip :content="t('layout.lang')" placement="bottom">
				<span class="icon-btn lang-btn" @click="toggleLang">{{ t('layout.lang') }}</span>
			</el-tooltip>
			<el-dropdown @command="onCommand">
				<div class="user-chip">
					<div class="avatar">{{ avatarChar }}</div>
					<span class="user-name">{{ userStore.user?.realName || userStore.user?.account }}</span>
					<el-icon class="chip-arrow"><ArrowDown /></el-icon>
				</div>
				<template #dropdown>
					<el-dropdown-menu>
						<el-dropdown-item command="logout">
							<el-icon><SwitchButton /></el-icon>{{ t('layout.logout') }}
						</el-dropdown-item>
					</el-dropdown-menu>
				</template>
			</el-dropdown>
		</div>
	</header>

	<!-- 未读公告弹窗(登录进入主布局后延迟一次拉取;4.11 升级公告以「系统升级」类型承载) -->
	<el-dialog v-model="noticeDlg.visible" title="系统更新/公告" width="620px" append-to-body>
		<div v-if="noticeDlg.list.length" class="notice-list">
			<div v-for="n in noticeDlg.list" :key="n.id" class="notice-item">
				<h4 class="notice-title">{{ n.title }}</h4>
				<p class="notice-meta">
					{{ noticeTypeText(n.type) }}<template v-if="n.createTime"> · {{ n.createTime }}</template>
				</p>
				<!-- 内容为后端富文本:渲染前做最小净化(剥离 script/iframe 与 on* 内联事件、javascript: 协议) -->
				<div class="notice-content" v-html="sanitizeHtml(n.content)" />
			</div>
		</div>
		<template #footer>
			<el-button type="primary" @click="onNoticeAck">我知道了</el-button>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessageBox } from 'element-plus'
import { ArrowDown, SwitchButton } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { i18n } from '@/i18n'
import { menuTitle } from '@/utils/menuTitle'
import * as noticeApi from '@/api/sys/notice'
import type { NoticeOutput } from '@/api/sys/notice'

const route = useRoute()
const { t } = useI18n()

/** 公告类型标签(批 AP:走 i18n,替代 api 层静态中文映射;未知取值容错为「类型 N」) */
function noticeTypeText(type: number): string {
	if (type === 1) return t('sysNotice.typeNotice')
	if (type === 2) return t('sysNotice.typeAnnouncement')
	if (type === 3) return t('sysNotice.typeUpgrade')
	return t('sysNotice.typeFallback', { type })
}
const appStore = useAppStore()
const userStore = useUserStore()

const crumbs = computed(() =>
	route.matched
		.filter(r => r.meta?.title && r.path !== '/')
		.map(r => menuTitle(r.name, r.meta.title as string))
)

const avatarChar = computed(() => (userStore.user?.realName || userStore.user?.account || '?').slice(0, 1).toUpperCase())

function toggleLang(): void {
	// 三向同步:store(写 localStorage 持久化)↔ i18n 全局 locale(业务文案 + request.ts 的
	// Accept-Language 取值来源);EP 内置文案由 App.vue 的 el-config-provider 计算属性跟随 i18n
	appStore.setLang(appStore.lang === 'zh-CN' ? 'en-US' : 'zh-CN')
	i18n.global.locale.value = appStore.lang
}

async function onCommand(cmd: string): Promise<void> {
	if (cmd === 'logout') {
		try {
			await ElMessageBox.confirm(t('layout.logoutConfirm'), t('layout.logout'), { type: 'warning' })
		} catch {
			return
		}
		await userStore.logout()
		window.location.href = '/login'
	}
}

/* ── 未读公告弹窗(自读面 /api/sysNotice/unReadList + setRead) ───────────── */
/** 登录后延迟拉取的延时:避开登录跳转瞬间,不打断首屏 */
const NOTICE_FETCH_DELAY_MS = 1200

const noticeDlg = reactive({ visible: false, list: [] as NoticeOutput[] })
/** 同一布局挂载只自动拉取一次(关闭后本会话不再弹) */
let noticeLoaded = false

/** 最小净化:剥离 <script>/<style>/<iframe>/<object>/<embed> 元素与 on* 内联事件、javascript: 协议。
 * WHY 不引净化库:新增依赖超出本件范围;公告内容来源=管理台自身发布,取最小防线即可。 */
function sanitizeHtml(raw: string | null): string {
	if (!raw) {
		return ''
	}
	return raw
		// 成对标签(含其内容)整体剥除
		.replace(/<\s*(script|style|iframe|object|embed)\b[^>]*>[\s\S]*?<\s*\/\s*\1\s*>/gi, '')
		// 自闭合/未闭合的残留标签
		.replace(/<\s*\/?\s*(script|style|iframe|object|embed)\b[^>]*>/gi, '')
		// on* 内联事件属性(带引号/不带引号两种形态)
		.replace(/\son[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, '')
		// href/src 的 javascript: 协议(中性化为 #)
		.replace(/\b(href|src)\s*=\s*(?:"[^"]*javascript:[^"]*"|'[^']*javascript:[^']*'|javascript:[^\s>]+)/gi, '$1="#"')
}

/** 拉取未读公告:非空则弹窗;失败在 api 层静默(不弹错打断登录) */
async function loadUnReadNotices(): Promise<void> {
	if (noticeLoaded) {
		return
	}
	noticeLoaded = true
	const list = await noticeApi.unReadNoticeList()
	if (list.length) {
		noticeDlg.list = list
		noticeDlg.visible = true
	}
}

/** 「我知道了」:逐条标记已读并关闭(标记失败的条目下次登录仍会提示) */
async function onNoticeAck(): Promise<void> {
	noticeDlg.visible = false
	const list = noticeDlg.list
	noticeDlg.list = []
	for (const n of list) {
		await noticeApi.setNoticeRead(n.id)
	}
}

onMounted(() => {
	window.setTimeout(() => {
		void loadUnReadNotices()
	}, NOTICE_FETCH_DELAY_MS)
})
</script>

<style scoped>
.topbar {
	height: var(--ba-topbar-h);
	flex-shrink: 0;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 16px;
	background: var(--ba-bg-elevated);
	border-bottom: 1px solid var(--ba-border);
}

.topbar-left,
.topbar-right {
	display: flex;
	align-items: center;
	gap: 10px;
}

.icon-btn {
	font-size: 18px;
	color: var(--ba-text-secondary);
	cursor: pointer;
	padding: 6px;
	border-radius: var(--ba-radius-sm);
	display: flex;
	align-items: center;
	transition: all 0.15s ease;
}
.icon-btn:hover {
	color: var(--ba-text);
	background: var(--ba-bg-hover);
}
.lang-btn {
	font-size: 12px;
	font-weight: 600;
	min-width: 30px;
	justify-content: center;
}

.crumb :deep(.el-breadcrumb__inner) {
	color: var(--ba-text-tertiary);
	font-size: 13px;
}
.crumb :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
	color: var(--ba-text);
	font-weight: 500;
}

.user-chip {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 4px 8px;
	border-radius: var(--ba-radius);
	cursor: pointer;
	transition: background 0.15s ease;
}
.user-chip:hover {
	background: var(--ba-bg-hover);
}
.avatar {
	width: 30px;
	height: 30px;
	border-radius: 50%;
	background: linear-gradient(135deg, #6366f1, #4338ca);
	color: #fff;
	font-size: 13px;
	font-weight: 600;
	display: flex;
	align-items: center;
	justify-content: center;
}
.user-name {
	font-size: 13px;
	color: var(--ba-text);
	font-weight: 500;
	max-width: 120px;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.chip-arrow {
	font-size: 12px;
	color: var(--ba-text-tertiary);
}

/* ── 未读公告弹窗 ───────────── */
.notice-item + .notice-item {
	margin-top: 14px;
	padding-top: 12px;
	border-top: 1px dashed var(--ba-border);
}
.notice-title {
	margin: 0 0 4px;
	font-size: 14px;
	font-weight: 600;
	color: var(--ba-text);
}
.notice-meta {
	margin: 0 0 8px;
	font-size: 12px;
	color: var(--ba-text-tertiary);
}
.notice-content {
	font-size: 13px;
	line-height: 1.7;
	color: var(--ba-text-secondary);
	word-break: break-word;
}
.notice-content :deep(img) {
	max-width: 100%;
}
.notice-content :deep(p) {
	margin: 0 0 8px;
}
.notice-content :deep(a) {
	color: var(--ba-brand);
}
</style>
