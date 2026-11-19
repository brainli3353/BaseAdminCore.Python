/** 接口文档 API(批 AG 6.7,契约 /api/apiDoc):消费后端反射**自建**的 OpenAPI 3.0 最小文档。只读。
 *
 * WHY 字段全可选:文档由后端 ApiDocGenerator 反射产出(纯 Dictionary 组合,不定义影子模型),
 * 字段随端点形态而定——如 `x-perm` 仅 [MenuPerm] 标注的端点才有;未标注端点无该字段 ⇒ 前端按「登录即可」容错。
 * 覆盖范围(有意裁剪):paths(路径/方法/operationId/tags/summary)、parameters、security + x-perm、
 * responses(200 + $ref)、components.schemas;不做 example / try-it-out / 请求体完整 JSON Schema。 */
import service from '../request'

/* ── 文档结构类型(OpenAPI 3.0 最小子集) ─────────────────────────────── */
/** 文档元信息(info) */
export interface OpenApiInfo {
	title?: string
	version?: string
	description?: string
}

/** schema 引用或内联类型(生成器只产出这两种形态之一) */
export interface OpenApiSchemaRef {
	/** 形如 #/components/schemas/UserOutput */
	$ref?: string
	/** 简化 JSON 类型:string / integer / boolean / number / array / object */
	type?: string
}

/** 端点参数(query 为 DTO 展平结果;body 记为 object) */
export interface OpenApiParameter {
	name?: string
	/** query | path | body */
	in?: string
	required?: boolean
	schema?: OpenApiSchemaRef
}

/** 单个响应定义(生成器只产出 200 一档) */
export interface OpenApiResponse {
	description?: string
	/** 媒体类型 → 载体 schema(键通常为 application/json) */
	content?: Record<string, { schema?: OpenApiSchemaRef }>
}

/** 单个操作(方法级);路径条目下另有 get/post/… 之外扩展键的容错由消费方处理 */
export interface OpenApiOperation {
	tags?: string[]
	/** 形如 "SysUser.Page"(后端按 tag.方法名 生成) */
	summary?: string
	operationId?: string
	parameters?: OpenApiParameter[]
	/** 鉴权方案声明;仅 [MenuPerm] 端点存在(与 x-perm 同生共死) */
	security?: Record<string, unknown>[]
	/** ★ 权限键(如 sysUser/page):仅标注 [MenuPerm] 的端点有;无此字段＝登录即可 */
	'x-perm'?: string
	/** ★ 分区(批 BE):framework(框架文档) / business(业务接口);后端按控制器程序集判定,缺失容错为 framework */
	'x-doc-zone'?: string
	responses?: Record<string, OpenApiResponse>
}

/** 路径条目:HTTP 方法名(小写 get/post/…) → 操作 */
export type OpenApiPathItem = Record<string, OpenApiOperation>

/** components.schemas 里的数据结构定义 */
export interface OpenApiSchema {
	type?: string
	/** 属性名(camelCase) → 简化类型 */
	properties?: Record<string, OpenApiSchemaRef>
}

/** OpenAPI 3.0.1 最小文档 */
export interface OpenApiDocument {
	/** 固定 "3.0.1" */
	openapi?: string
	info?: OpenApiInfo
	/** 路径 → 方法 → 操作 */
	paths?: Record<string, OpenApiPathItem>
	components?: { schemas?: Record<string, OpenApiSchema> }
}

/* ── 端点 ─────────────────────────────── */
/** GET /api/apiDoc/openapi → OpenAPI 3.0.1 文档
 * (ApiDoc:Enabled=false 时后端抛 403 业务异常,由响应拦截器统一弹错,页面不自 catch) */
export const getOpenApiDoc = () => service.get('/api/apiDoc/openapi') as Promise<OpenApiDocument>