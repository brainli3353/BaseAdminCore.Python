<template>
	<div class="ba-page">
		<!-- 页头 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('apiDoc.title') }}</h3>
				<p class="ba-sub">{{ t('apiDoc.sub') }}</p>
			</div>
			<el-button-group>
				<el-button :disabled="!doc" @click="downloadJson">
					<el-icon><Download /></el-icon>{{ t('apiDoc.btnDownload') }}
				</el-button>
				<el-button :loading="loading" @click="fetchDoc">
					<el-icon><Refresh /></el-icon>{{ t('apiDoc.btnRefresh') }}
				</el-button>
			</el-button-group>
		</div>

		<!-- 主体(权限键与端点 [MenuPerm] 同键:未授权整块不渲染) -->
		<div v-perm="'apiDoc/openapi'" class="ba-body">
			<div class="split">
				<!-- 左:按控制器 tag 分组的接口清单 -->
				<div class="ba-card ba-card-padded pane list-pane">
					<!-- 批 BE:框架文档 / 业务接口 分区切换 -->
					<div class="search-row zone-row">
						<el-segmented v-model="zone" :options="zoneOptions" size="small" />
					</div>
					<div class="search-row">
						<el-input
							v-model="keyword"
							class="search-input"
							:placeholder="t('apiDoc.phSearch')"
							clearable
						>
							<template #prefix><el-icon><Search /></el-icon></template>
						</el-input>
						<span class="hint">
							{{
								t('apiDoc.hintMeta', {
									name: docLabel,
									total: zoneTotal,
									hit: hitCount,
									groups: groups.length
								})
							}}
						</span>
					</div>
					<div class="pane-scroll">
						<template v-if="filteredGroups.length">
							<div v-for="g in filteredGroups" :key="g.tag" class="group">
								<div class="group-head">
									<span class="group-tag">{{ g.tag }}</span>
									<span class="group-count">{{ t('apiDoc.groupCount', { n: g.items.length }) }}</span>
								</div>
								<div
									v-for="ep in g.items"
									:key="ep.key"
									class="ep-item"
									:class="{ active: ep.key === selectedKey }"
									@click="selectedKey = ep.key"
								>
									<div class="ep-line">
										<span class="m" :class="methodClass(ep.method)">{{ ep.method }}</span>
										<span class="ep-path">{{ ep.path }}</span>
										<span v-if="ep.perm" class="ep-perm">{{ ep.perm }}</span>
										<span v-else class="ep-noperm">{{ t('apiDoc.permLoginOnly') }}</span>
									</div>
									<div class="ep-summary">{{ ep.summary || t('apiDoc.noSummary') }}</div>
								</div>
							</div>
						</template>
						<el-empty v-else :description="emptyText" :image-size="60" />
					</div>
				</div>

				<!-- 右:选中接口详情 -->
				<div class="ba-card ba-card-padded pane detail-pane">
					<template v-if="selected">
						<div class="detail-head">
							<span class="m" :class="methodClass(selected.method)">{{ selected.method }}</span>
							<span class="detail-path">{{ selected.path }}</span>
						</div>
						<el-descriptions :column="1" border size="small">
							<el-descriptions-item :label="t('apiDoc.labelSummary')">
								{{ selected.summary || '—' }}
							</el-descriptions-item>
							<el-descriptions-item :label="t('apiDoc.labelController')">{{ selected.tag }}</el-descriptions-item>
							<el-descriptions-item label="operationId">{{ selected.operationId || '—' }}</el-descriptions-item>
							<el-descriptions-item :label="t('apiDoc.labelPerm')">
								<span v-if="selected.perm" class="ep-perm">{{ selected.perm }}</span>
								<span v-else class="ep-noperm">{{ t('apiDoc.permLoginOnlyNoMenuPerm') }}</span>
							</el-descriptions-item>
							<el-descriptions-item :label="t('apiDoc.labelResponse')">
								{{ selected.schemaName || t('apiDoc.genericObject') }}
							</el-descriptions-item>
						</el-descriptions>

						<div class="sub-title">{{ t('apiDoc.paramTitle', { n: selected.parameters.length }) }}</div>
						<el-table :data="selected.parameters" size="small" border>
							<el-table-column prop="name" :label="t('apiDoc.colName')" min-width="160" sortable />
							<el-table-column prop="in" :label="t('apiDoc.colIn')" width="80" sortable />
							<el-table-column :label="t('apiDoc.colRequired')" width="70">
								<template #default="{ row }">{{ row.required ? t('common.yes') : t('common.no') }}</template>
							</el-table-column>
							<el-table-column :label="t('apiDoc.colType')" width="90">
								<template #default="{ row }">{{ row.schema?.type ?? '—' }}</template>
							</el-table-column>
						</el-table>
					</template>
					<el-empty v-else :description="t('apiDoc.emptyPick')" :image-size="60" />
				</div>
			</div>

			<!-- 数据结构:默认联动选中接口引用的 schema;下拉可查阅全部 schemas -->
			<div class="ba-card ba-card-padded">
				<div class="search-row">
					<span class="sub-title no-margin">{{ t('apiDoc.schemaTitle') }}</span>
					<el-select
						v-model="pickedSchema"
						class="schema-select"
						filterable
						clearable
						:placeholder="t('apiDoc.phSchema')"
					>
						<el-option v-for="n in schemaNames" :key="n" :label="n" :value="n" />
					</el-select>
					<span class="hint">{{ t('apiDoc.schemaCount', { n: schemaNames.length }) }}</span>
				</div>
				<el-table v-if="schemaProps.length" :data="schemaProps" size="small" border max-height="260">
					<el-table-column prop="name" :label="t('apiDoc.colProp')" min-width="220" sortable />
					<el-table-column prop="type" :label="t('apiDoc.colType')" width="120" sortable />
				</el-table>
				<el-empty v-else :description="schemaEmptyText" :image-size="60" />
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'ApiDoc' })

