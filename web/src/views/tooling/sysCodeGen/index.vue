<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('sysCodeGen.title') }}</h3>
				<p class="ba-sub">
					{{ t('sysCodeGen.sub') }}<strong>{{ t('sysCodeGen.subStrong') }}</strong>{{ t('sysCodeGen.subTail') }}
				</p>
			</div>
			<el-button v-if="canTables" :loading="loadingTables" @click="loadTables">
				<el-icon><Refresh /></el-icon>{{ t('sysCodeGen.btnRefreshTables') }}
			</el-button>
		</div>

		<!-- 目标表:未授权(权限键 sysCodeGen/tables)既不渲染也不请求 -->
		<div v-if="canTables" v-perm="'sysCodeGen/tables'" class="ba-card ba-card-padded">
			<div class="section-title">
				{{ t('sysCodeGen.cardTargetTable') }}
				<span class="section-hint">{{ t('sysCodeGen.hintTargetTable') }}</span>
			</div>
			<div class="form-row">
				<el-input
					v-model="keyword"
					class="kw-input"
					:placeholder="t('sysCodeGen.phKeyword')"
					clearable
					@keyup.enter="loadTables"
					@clear="loadTables"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
				<el-button :loading="loadingTables" @click="loadTables">{{ t('common.search') }}</el-button>
				<el-select
					v-model="selectedTableName"
					class="table-select"
					filterable
					clearable
					:placeholder="t('sysCodeGen.phSelectTable')"
				>
					<el-option v-for="t in tables" :key="t.tableName" :label="tableLabel(t)" :value="t.tableName" />
				</el-select>
				<span class="hint">{{ t('sysCodeGen.tableCount', { count: tables.length }) }} · {{ selectionHint }}</span>
			</div>
		</div>

		<!-- 生成参数与触发:权限键 sysCodeGen/preview -->
		<div v-if="canPreview" v-perm="'sysCodeGen/preview'" class="ba-card ba-card-padded card-gap">
			<div class="section-title">
				{{ t('sysCodeGen.cardGenParams') }}
				<span class="section-hint">{{ t('sysCodeGen.hintGenParams') }}</span>
			</div>
			<div class="form-row">
				<el-input v-model="form.className" class="p-input" :placeholder="t('sysCodeGen.phClassName')" clearable />
				<el-input v-model="form.moduleName" class="p-input" :placeholder="t('sysCodeGen.phModuleName')" clearable />
				<el-input v-model="form.removePrefix" class="p-input" :placeholder="t('sysCodeGen.phRemovePrefix')" clearable />
				<el-select v-model="form.baseType" class="p-select" clearable :placeholder="t('sysCodeGen.phBaseType')">
					<el-option label="EntityBase" value="EntityBase" />
					<el-option label="EntityTenant" value="EntityTenant" />
				</el-select>
				<el-button type="primary" :loading="loadingPreview" :disabled="!selectedTableName" @click="doPreview">
					<el-icon><MagicStick /></el-icon>{{ t('sysCodeGen.btnPreview') }}
				</el-button>
			</div>
		</div>

		<!-- 生成提示(如"未知列类型已回落 string"):逐条展示 -->
		<el-alert v-if="preview && preview.warnings.length" class="card-gap" type="warning" :closable="false" :title="t('sysCodeGen.warnTitle')">
			<ul class="warn-list">
				<li v-for="(w, i) in preview.warnings" :key="i">{{ w }}</li>
			</ul>
		</el-alert>

		<!-- 预览区:三段文本 + 逐块复制 -->
		<div class="ba-card ba-card-padded card-gap">
			<div class="section-title">
				{{ t('sysCodeGen.cardResult') }}
				<span class="section-hint">{{ preview ? t('sysCodeGen.resultHint', { table: preview.tableName, cls: preview.className }) : t('sysCodeGen.resultEmptyHint') }}</span>
			</div>
			<el-tabs v-if="preview" v-model="activeTab">
				<el-tab-pane v-for="seg in segments" :key="seg.key" :label="seg.label" :name="seg.key">
					<div class="code-wrap">
						<el-button class="copy-btn" size="small" @click="copyText(seg.text, seg.label)">
							<el-icon><DocumentCopy /></el-icon>{{ t('sysCodeGen.btnCopy') }}
						</el-button>
						<pre class="code">{{ seg.text || t('sysCodeGen.emptyCode') }}</pre>
					</div>
				</el-tab-pane>
			</el-tabs>
			<el-empty v-else :description="emptyText" :image-size="60" />
		</div>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'SysCodeGen' })

