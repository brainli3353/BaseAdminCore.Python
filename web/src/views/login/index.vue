<template>
	<div class="login-shell">
		<!-- 左:品牌面板(靛蓝渐变 + 几何光斑) -->
		<div class="login-brand">
			<div class="brand-orb orb-a" />
			<div class="brand-orb orb-b" />
			<div class="brand-content">
				<div class="brand-mark">
					<div class="brand-logo-lg">{{ brandInitial() }}</div>
					<span class="brand-name">{{ brand.name }}</span>
				</div>
				<h1 class="brand-title">{{ loginTitle }}</h1>
				<p class="brand-slogan">{{ t('login.slogan') }}</p>
				<ul class="brand-points">
					<li><el-icon><Lock /></el-icon> {{ t('login.featOtp') }}</li>
					<li><el-icon><Share /></el-icon> {{ t('login.featRbac') }}</li>
					<li><el-icon><Coin /></el-icon> {{ t('login.featAudit') }}</li>
				</ul>
				<footer class="brand-footer">© 2026 {{ brand.fullName }} · Native ASP.NET Core</footer>
			</div>
		</div>

		<!-- 右:登录卡片 -->
		<div class="login-panel">
			<div class="login-card">
				<!-- 步骤一:账号密码初验 -->
				<template v-if="step === 1">
					<h2 class="card-title">{{ loginTitle }}</h2>
					<el-form class="login-form" @submit.prevent="onStep1">
						<el-form-item>
							<el-input
								v-model="form.account"
								:placeholder="t('login.accountPlaceholder')"
								:prefix-icon="User"
								size="large"
								clearable
								@keyup.enter="onStep1"
							/>
						</el-form-item>
						<el-form-item>
							<el-input
								v-model="form.password"
								type="password"
								:placeholder="t('login.passwordPlaceholder')"
								:prefix-icon="Lock"
								size="large"
								show-password
								@keyup.enter="onStep1"
							/>
						</el-form-item>
						<el-button
							type="primary"
							size="large"
							class="login-btn"
							:loading="loading"
							@click="onStep1"
						>
							{{ t('login.submit') }}
						</el-button>
					</el-form>
				</template>

				<!-- 步骤二:OTP 动态码(首次登录附带绑定引导) -->
				<template v-else-if="step === 2 && challenge">
					<el-button text class="back-btn" @click="backToStep1">
						<el-icon><ArrowLeft /></el-icon>{{ t('login.back') }}
					</el-button>
					<h2 class="card-title">{{ t('login.otpStep') }}</h2>
					<p class="card-hint">{{ t('login.otpHint') }}</p>

					<div v-if="challenge.bindRequired" class="bind-box">
						<p class="bind-tip">{{ t('login.binding') }}</p>
						<img v-if="qrDataUrl" :src="qrDataUrl" class="qr" alt="Authenticator QR" />
						<div class="secret-row">
							<span class="secret-label">{{ t('login.bindingManual') }}</span>
							<code class="secret-code">{{ challenge.secret }}</code>
							<el-button size="small" text type="primary" @click="copySecret">
								<el-icon><CopyDocument /></el-icon>
							</el-button>
						</div>
					</div>

					<el-form class="login-form" @submit.prevent="onStep2">
						<el-form-item>
							<el-input
								v-model="otpCode"
								maxlength="6"
								class="otp-input"
								:placeholder="t('login.otpCodePlaceholder')"
								size="large"
								@keyup.enter="onStep2"
							/>
						</el-form-item>
						<el-button
							type="primary"
							size="large"
							class="login-btn"
							:loading="loading"
							@click="onStep2"
						>
							{{ t('login.verify') }}
						</el-button>
					</el-form>
				</template>

				<!-- 步骤三:密码到期强制改密(改密触发 TokenVersion++,旧令牌作废 → 重新登录) -->
				<template v-else-if="step === 3">
					<h2 class="card-title">
						<el-icon class="warn-icon"><WarningFilled /></el-icon>
						{{ t('login.passwordExpiredTitle') }}
					</h2>
					<p class="card-hint">{{ t('login.passwordExpiredHint') }}</p>
					<el-form class="login-form" @submit.prevent="onChangePassword">
						<el-form-item>
							<el-input
								v-model="pwForm.oldPassword"
								type="password"
								show-password
								:placeholder="t('login.oldPassword')"
								:prefix-icon="Lock"
								size="large"
							/>
						</el-form-item>
						<el-form-item>
							<el-input
								v-model="pwForm.newPassword"
								type="password"
								show-password
								:placeholder="t('login.newPassword')"
								:prefix-icon="Lock"
								size="large"
								@keyup.enter="onChangePassword"
							/>
						</el-form-item>
						<el-button
							type="primary"
							size="large"
							class="login-btn"
							:loading="loading"
							@click="onChangePassword"
						>
							{{ t('login.changeAndEnter') }}
						</el-button>
					</el-form>
				</template>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
	ArrowLeft,
	Coin,
	CopyDocument,
	Lock,
	Share,
	User,
	WarningFilled
} from '@element-plus/icons-vue'
import QRCode from 'qrcode'
import { brand, brandInitial, composeTitle } from '@/config/brand'
import * as authApi from '@/api/auth'
import { useUserStore } from '@/stores/user'
import type { LoginChallenge } from '@/types/api'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// 站点身份(批 AY G24;批 BA):标题随运行期品牌变化;后缀语义与浏览器标签同源——
// 后端显式配了 TitleSuffix(含空串)就用它,未配则按**当前语言**兜底(zh「管理台」/en「Admin」)
const loginTitle = computed(() =>
	composeTitle(brand.fullName, brand.titleSuffix, brand.titleSuffixConfigured, t('login.brandSuffix'))
)
const userStore = useUserStore()