import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Download, Refresh, Search } from '@element-plus/icons-vue'
import {
	getOpenApiDoc,
	type OpenApiDocument,
	type OpenApiParameter,
	type OpenApiResponse,
	type OpenApiSchema
} from '@/api/sys/apiDoc'

/** 清单里的一项接口(paths 展平结果) */
interface EndpointItem {
	/** 稳定键:`METHOD 路径`(同一路径不同方法各成一项,全局唯一) */
	key: string
	/** 大写方法名 GET/POST/PUT/DELETE… */
	method: string
	path: string
	/** 控制器 tag(tags[0];缺失归入「未分组」) */
	tag: string
	summary: string
	operationId: string
	/** 权限键;端点未标注 [MenuPerm] 时为空串 */
	perm: string
	parameters: OpenApiParameter[]
	/** 响应 $ref 引用的 schema 名;无 $ref 时为空串 */
	schemaName: string
	/** 分区(批 BE):framework(框架文档) / business(业务接口);后端缺失时容错为 framework */
	zone: 'framework' | 'business'
}

/** schema 属性行(展示用) */
interface SchemaPropRow {
	name: string
	type: string
}

/** HTTP 方法键白名单(路径条目下可能混入 parameters/summary 等扩展键,一律忽略) */
const HTTP_METHODS = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']

const { t } = useI18n()

const loading = ref(false)
const doc = ref<OpenApiDocument | null>(null)
const keyword = ref('')
/** 当前分区(批 BE):framework(框架文档) / business(业务接口) */
const zone = ref<'framework' | 'business'>('framework')
/** 当前选中接口的键(''＝未选) */
const selectedKey = ref('')
/** 数据结构区当前查阅的 schema 名(随选中接口联动,也可在上方下拉里改) */
const pickedSchema = ref('')

/** paths 展平为接口清单(方法键统一大写) */
function flatten(d: OpenApiDocument | null): EndpointItem[] {
	const items: EndpointItem[] = []
	for (const [path, pathItem] of Object.entries(d?.paths ?? {})) {
		for (const [verb, op] of Object.entries(pathItem ?? {})) {
			if (!HTTP_METHODS.includes(verb.toLowerCase())) continue
			const method = verb.toUpperCase()
			items.push({
				key: `${method} ${path}`,
				method,
				path,
				tag: op.tags?.[0] || t('apiDoc.ungrouped'),
				summary: op.summary ?? '',
				operationId: op.operationId ?? '',
				// WHY 缺省空串:x-perm 为可选字段(未标注 [MenuPerm] 的端点没有它)
				perm: op['x-perm'] ?? '',
				parameters: op.parameters ?? [],
				schemaName: refSchemaName(op.responses),
				// 批 BE:分区;x-doc-zone 缺失(旧文档)容错归框架区
				zone: op['x-doc-zone'] === 'business' ? 'business' : 'framework'
			})
		}
	}
	return items
}

