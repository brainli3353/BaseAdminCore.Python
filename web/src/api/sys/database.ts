/** 数据库管理 API(契约 /api/sysDatabase 三端点:表清单/列结构/索引)。全部只读。 */
import service from '../request'

/* ── 表清单(非分页,返回数组) ─────────────────────────────── */
export interface DbTableOutput {
	tableName: string
	comment: string | null
	/** 行数估算(统计信息/系统表口径,非精确 COUNT) */
	rowEstimate: number
	/** 已格式化大小(如 "1.2 MB") */
	totalSize: string
	indexCount: number
}

/** keyword 按表名/注释模糊(留空/不传=全量)。 */
export const listDbTables = (keyword?: string | null) =>
	service.get('/api/sysDatabase/tables', { params: { keyword: keyword || null } }) as Promise<DbTableOutput[]>

/* ── 列结构 ─────────────────────────────── */
export interface DbColumnOutput {
	columnName: string
	dataType: string
	isNullable: boolean
	maxLength: number | null
	isPrimaryKey: boolean
	comment: string | null
	/** 序位(从 1 起) */
	ordinalPosition: number
}

export const listDbColumns = (table: string) =>
	service.get('/api/sysDatabase/columns', { params: { table } }) as Promise<DbColumnOutput[]>

/* ── 索引 ─────────────────────────────── */
export interface DbIndexOutput {
	indexName: string
	/** 建索引原始语句/定义 */
	definition: string | null
	isUnique: boolean
	isPrimary: boolean
}

export const listDbIndexes = (table: string) =>
	service.get('/api/sysDatabase/indexes', { params: { table } }) as Promise<DbIndexOutput[]>