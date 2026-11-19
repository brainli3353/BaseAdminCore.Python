/** 系统枚举 API(批 Z 6.9,契约 /api/sysEnum 三端点)。全部只读(编译期枚举元数据内省)。 */
import service from '../request'

/* ── 类型 ─────────────────────────────── */
/** 枚举值条目 */
export interface EnumEntity {
	/** 成员名(如 Public) */
	name: string
	/** 描述([Description] 特性,无则成员名) */
	describe: string
	/** 数值(底层 int) */
	value: number
}

/** 枚举类型输出(含值集合) */
export interface EnumTypeOutput {
	/** 类型描述([Description] 特性,无则类型名) */
	typeDescribe: string
	/** 类型名(如 NoticeStatusEnum) */
	typeName: string
	/** 值集合 */
	enumEntities: EnumEntity[]
}

/* ── 端点 ─────────────────────────────── */
/** GET /api/sysEnum/typeList → 全部枚举类型(名称排序,含值集合) */
export function getEnumTypeList() {
	return service.get('/api/sysEnum/typeList') as Promise<EnumTypeOutput[]>
}

/** GET /api/sysEnum/data?enumName= → 单枚举值集合 */
export function getEnumData(enumName: string) {
	return service.get('/api/sysEnum/data', { params: { enumName } }) as Promise<EnumEntity[]>
}

/** GET /api/sysEnum/dataByField?entityName=&fieldName= → 实体字段枚举值集合 */
export function getEnumDataByField(entityName: string, fieldName: string) {
	return service.get('/api/sysEnum/dataByField', {
		params: { entityName, fieldName }
	}) as Promise<EnumEntity[]>
}
