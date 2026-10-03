# Claude 账号受限观察站

用可检查、可修改的方法，共同研究 Claude 账号受限经历中的关联。

**原始记录留在本机；开源 Skill、提示词、提取工具、结果格式和研究方法。** GitHub 用来讨论与改进方法，参与者本人确认的脱敏结果提交到[观察站](https://account-restriction-observatory.jackchen815.chatgpt.site)。仓库不接收真实聊天、账号资料、回执或逐行参与记录。

## 初始版本

| 发布 | Skill | 研究协议 | 提示词 | 提取器 | 结果格式 |
| --- | --- | --- | --- | --- | --- |
| `v1.0.0` | `1.0.0` | `1.0.0` | `1.0.0` | `1.0.0` | `1.1` |

版本相互独立：改 Skill 工作流记录 Skill 版本；改提示词不必改计数规则；改字段结构要更新结果格式；改指标含义必须更新方法/提取器并说明兼容性。

- [Skill 入口](SKILL.md)
- [统一脱敏提示词与说明](tools/统一提取提示词.txt)
- [Python 标准库离线提取器](tools/claude-study-extract.py)
- [严格 JSON Schema](study-schema.json)
- [冻结的研究协议](protocol-v1.0.0.txt)
- [版本清单和文件 SHA-256](versions.json)
- [版本与兼容规则](docs/versioning.md)
- [字段清单：究竟发送什么](docs/data-fields.md)

发布标签对应一个固定 Git 提交；`versions.json` 固定对应文件的 SHA-256。发布版发生变更时创建新版本，不替换原标签/清单/文件。`main` 是开发分支，参与研究应使用明确的发布版。

## 使用 Skill

本仓库根目录就是一个自包含的 `claude-account-observatory` Skill。下载固定发布版，把整个目录交给支持本机工具执行的编码助手，或按该助手的说明放入它的技能目录。保留 `tools/` 和参考文件，不要只复制 `SKILL.md`。普通网页聊天不能替代本机脚本执行。

例如：

```sh
git clone --branch v1.0.0 --depth 1 https://github.com/thejackchen/claude-account-observatory.git
```

对助手说：“使用 claude-account-observatory Skill，在本机生成一份脱敏研究结果，保留未知字段和版本，先给我预览，不上传原始聊天。”

Skill 阅读固定提示词后调用相同脚本，输出额外声明 `skill_version=1.0.0`，仍由本人核对与提交。没有启用 Skill 时保持 `not_used`。仓库发布 Skill 不会自动安装到任何人的电脑，也不会自动获得上传权限。

## 如何参加

可以直接在网页手动填写，不能核实的内容保留 `unknown`。也可以下载某个发布版，在本机使用 Python 3：

```sh
# 正常组：最近 14 个完整本机日，且期间未受限、有实际使用
python3 tools/claude-study-extract.py --output claude-study-result.json

# 受限/恢复组：第一次受限日前 14 个完整本机日，不包含当天
python3 tools/claude-study-extract.py --anchor YYYY-MM-DD --output claude-study-result.json

# 确实使用了本仓库 1.0.0 提示词时，显式记录参与者声明
python3 tools/claude-study-extract.py --prompt-version 1.0.0 --output claude-study-result.json
```

脚本不安装依赖、不联网、不读取设置/认证/凭据文件。只读指定项目 JSONL 元数据；原始聊天内容不会进入结果。多账号日志需要本人分离，无法确认不能标为单账号完整窗。

结果先在本机生成，包含 `provenance`，授权默认为 `false`。在网页导入后本人核对、补充事实、查看拟发送的完整 JSON，再主动授权提交。保存结果和独立管理回执，之后用回执更新/撤回；不要把回执推到 GitHub。

使用提示词只是调用固定工具的一种方式。直接运行脚本未使用提示词时，`prompt_version=not_used`；手动填写未使用脚本时，`extractor_version=not_used`。无法确认或未注册改写版保持 `unknown`。

**版本标识是来源声明，文件哈希是下载一致性校验；二者不能证明事实真伪或用户确实执行了该工具。**

## 如何共同建设

任何人都可以 Fork、提出 Issue 或提交 PR。欢迎改进字段解释、减少隐私泄露、修复统计边界、完善合成样例与测试、翻译提示词，或对研究方法提出异议。

阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。先讨论会改变指标含义/采集字段/公开范围的改动；小修复可以直接提 PR。只使用合成样例，不提交任何真实日志、截图、账号、邀请码或管理回执。

Fork 的实验欢迎公开，但经过字段/隐私/版本兼容审核前，不能标为本仓库未修改发布版。维护者合并后注册新版本并发布变更记录。网站目前只识别已注册版本或 `unknown`，不会自动信任任意版本字符串。

## 研究的边界

受限者与正常使用者从同一来源同时招募，观察窗与结果格式相同。恢复账号保留首次受限历史组。版本和数据来源不同要单独报告，计数规则不同不得直接混算。

自愿样本可以比较参与者中的特征关联，不能推算全国封禁率、个人处罚概率、因果处罚原因或 Anthropic 内部风控权重。我们不提供绕过限制的方案，也不让参与者为补样本故意触发处罚。

公开结果只发布经过复核的群体汇总，每个公开单元格至少 10 份，并检查互补抑制与跨表/跨版本差分。单行结果不公开；公共托管可能处理访问元数据，不承诺绝对匿名。

## 验证与许可

```sh
python3 -m unittest discover -s tests -v
```

测试只使用临时目录里的合成数据。代码、提示词和文档使用 [MIT License](LICENSE)，允许复用和改写。**这不构成公开参与者记录的授权**；参与者授权以研究提交页为准。

独立社区项目，与 Anthropic 无隶属关系。
