<template>
	<!--
		页型模板 · 树表页（TreeTablePage）
		源：web/src/views/sys/sysOrg/index.vue（批 UX·2026-10-25 抽取；源页审单已 PASS）
		形态：**树形表格**（vxe-grid tree-config + 单选高亮 + 选中反馈条）——sys/sysOrg 取的是这一形态。
		  若目标页要「左树右表」：左侧换 `el-tree`（:data 同一棵树）、右侧 grid 去掉 tree-config，
		  并把本模板的 onRowClick 改挂 el-tree 的 @node-click（选中反馈条与「新增子节点」语义照抄不变）。
		抄法：整文件复制为 web/src/views/<domain>/<entity>/index.vue，再按文件内 ⚠ 标注替换三处：
		  ① 数据源（getDemoTree 示例函数 → `import * as demoApi from '@/api/<domain>/<entity>'` 的 tree 端点）
		  ② i18n 命名空间（demo.* → **新页自建命名空间**，zh-CN / en-US 两文件同键）
		  ③ 实体（DemoTreeNode → 业务树 DTO）、列定义、表单字段
		审单口径单源：docs/可用性审单_框架管理页.md。
	-->
	<div class="ba-page">
		<!-- 页头：新增顶级节点（D2）；进入后默认挂在「顶级」语义下 -->
		<div class="ba-page-header">
			<div>
				<h3 class="ba-title">{{ t('demo.title') }}</h3>
				<p class="ba-sub">{{ t('demo.sub') }}</p>
			</div>
			<el-button v-perm="'demo/add'" type="primary" @click="openAdd(selected)">
				<el-icon><Plus /></el-icon>{{ t('demo.btnAdd') }}
			</el-button>
		</div>

		<!-- 数据卡 -->
		<div class="ba-card">
			<p class="table-hint">{{ t('demo.tableHint') }}</p>
			<!-- A1 关键字：树一次全量加载，过滤在**前端递归**做（后端无对应参数，见审单边界） -->
			<div class="search-row">
				<el-input
					v-model="filterKeyword"
					:placeholder="t('demo.filterPlaceholder')"
					clearable
					class="search-input"
				>
					<template #prefix><el-icon><Search /></el-icon></template>
				</el-input>
			</div>
			<!-- 选中反馈条：让用户看得见「新增子节点会挂在谁下面」（sysDict currentType 同款写法，非控件） -->
			<p class="tree-selected">
				{{ selected ? t('demo.currentNode', { name: selected.name }) : t('demo.selectNodeHint') }}
			</p>
			<!-- B4 loading 遮罩（B6 不适用：树一次全量加载，无分页）/ C3 失败由 api/request.ts 拦截器统一透出 -->
			<vxe-grid
				:loading="loading"
				:data="filteredRows"
				:columns="columns"
				:row-config="{ keyField: 'id' }"
				:tree-config="{ rowField: 'id', expandAll: true }"
				:radio-config="{ highlight: true }"
				@cell-click="onRowClick"
			>
				<!-- B8 状态列 tag 色义 -->
				<template #cell_status="{ row }">
					<el-tag :type="row.status === 0 ? 'success' : 'info'" disable-transitions size="small">
						{{ row.status === 0 ? t('demo.statusNormal') : t('demo.statusDisabled') }}
					</el-tag>
				</template>
				<!-- B7 操作列：新增子节点 / 编辑 直出，删除折「更多」；@click.stop 防触发行选中 -->
				<template #row_ops="{ row }">
					<div @click.stop>
						<BaActionButtons :actions="rowActions(row)" @select="(i: number) => onRowAction(row, i)" />
					</div>
				</template>
				<!-- B5 空态分态 -->
				<template #empty>
					<BaEmpty :state="loading ? 'loading' : 'empty'" />
				</template>
			</vxe-grid>
		</div>

		<!-- 新增/编辑对话框（C5 / D3） -->
		<el-dialog
			v-model="dialog.visible"
			:title="dialog.mode === 'add' ? t('demo.btnAdd') : t('demo.btnEdit')"
			width="460px"
			destroy-on-close
		>
			<el-form ref="formRef" :model="form" :rules="rules" label-width="84px">
				<!-- 父级只读回显：新增子节点时显示父节点名，新增顶级显示「顶级」 -->
				<el-form-item :label="t('demo.parentNode')">
					<el-input :model-value="dialog.pidLabel" disabled />
				</el-form-item>
				<el-form-item :label="t('demo.colName')" prop="name">
					<el-input v-model="form.name" :placeholder="t('demo.phName')" />
				</el-form-item>
				<el-form-item :label="t('demo.colCode')">
					<el-input v-model="form.code" :placeholder="t('demo.phCode')" />
				</el-form-item>
				<el-form-item :label="t('demo.colSort')">
					<el-input-number v-model="form.sort" :min="0" :max="9999" />
				</el-form-item>
				<el-form-item :label="t('common.status')">
					<el-radio-group v-model="form.status">
						<el-radio :value="0">{{ t('demo.statusNormal') }}</el-radio>
						<el-radio :value="1">{{ t('demo.statusDisabled') }}</el-radio>
					</el-radio-group>
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dialog.visible = false">{{ t('common.cancel') }}</el-button>
				<el-button type="primary" :loading="saving" @click="onSave">{{ t('common.save') }}</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
	defineOptions({ name: 'DemoTreeTablePage' })

