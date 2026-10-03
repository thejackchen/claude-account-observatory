# 究竟发送什么

参与者在网页看到拟提交的完整 JSON；结果严格遵循对应 [JSON Schema](../study-schema.json)，拒收额外字段。字段可未知，不由 LLM 补猜事实。

| 类别 | 字段 |
| --- | --- |
| 格式与来源 | `schema_version`, `provider`, `source`, `provenance.protocol_version`, `provenance.prompt_version`, `provenance.extractor_version`, `provenance.skill_version` |
| 观察窗与状态 | `anchor_month`, `window_days`, `window_complete`, `status`, `notice_category`, `appeal` |
| 地区与网络 | `physical_region`, `exit_region`, `network_kind` |
| 账号与付款 | `account_origin`, `plan`, `payment`, `gift_card` |
| 接入与使用 | `credential_use`, `client`, `client_integrity`, `automation`, `prior_warning` |
| 招募和重复参与声明 | `recruitment`, `other_accounts_in_study` |
| 留存日志指标 | `metrics.responses_bucket`, `peak_daily_bucket`, `active_days_bucket`, `overnight_days_bucket`, `error_events_bucket`, `cli_version`, `log_coverage`, `gateway_claude_activity` |
| 本人授权 | `consent_aggregate` |

`anchor_month` 仅月份，不含首次受限的具体日期。地区仅粗区域，没有 IP/ASN/代理名称。指标为区间、已知 CLI 版本或 `unknown`，不含消息标识、聊天文本、项目名称或文件路径。

请求管理字段与研究结果分开：随机 `record_id`、管理 `access_key` 和试点 `invite_code` 用于提交管理；邀请码和管理密钥不进入研究 JSON，管理密钥仅保存验证摘要。研究表另保留提交/更新时间，单行不公开。公共托管仍可能处理访问 IP 等技术元数据。

逐条个人结果不推到 GitHub，也不在公开 Issues 互相比较。社区借鉴通过经过复核的群体汇总及公开方法改进实现。
