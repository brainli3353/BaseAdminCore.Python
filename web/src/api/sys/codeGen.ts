/** 代码生成 API(批 AI 6.1,契约 /api/sysCodeGen 两端点:表清单 / 生成预览)。**只返回文本,不写盘**。
 *
 * WHY 表清单类型复用 database 模块:后端 GetTableListAsync 直接复用 SysDatabaseService 的只读表清单,
 * 返回同一份 DbTableOutput(字段口径完全一致)——前端再声明一个影子接口只会两处漂移。
 * 生成口径:三段 C# 源码文本(entityCode/dtoCode/serviceCode)+ warnings(如未知列类型已回落 string)。 */
import service from '../request'
import type { DbTableOutput } from './database'

/** 表清单条目(与 /api/sysDatabase/tables 同型,后端同一份 DTO) */
export type { DbTableOutput }

/* ── 表清单(非分页,返回数组) ─────────────────────────────── */
/** keyword 按表名/注释模糊(留空/不传=全量)。权限键 sysCodeGen/tables。 */
export const listCodeGenTables = (keyword?: string | null) =>
	service.get('/api/sysCodeGen/tables', { params: { keyword: keyword || null } }) as Promise<DbTableOutput[]>

/* ── 生成预览 ─────────────────────────────── */
/** 生成输入(JSON camelCase;后四个可省——后端缺省:className=表名去 removePrefix 前缀后 PascalCase、
 * moduleName="Business"、removePrefix="sys_"、baseType="EntityBase")。 */
export interface CodeGenInput {
	/** 目标表名(必填) */
	tableName: string
	/** 类名(留空=后端按表名推导) */
	className?: string | null
	/** 模块名(留空=Business) */
	moduleName?: string | null
	/** 去前缀(留空=sys_) */
	removePrefix?: string | null
	/** 实体基类(EntityBase / EntityTenant) */
	baseType?: string | null
}

/** 生成预览输出:三段 C# 源码文本 + 提示清单(**无任何写盘副作用**) */
export interface CodeGenPreviewOutput {
	tableName: string
	/** 实际生效的类名(后端推导结果回显) */
	className: string
	/** 实体类源码 */
	entityCode: string
	/** Dto 组源码 */
	dtoCode: string
	/** 服务骨架源码 */
	serviceCode: string
	/** 生成提示(如"未知列类型已回落 string"、审计列已跳过);无提示为空数组 */
	warnings: string[]
}

/** 生成预览(只返回文本)。权限键 sysCodeGen/preview;表不存在等业务失败由全局拦截器统一弹错。 */
export const previewCodeGen = (input: CodeGenInput) =>
	service.post('/api/sysCodeGen/preview', input) as Promise<CodeGenPreviewOutput>