import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import BaActionButtons from '@/components/BaActionButtons.vue'
import BaEmpty from '@/components/BaEmpty.vue'
import { useMenuStore } from '@/stores/menu'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const menuStore = useMenuStore()
const userStore = useUserStore()

/* ══════════ ①⚠ 示例数据源（骨架自洽用，抄页时整块替换）══════════
 * 树是**一次全量加载**（不分页）——这是前端递归过滤的前提；
 * 若后端只给平铺列表，先在前端按 pid 建树（tree-config rowField 需 children 字段）。 */
interface DemoTreeNode {
	id: string
	pid: string
	name: string
	code: string | null
	sort: number
	status: number
	remark: string | null
	children?: DemoTreeNode[]
}

async function getDemoTree(): Promise<DemoTreeNode[]> {
	return []
}

const loading = ref(false)
const saving = ref(false)
const rows = ref<DemoTreeNode[]>([])
const selected = ref<DemoTreeNode | null>(null)

/* ── 前端递归过滤（A1）：命中自身保留**整棵子树**；仅子命中时收窄为命中的子树 ── */
const filterKeyword = ref('')

function filterTree(nodes: DemoTreeNode[], keyword: string): DemoTreeNode[] {
	const out: DemoTreeNode[] = []
	for (const n of nodes) {
		const children = filterTree(n.children ?? [], keyword)
		const selfOk =
			!keyword ||
			(n.name ?? '').toLowerCase().includes(keyword) ||
			(n.code ?? '').toLowerCase().includes(keyword)
		if (selfOk || children.length > 0) {
			// selfOk 时原样保子树（命中父节点＝用户要看它下面的全貌，不做二次裁剪）
			out.push({ ...n, children: selfOk ? n.children : children })
		}
	}
	return out
}

const filteredRows = computed(() => filterTree(rows.value, filterKeyword.value.trim().toLowerCase()))

const columns = computed(() => [
	// B1 名称列 treeNode + tooltip（树列必须标 treeNode: true）
	{ field: 'name', title: t('demo.colName'), minWidth: 200, treeNode: true, showOverflow: 'tooltip' as const },
	{ field: 'code', title: t('demo.colCode'), minWidth: 120, showOverflow: 'tooltip' as const },
	{ field: 'sort', title: t('demo.colSort'), width: 80 },
	{ field: 'remark', title: t('common.remark'), minWidth: 160, showOverflow: 'tooltip' as const },
	// B8 状态列走插槽而非 formatter（formatter 返回的串在 vxe v4 按纯文本渲染，标签必须用插槽）
	{ field: 'status', title: t('common.status'), width: 100, slots: { default: 'cell_status' } } as object,
	// B7 操作列右 sticky
	{ title: t('common.operations'), minWidth: 180, fixed: 'right' as const, slots: { default: 'row_ops' } }
])

async function fetchData(): Promise<void> {
	loading.value = true
	try {
		// B4 loading 遮罩由 :loading 承载
		rows.value = await getDemoTree()
	} finally {
		loading.value = false
	}
}

/** 行点击 → 选中反馈条（同时作为「新增子节点」的默认父级） */
function onRowClick({ row }: { row: DemoTreeNode }): void {
	selected.value = row
}

/* ── 权限：与 v-perm 同口径（超管直通）；收纳项权限走 actions[].hidden ── */
function can(key: string): boolean {
	return userStore.user?.accountType === 999 || menuStore.permissions.includes(key)
}

/* ── C1/C2 危险确认与 per-row 防重 ───────────────────────── */
const pendingId = ref<string | null>(null)

function rowBusy(row: DemoTreeNode): boolean {
	return pendingId.value === row.id
}