/** 取响应里 content['application/json'].schema.$ref 的末段作 schema 名(无 $ref 返回空串) */
function refSchemaName(responses: Record<string, OpenApiResponse> | undefined): string {
	for (const r of Object.values(responses ?? {})) {
		const schema = r?.content?.['application/json']?.schema
		if (schema?.$ref) return schema.$ref.split('/').pop() ?? ''
	}
	return ''
}

/** 按名取 components.schemas 定义;$ref 名与键不一致时(如 ApiResult_UserOutput)去前缀兜底 */
function resolveSchema(name: string): OpenApiSchema | null {
	const schemas = doc.value?.components?.schemas
	if (!name || !schemas) return null
	return schemas[name] ?? schemas[name.replace(/^ApiResult_/, '')] ?? null
}

/** 方法徽标配色类:GET 绿 / POST 品牌蓝 / PUT·PATCH 橙 / DELETE 红,其余中性灰 */
function methodClass(method: string): string {
	return `m-${method.toLowerCase()}`
}

const endpoints = computed<EndpointItem[]>(() => flatten(doc.value))

/** 批 BE:当前分区的接口(framework/business);分区切换只影响清单区,详情区仍按全量选中 */
const zoneEndpoints = computed<EndpointItem[]>(() => endpoints.value.filter(ep => ep.zone === zone.value))

/** 当前分区接口总数(供页头 hint 展示) */
const zoneTotal = computed(() => zoneEndpoints.value.length)

/** 分区选项(el-segmented):框架文档 / 业务接口 */
const zoneOptions = computed(() => [
	{ label: t('apiDoc.zoneFramework'), value: 'framework' },
	{ label: t('apiDoc.zoneBusiness'), value: 'business' }
])

/** 按 tag(控制器)分组(仅当前分区):组名排序,组内按路径再按方法 */
const groups = computed(() => {
	const byTag = new Map<string, EndpointItem[]>()
	for (const ep of zoneEndpoints.value) {
		const list = byTag.get(ep.tag)
		if (list) list.push(ep)
		else byTag.set(ep.tag, [ep])
	}
	return [...byTag.entries()]
		.map(([tag, items]) => ({
			tag,
			items: [...items].sort((a, b) => a.path.localeCompare(b.path) || a.method.localeCompare(b.method))
		}))
		.sort((a, b) => a.tag.localeCompare(b.tag))
})

/** 本地过滤:路径 / 控制器 tag / 权限键 任一模糊命中;组内全被滤掉的组整组隐藏 */
const filteredGroups = computed(() => {
	const k = keyword.value.trim().toLowerCase()
	if (!k) return groups.value
	return groups.value
		.map(g => ({
			tag: g.tag,
			items: g.items.filter(
				ep =>
					ep.path.toLowerCase().includes(k) ||
					ep.tag.toLowerCase().includes(k) ||
					ep.perm.toLowerCase().includes(k)
			)
		}))
		.filter(g => g.items.length)
})

const hitCount = computed(() => filteredGroups.value.reduce((n, g) => n + g.items.length, 0))

const selected = computed<EndpointItem | null>(
	() => endpoints.value.find(ep => ep.key === selectedKey.value) ?? null
)

const info = computed(() => doc.value?.info ?? null)

const docLabel = computed(() =>
	info.value
		? `${info.value.title ?? 'API'} v${info.value.version ?? '?'}`
		: loading.value
			? t('common.loading')
			: t('apiDoc.noDocInfo')
)

const emptyText = computed(() => {
	if (loading.value) return t('common.loading')
	if (keyword.value.trim()) return t('apiDoc.emptyNoMatch')
	// 批 BE:业务区当前无接口时给出语义化空态(框架区用通用空态)
	if (zone.value === 'business') return t('apiDoc.emptyBusiness')
	return t('apiDoc.emptyNoEndpoints')
})

const schemaNames = computed(() =>
	Object.keys(doc.value?.components?.schemas ?? {}).sort((a, b) => a.localeCompare(b))
)

const currentSchema = computed<OpenApiSchema | null>(() => resolveSchema(pickedSchema.value))

const schemaProps = computed<SchemaPropRow[]>(() =>
	Object.entries(currentSchema.value?.properties ?? {}).map(([name, s]) => ({
		name,
		type: s?.type ?? '—'
	}))
)

const schemaEmptyText = computed(() => {
	if (!pickedSchema.value) return t('apiDoc.emptySchemaNoRef')
	return currentSchema.value
		? t('apiDoc.emptySchemaNoProps')
		: t('apiDoc.emptySchemaNotFound', { name: pickedSchema.value })
})

// 选中接口 → 数据结构区联动其引用的 schema(该接口无引用则清空)
watch(selected, ep => {
	pickedSchema.value = ep?.schemaName ?? ''
})