import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { DocumentCopy, MagicStick, Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as codeGenApi from '@/api/sys/codeGen'
import type { CodeGenPreviewOutput, DbTableOutput } from '@/api/sys/codeGen'
import { useMenuStore } from '@/stores/menu'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const menuStore = useMenuStore()
const userStore = useUserStore()

/** 与 v-perm 同口径(超管直通):未授权分块既不渲染也不请求(v-perm 只摘 DOM,拦不住 mounted 拉数)。 */
function hasPerm(key: string): boolean {
	return userStore.user?.accountType === 999 || menuStore.permissions.includes(key)
}
const canTables = hasPerm('sysCodeGen/tables')
const canPreview = hasPerm('sysCodeGen/preview')

/* ── 目标表 ─────────────────────────────── */
const keyword = ref('')
const tables = ref<DbTableOutput[]>([])
const loadingTables = ref(false)
/** 选中表名(''＝未选) */
const selectedTableName = ref('')

/* ── 生成参数(四个可选字段留空＝交给后端缺省) ─────────────────────────────── */
const form = reactive({
	className: '',
	moduleName: '',
	removePrefix: '',
	baseType: ''
})

/* ── 预览结果 ─────────────────────────────── */
const preview = ref<CodeGenPreviewOutput | null>(null)
const loadingPreview = ref(false)
const activeTab = ref<'entity' | 'dto' | 'service'>('entity')

/** 三段文本(模板里按 tab 遍历渲染,避免三份复制粘贴的块) */
interface CodeSegment {
	key: 'entity' | 'dto' | 'service'
	label: string
	text: string
}

const segments = computed<CodeSegment[]>(() => [
	{ key: 'entity', label: t('sysCodeGen.segEntity'), text: preview.value?.entityCode ?? '' },
	{ key: 'dto', label: t('sysCodeGen.segDto'), text: preview.value?.dtoCode ?? '' },
	{ key: 'service', label: t('sysCodeGen.segService'), text: preview.value?.serviceCode ?? '' }
])

/** 下拉选项文案:有注释则附注(便于同前缀表区分) */
function tableLabel(row: DbTableOutput): string {
	return row.comment
		? t('sysCodeGen.tableWithComment', { table: row.tableName, comment: row.comment })
		: row.tableName
}

/** 当前选中表(选中项可能已被关键字过滤掉,故按名回查) */
const selectedTable = computed<DbTableOutput | null>(
	() => tables.value.find(t => t.tableName === selectedTableName.value) ?? null
)

const selectionHint = computed(() => {
	const s = selectedTable.value
	if (!s) return t('sysCodeGen.notSelected')
	return t('sysCodeGen.selectionHint', {
		table: s.tableName,
		rows: s.rowEstimate,
		size: s.totalSize,
		indexes: s.indexCount
	})
})

const emptyText = computed(() =>
	selectedTableName.value ? t('sysCodeGen.previewNotGenerated') : t('sysCodeGen.selectTableFirst')
)

/** 拉表清单(失败由全局响应拦截器统一弹错,此处不 catch)。 */
async function loadTables(): Promise<void> {
	if (!canTables) return
	loadingTables.value = true
	try {
		tables.value = await codeGenApi.listCodeGenTables(keyword.value.trim() || null)
		// 选中表已被关键字过滤掉:清空选择(并连带清空已生成的预览,避免展示与选中不一致的文本)
		if (selectedTableName.value && !tables.value.some(t => t.tableName === selectedTableName.value)) {
			selectedTableName.value = ''
		}
	} finally {
		loadingTables.value = false
	}
}

watch(selectedTableName, () => {
	// 换表即作废旧预览(文本属于上一张表,留着易误复制)
	preview.value = null
	activeTab.value = 'entity'
})

/** 生成预览:只读接口,无写盘动作;业务失败交全局拦截器弹错。 */
async function doPreview(): Promise<void> {
	if (!canPreview || !selectedTableName.value) return
	loadingPreview.value = true
	// 发起预览即作废旧结果:参数/表可能已变,旧参数源码不得残留(否则可被误拷),失败时也保持清空
	preview.value = null
	try {
		preview.value = await codeGenApi.previewCodeGen({
			tableName: selectedTableName.value,
			// 空串→null:让后端缺省规则生效(className 按表名推导 / removePrefix 回落 sys_)
			className: form.className.trim() || null,
			moduleName: form.moduleName.trim() || null,
			removePrefix: form.removePrefix.trim() || null,
			baseType: form.baseType || null
		})
		activeTab.value = 'entity'
	} finally {
		loadingPreview.value = false
	}
}

/** execCommand('copy') 兜底:非安全上下文(如内网 http)下 clipboard API 不可用,用离屏 textarea 选中复制。 */
function fallbackCopy(text: string): boolean {
	const ta = document.createElement('textarea')
	ta.value = text
	ta.setAttribute('readonly', 'readonly')
	ta.style.position = 'fixed'
	ta.style.top = '-1000px'
	ta.style.opacity = '0'
	document.body.appendChild(ta)
	ta.select()
	let ok = false
	try {
		ok = document.execCommand('copy')
	} catch {
		ok = false
	}
	document.body.removeChild(ta)
	return ok
}

async function copyText(text: string, label: string): Promise<void> {
	if (!text) {
		ElMessage.warning(t('sysCodeGen.copyEmpty'))
		return
	}
	try {
		await navigator.clipboard.writeText(text)
		ElMessage.success(t('sysCodeGen.copySuccess', { label }))
	} catch {
		// 剪贴板 API 被拒(权限/非 https)→ 兜底并如实提示所用方式
		if (fallbackCopy(text)) {
			ElMessage.success(t('sysCodeGen.copySuccessFallback', { label }))
		} else {
			ElMessage.warning(t('sysCodeGen.copyDenied'))
		}
	}
}

onMounted(() => {
	void loadTables()
})
</script>

<style scoped>
.section-title {
	font-size: 14px;
	font-weight: 600;
	margin-bottom: 12px;
}
.section-hint {
	font-size: 12px;
	color: var(--ba-text-tertiary);
	font-weight: 400;
	margin-left: 8px;
}

.form-row {
	display: flex;
	align-items: center;
	gap: 10px;
	flex-wrap: wrap;
}
.kw-input {
	width: 240px;
}
.table-select {
	width: 340px;
}
.p-input {
	width: 250px;
}
.p-select {
	width: 200px;
}
.hint {
	font-size: 12px;
	color: var(--ba-text-tertiary);
}

.card-gap {
	margin-top: 14px;
}
.warn-list {
	margin: 0;
	padding-left: 18px;
}

.code-wrap {
	position: relative;
}
.copy-btn {
	position: absolute;
	top: 8px;
	right: 8px;
	z-index: 1;
}
.code {
	margin: 0;
	padding: 12px;
	max-height: 520px;
	overflow: auto;
	background: var(--ba-bg);
	border: 1px solid var(--ba-border);
	border-radius: var(--ba-radius-sm);
	font-family: ui-monospace, Menlo, Consolas, monospace;
	font-size: 12.5px;
	line-height: 1.55;
	white-space: pre;
	tab-size: 4;
}
</style>