const step = ref<1 | 2 | 3>(1)
const loading = ref(false)
const form = reactive({ account: '', password: '' })
const challenge = ref<LoginChallenge | null>(null)
const otpCode = ref('')
const qrDataUrl = ref('')
const pwForm = reactive({ oldPassword: '', newPassword: '' })

onMounted(() => {
	// 已持有有效会话直接放行(登录页守卫也会拦截,此处双保险)
	if (userStore.isLoggedIn) {
		router.replace('/')
	}
})

async function onStep1(): Promise<void> {
	if (!form.account || !form.password) {
		ElMessage.warning(t('login.accountPlaceholder') + ' / ' + t('login.passwordPlaceholder'))
		return
	}
	loading.value = true
	try {
		const result = await authApi.postLogin(form.account, form.password)
		// 批 BB:OTP 全局开关关闭 → 后端直接签发令牌(带 accessToken),与 onStep2 成功块同口径;
		// 开关开启 → 挑战分支(无 accessToken),按原逻辑进 step2
		if ('accessToken' in result) {
			userStore.setSession(result.accessToken, result.refreshToken, result.passwordExpired)
			if (result.passwordExpired) {
				step.value = 3
				return
			}
			enterSystem()
			return
		}
		challenge.value = result
		otpCode.value = ''
		step.value = 2
		if (challenge.value.bindRequired && challenge.value.otpauthUri) {
			qrDataUrl.value = await QRCode.toDataURL(challenge.value.otpauthUri, {
				width: 200,
				margin: 1,
				color: { dark: '#111827', light: '#ffffff' }
			})
		}
	} catch {
		// 失败提示已由 http 拦截器统一弹出(request.ts:401 凭据错误分支 / 业务码分支);
		// 这里只吞掉拒绝,避免 "未处理 Promise 拒绝" 控制台噪声,不重复提示。
	} finally {
		loading.value = false
	}
}

async function onStep2(): Promise<void> {
	if (!challenge.value || otpCode.value.length !== 6) {
		ElMessage.warning(t('login.otpCodePlaceholder'))
		return
	}
	loading.value = true
	try {
		const result = await authApi.postLoginOtp(challenge.value.challengeId, otpCode.value)
		userStore.setSession(result.accessToken, result.refreshToken, result.passwordExpired)
		if (result.passwordExpired) {
			step.value = 3
			return
		}
		enterSystem()
	} catch {
		// 失败提示已由 http 拦截器统一弹出(request.ts:401 凭据错误分支 / 业务码分支);
		// 这里只吞掉拒绝,避免 "未处理 Promise 拒绝" 控制台噪声,不重复提示。
		// 批 AX F4:清空输入——动态码 30s 一步、**用过即废**(后端防重放),不清空会让用户反复提交
		// 同一个已消费的码并看到"校验码验证失败"(2026-09-28 实测困惑点)。
		otpCode.value = ''
	} finally {
		loading.value = false
	}
}

async function onChangePassword(): Promise<void> {
	if (!pwForm.oldPassword || !pwForm.newPassword) {
		ElMessage.warning(t('login.oldPassword') + ' / ' + t('login.newPassword'))
		return
	}
	loading.value = true
	try {
		await authApi.postUpdatePassword(pwForm.oldPassword, pwForm.newPassword)
		// 改密触发 TokenVersion++:刚签发的令牌即刻作废 → 清会话回步骤一重新登录
		userStore.reset()
		pwForm.oldPassword = ''
		pwForm.newPassword = ''
		challenge.value = null
		step.value = 1
		ElMessage.success(t('common.success'))
	} catch {
		// 失败提示已由 http 拦截器统一弹出(request.ts:401 凭据错误分支 / 业务码分支);
		// 这里只吞掉拒绝,避免 "未处理 Promise 拒绝" 控制台噪声,不重复提示。
	} finally {
		loading.value = false
	}
}

function backToStep1(): void {
	challenge.value = null
	qrDataUrl.value = ''
	otpCode.value = ''
	step.value = 1
}

function copySecret(): void {
	const secret = challenge.value?.secret
	if (!secret) return
	void navigator.clipboard.writeText(secret).then(
		() => ElMessage.success('OK'),
		() => ElMessage.error('Copy failed')
	)
}

function enterSystem(): void {
	const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
	router.push(redirect || '/')
}
</script>

<style scoped>
.login-shell {
	display: flex;
	height: 100vh;
	overflow: hidden;
}