/** 拉取文档:失败交全局响应拦截器统一弹错(页面不自 catch) */
async function fetchDoc(): Promise<void> {
	loading.value = true
	try {
		doc.value = await getOpenApiDoc()
	} finally {
		loading.value = false
	}
}

/** 批 BE:下载完整 OpenAPI 文档为 Swagger JSON(client-side Blob,不新增后端端点) */
function downloadJson(): void {
	const d = doc.value
	if (!d) return
	const json = JSON.stringify(d, null, 2)
	const blob = new Blob([json], { type: 'application/json' })
	const url = URL.createObjectURL(blob)
	const a = document.createElement('a')
	const version = d.info?.version
	a.href = url
	a.download = `baseadmin-openapi${version ? `-v${version}` : ''}.json`
	document.body.appendChild(a)
	a.click()
	document.body.removeChild(a)
	URL.revokeObjectURL(url)
}

// 批 BE:切分区时,若当前选中接口不在新分区则清空(避免详情区滞留另一区的接口)
watch(zone, z => {
	const sel = endpoints.value.find(ep => ep.key === selectedKey.value)
	if (sel && sel.zone !== z) selectedKey.value = ''
})

onMounted(() => {
	void fetchDoc()
})
</script>

<style scoped>
.ba-body {
	flex: 1;
	min-height: 0;
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.split {
	flex: 1;
	min-height: 0;
	display: flex;
	gap: 12px;
}

.pane {
	display: flex;
	flex-direction: column;
	min-width: 0;
}
.list-pane {
	flex: 1 1 46%;
}
.detail-pane {
	flex: 1 1 54%;
	overflow: auto;
}

.search-row {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 12px;
	flex-wrap: wrap;
}
.search-input {
	max-width: 320px;
}
.hint {
	font-size: 12px;
	color: var(--ba-text-tertiary);
}
/* 批 BE:分区切换行(复用 search-row 布局,贴紧下方搜索行) */
.zone-row {
	margin-bottom: 4px;
}
.pane-scroll {
	flex: 1;
	min-height: 0;
	overflow: auto;
}

.group {
	margin-bottom: 14px;
}
.group-head {
	display: flex;
	align-items: center;
	gap: 8px;
	border-bottom: 1px solid var(--ba-border);
	padding-bottom: 6px;
	margin-bottom: 6px;
}
.group-tag {
	font-size: 13px;
	font-weight: 600;
}
.group-count {
	font-size: 12px;
	color: var(--ba-text-tertiary);
}

.ep-item {
	padding: 6px 8px;
	border-radius: var(--ba-radius-sm);
	cursor: pointer;
}
.ep-item:hover {
	background: var(--ba-bg-hover);
}
.ep-item.active {
	background: var(--ba-brand-soft);
}
.ep-line {
	display: flex;
	align-items: center;
	gap: 8px;
	flex-wrap: wrap;
}
.ep-path {
	font-family: ui-monospace, Menlo, Consolas, monospace;
	font-size: 12px;
	word-break: break-all;
}
.ep-summary {
	font-size: 12px;
	color: var(--ba-text-secondary);
	margin-top: 2px;
}

/* 方法徽标:描边与文字同色(currentColor),色彩只取自设计令牌 */
.m {
	display: inline-block;
	min-width: 54px;
	text-align: center;
	padding: 1px 6px;
	border: 1px solid currentColor;
	border-radius: 10px;
	font-size: 11px;
	font-weight: 700;
	color: var(--ba-info);
}
.m-get {
	color: var(--ba-success);
}
.m-post {
	color: var(--ba-brand);
}
.m-put,
.m-patch {
	color: var(--ba-warning);
}
.m-delete {
	color: var(--ba-danger);
}

.ep-perm {
	font-size: 11px;
	color: var(--ba-brand);
	background: var(--ba-brand-soft);
	border-radius: 10px;
	padding: 1px 8px;
}
.ep-noperm {
	font-size: 11px;
	color: var(--ba-text-tertiary);
}

.detail-head {
	display: flex;
	align-items: center;
	gap: 8px;
	margin-bottom: 10px;
}
.detail-path {
	font-family: ui-monospace, Menlo, Consolas, monospace;
	font-size: 13px;
	font-weight: 600;
	word-break: break-all;
}
.sub-title {
	font-size: 13px;
	font-weight: 600;
	margin: 14px 0 8px;
}
.no-margin {
	margin: 0;
}
.schema-select {
	width: 260px;
}
</style>