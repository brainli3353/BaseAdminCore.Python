/** 时间展示统一口径(批 UX·F0 公共件):全站时间列一律 `YYYY-MM-DD HH:mm:ss`(审单 B2)。
 * 零依赖、不引 moment/dayjs(web/package.json 无此依赖)——只用原生 Date;
 * 空值(null/undefined/空串)回 `-`(不显示空白/NaN);解析失败原样返回(不吞原始串、便于排查)。
 * 用法:`import { formatDateTime } from '@/utils/format'` → `formatDateTime(row.createTime)`。 */
export function formatDateTime(v?: string | null): string {
	if (v === undefined || v === null || v === '') {
		return '-'
	}
	const d = new Date(v)
	if (Number.isNaN(d.getTime())) {
		return v
	}
	const pad = (n: number): string => String(n).padStart(2, '0')
	return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}