/* ── 左:品牌面板 ─────────────────────────── */
.login-brand {
	flex: 1.2;
	position: relative;
	display: flex;
	align-items: center;
	justify-content: center;
	background:
		radial-gradient(ellipse 80% 60% at 20% 10%, rgb(99 102 241 / 35%), transparent 60%),
		radial-gradient(ellipse 70% 50% at 90% 90%, rgb(79 70 229 / 30%), transparent 55%),
		linear-gradient(160deg, #1e1b4b 0%, #312e81 55%, #4f46e5 130%);
	overflow: hidden;
}
.brand-orb {
	position: absolute;
	border-radius: 50%;
	filter: blur(60px);
	opacity: 0.5;
}
.orb-a {
	width: 340px;
	height: 340px;
	background: #6366f1;
	top: -80px;
	right: -60px;
}
.orb-b {
	width: 280px;
	height: 280px;
	background: #a5b4fc;
	bottom: -100px;
	left: -40px;
	opacity: 0.3;
}

.brand-content {
	position: relative;
	color: #fff;
	padding: 48px;
	max-width: 520px;
}
.brand-mark {
	display: flex;
	align-items: center;
	gap: 12px;
	margin-bottom: 40px;
}
.brand-logo-lg {
	width: 44px;
	height: 44px;
	border-radius: 12px;
	background: rgb(255 255 255 / 14%);
	backdrop-filter: blur(8px);
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24px;
	font-weight: 700;
}
.brand-name {
	font-size: 20px;
	font-weight: 600;
	letter-spacing: 0.5px;
}
.brand-title {
	font-size: 30px;
	font-weight: 700;
	margin: 0 0 12px;
	letter-spacing: 0.3px;
}
.brand-slogan {
	font-size: 15px;
	color: rgb(255 255 255 / 72%);
	margin: 0 0 40px;
}
.brand-points {
	list-style: none;
	margin: 0;
	padding: 0;
	display: flex;
	flex-direction: column;
	gap: 14px;
}
.brand-points li {
	display: flex;
	align-items: center;
	gap: 10px;
	font-size: 14px;
	color: rgb(255 255 255 / 82%);
}
.brand-points .el-icon {
	color: #a5b4fc;
	font-size: 17px;
}
.brand-footer {
	margin-top: 56px;
	font-size: 12px;
	color: rgb(255 255 255 / 40%);
}

/* ── 右:登录卡片 ─────────────────────────── */
.login-panel {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	background: var(--ba-bg);
	padding: 32px;
}
.login-card {
	width: 100%;
	max-width: 400px;
	background: var(--ba-bg-elevated);
	border: 1px solid var(--ba-border);
	border-radius: 20px;
	box-shadow: var(--ba-shadow-lg);
	padding: 40px 36px;
}
.card-title {
	font-size: 20px;
	font-weight: 700;
	margin: 0 0 8px;
	display: flex;
	align-items: center;
	gap: 8px;
}
.warn-icon {
	color: var(--ba-warning);
}
.card-hint {
	font-size: 13px;
	color: var(--ba-text-tertiary);
	margin: 0 0 20px;
}
.back-btn {
	padding: 0;
	height: auto;
	color: var(--ba-text-tertiary);
	margin-bottom: 4px;
}
.back-btn:hover {
	color: var(--ba-brand);
}

.login-form {
	margin-top: 8px;
}
.login-form :deep(.el-input__wrapper) {
	padding: 4px 12px;
	border-radius: 10px;
}
.login-btn {
	width: 100%;
	margin-top: 4px;
	border-radius: 10px;
	font-weight: 600;
	letter-spacing: 2px;
}

/* OTP 输入:大字号 + 字距,验证码观感 */
.otp-input :deep(.el-input__inner) {
	text-align: center;
	font-size: 20px !important;
	letter-spacing: 12px;
	font-weight: 600;
	font-family: 'SF Mono', 'Consolas', monospace;
}

/* 绑定引导 */
.bind-box {
	background: var(--ba-brand-soft);
	border: 1px solid var(--ba-brand-soft-border);
	border-radius: 14px;
	padding: 18px;
	margin-bottom: 18px;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 10px;
}
.bind-tip {
	margin: 0;
	font-size: 13px;
	font-weight: 600;
	color: var(--ba-brand);
}
.qr {
	width: 180px;
	height: 180px;
	border-radius: 10px;
	border: 1px solid var(--ba-border);
	background: #fff;
}
.secret-row {
	display: flex;
	align-items: center;
	gap: 8px;
	width: 100%;
	justify-content: center;
}
.secret-label {
	font-size: 12px;
	color: var(--ba-text-secondary);
}
.secret-code {
	font-size: 12px;
	background: var(--ba-bg-elevated);
	border: 1px solid var(--ba-border);
	border-radius: 6px;
	padding: 2px 8px;
	font-family: 'SF Mono', 'Consolas', monospace;
	max-width: 180px;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

/* 窄屏:品牌面板折叠为顶部条 */
@media (max-width: 860px) {
	.login-shell {
		flex-direction: column;
	}
	.login-brand {
		display: none;
	}
}
</style>