/** B7 前 2 直出（新增子节点 / 编辑）、第 3 项起收纳（删除） */
function rowActions(row: DemoTreeNode): { label: string; danger?: boolean; hidden?: boolean; disabled?: boolean }[] {
	return [
		{ label: t('demo.btnAddChild'), hidden: !can('demo/add') },
		{ label: t('common.edit'), hidden: !can('demo/update'), disabled: row.status === 1 },
		{ label: t('common.delete'), danger: true, hidden: !can('demo/delete'), disabled: row.status === 1 || rowBusy(row) }
	]
}

function onRowAction(row: DemoTreeNode, index: number): void {
	if (index === 0) {
		openAdd(row)
	} else if (index === 1) {
		openEdit(row)
	} else if (index === 2) {
		void onDelete(row)
	}
}

async function onDelete(row: DemoTreeNode): Promise<void> {
	if (rowBusy(row)) {
		return
	}
	try {
		await ElMessageBox.confirm(t('demo.msgDeleteConfirm', { name: row.name }), t('demo.msgDeleteTitle'), {
			type: 'warning'
		})
	} catch {
		return
	}
	pendingId.value = row.id
	try {
		// ⚠ 抄页替换：await demoApi.deleteDemo(row.id)
		ElMessage.success(t('demo.msgDeleted'))
		if (selected.value?.id === row.id) {
			selected.value = null
		}
		void fetchData()
	} finally {
		pendingId.value = null
	}
}

/* ── 新增/编辑：父级语义（pid=0 顶级；从行内新增时 pid=父节点 id）────────── */
const dialog = reactive({
	visible: false,
	mode: 'add' as 'add' | 'edit',
	id: '' as string,
	pid: '0' as string,
	pidLabel: ''
})
const formRef = ref<FormInstance>()
const form = reactive({ name: '', code: '', sort: 0, status: 0, remark: '' })
const rules = computed<FormRules>(() => ({
	name: [{ required: true, message: t('demo.ruleNameRequired'), trigger: 'blur' }]
}))

/** 父级 id → 名称：树中找不到（被过滤/越权范围外）回落 #id，不静默空 */
function findNodeName(id: string, nodes: DemoTreeNode[] = rows.value): string | null {
	for (const n of nodes) {
		if (String(n.id) === String(id)) {
			return n.name
		}
		const hit = findNodeName(id, n.children ?? [])
		if (hit !== null) {
			return hit
		}
	}
	return null
}

function openAdd(parent: DemoTreeNode | null): void {
	dialog.mode = 'add'
	dialog.id = ''
	dialog.pid = parent ? parent.id : '0'
	dialog.pidLabel = parent ? parent.name : t('demo.topLevel')
	dialog.visible = true
	Object.assign(form, { name: '', code: '', sort: 0, status: 0, remark: '' })
}

function openEdit(row: DemoTreeNode): void {
	dialog.mode = 'edit'
	dialog.id = row.id
	dialog.pid = row.pid
	dialog.pidLabel = String(row.pid) === '0' ? t('demo.topLevel') : findNodeName(row.pid) ?? `#${row.pid}`
	dialog.visible = true
	Object.assign(form, {
		name: row.name ?? '',
		code: row.code ?? '',
		sort: row.sort,
		status: row.status,
		remark: row.remark ?? ''
	})
}

async function onSave(): Promise<void> {
	await formRef.value?.validate()
	saving.value = true
	try {
		if (dialog.mode === 'add') {
			// ⚠ 抄页替换：await demoApi.addDemo({ pid: dialog.pid, name: form.name, code: form.code || undefined, sort: form.sort, status: form.status, remark: form.remark || undefined })
		} else {
			// ⚠ 抄页替换：编辑须**回传 pid**（增量更新口径；停用节点仍要能保存，勿默认 pid=0）
		}
		ElMessage.success(t('demo.msgSaved'))
		dialog.visible = false
		void fetchData()
	} finally {
		saving.value = false
	}
}

onMounted(() => {
	void fetchData()
})
</script>

<style scoped>
.table-hint {
	font-size: 12px;
	color: var(--ba-text-tertiary);
	margin: 0 0 10px;
}
.search-row {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 10px;
}
.search-input {
	max-width: 280px;
}
/* 选中反馈条（品牌软色胶囊；参照 sysDict currentType / sysOrg org-selected 写法） */
.tree-selected {
	display: inline-block;
	font-size: 12px;
	line-height: 1.5;
	color: var(--ba-brand);
	background: var(--ba-brand-soft);
	border-radius: 10px;
	padding: 2px 10px;
	margin: 0 0 10px;
}
</style>