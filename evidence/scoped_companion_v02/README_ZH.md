# 实证补充材料与复现入口（公开派生版 V02）

[英文说明](SCOPED_EVIDENCE_COMPANION_EN.md) 保留 Wine 分层证据与 ValueEval 原件预算研究的结论；[证据索引](EVIDENCE_REGISTER_V02.json) 绑定已完成的软件搬迁验收。[来源与原有声明](SOURCES_AND_NOTICES.md) 和 [来源索引](SOURCE_INDEX_V01.json) 说明原始对象、URL、摘要及既有 notice。

## 原有搬迁验收与当前公开分发

| 包 | 内容与运行入口 | 已保留的验收证据 |
|---|---|---|
| [Wine ZIP](packages/wine_layer_calibration_v01.zip) | 25 文件；Python 3.10+ 标准库（含 sqlite3）。解压后运行 `python -I -X utf8 -B run.py --output "../new wine output"`。输出目录须全新、在包外，父目录须存在。 | [独立 QA](evidence/iteration305/PACKAGE_ACCEPTANCE_V01.json)、[实际执行回执](evidence/iteration305/EXECUTION_V01.json)、[搬迁结果](evidence/iteration305/relocated_output/RESULT.json) |
| [ValueEval 初始化 ZIP](packages/valueeval_bootstrap_v01.zip) | 新 16 文件分发版：12 个原件及初始化脚本/说明。按[来源取得与离线还原](SOURCE_RECOVERY.md)准备两文件，再以原 `hydrate.py --source-directory <精确源目录> --output <包外新目录>` 组装原 14 文件。 | [原完整包科学验收](evidence/iteration304/PACKAGE_ACCEPTANCE_V01.json)、[本地导入组装验收](evidence/bootstrap/BOOTSTRAP_ACCEPTANCE_V01.json)；来源还原和组装没有重跑科学。 |

ValueEval 的外部提取器 SHA-256 为 `640b9a93fa31fc093860c635cd410a3e30f7d1e6166cb1130993fb1985f474ff`，343,552 字节；安装及 DLL 依赖不在包内。没有验证其他平台或其他提取器，不能按任意机器开箱使用理解。Wine 只声明标准库依赖和这次 Windows 本地搬迁通过，也没有跨操作系统实测。

两项验收均从原 ZIP 解压到含空格的新目录，在无关工作目录发起单次回放。Wine 候选与 SQL 基线各一次独立进程；旧参考只在两者终态后参与比较。ValueEval 仅回放一次，七原件、五证书、五次拒读和非计时科学字段保持一致。旧工程在操作系统中仍可访问；相对路径绑定与代码审查不等于操作系统隔离或跨机器独立复现。

## 可支持的范围

Wine 包含三份真实归档、两项构造拼接、一个重复引用控制。v07 没有 CSV 或作者摘要。候选和同信息 SQL 基线的 30 个标签一致；历史执行层全部未定。搬迁协议有新摘要，30 份候选证书的 `snapshot_digest`、`scope_digest`、`input_digest`、`certificate_digest` 按公式重新绑定，不能说证书逐字相同；其余候选报告内容按精确对照保持一致。没有重新训练、重新密码验签或完整消费字节认证。

ValueEval 仍是旧 29 篇开发集里后验选择的五个已知正例。固定基线已达到所声明七对象依赖模型的预算下界。两项搬迁属于软件交付验收，不增加科学样本、不建立准确率或同信息强基线之上的方法优势，也未补齐自然应用的完整世界模型。

## 路径、历史与来源

新入口正文链接全部使用相对位置，可连同本目录搬迁；[MANIFEST](MANIFEST.json) 绑定成员摘要，不是签名。Wine ZIP 逐字复制原包。公开 ValueEval 改为初始化 ZIP，原完整 ZIP 留在私有归档；原 14 文件科学合同不变，但公开传输内容不同。[派生映射](PUBLIC_EDITION_MAP.json) 和新 manifest 绑定本版，不能沿用旧 manifest 声称全部字节未变。历史回执、原报告、来源 JSON 和 ZIP 内保留的报告可能含旧绝对路径及公开账号/运行身份，是惰性来源文本，**本材料没有匿名化**。不要把旧路径当运行输入或当前可访问依赖。

`evidence/` 保存本说明所用的 QA、执行、结果和有限历史支撑；没有声称复制了每份祖先回执的全部依赖闭包。原报告内部历史链接按原字节保留，部分指向旧工作区；可搬迁链接检查限本入口、英文说明和来源说明。两项原研究见 [Wine 302](evidence/history/RESEARCH_ITERATION_302_ZH.md) 与 [ValueEval 303](evidence/history/RESEARCH_ITERATION_303_ZH.md)。[理论源稿 V08](evidence/theory/paper.tex) 仅作为既有论述的版本参照，本入口不是其编译依赖包。

原作者 PDF、代码与数据保留各自来源和既有 notice；本地副本不代表整体许可或权属确认。标签来自明确合同下的机器推导，不是真人 gold；这里没有填写作者批准、私人作者表或新增人工审读前置。本目录是供仓库发布的派生版本，实际发布以对应提交与交付回执为准。

## 来源取得、离线派生与当前边界

[五篇 PDF 署名、许可与两公共来源说明](VALUEEVAL_PUBLIC_NOTICE_V02.md) 保留先前直接 GET 的观察：archive JSON 匹配，organizer HTML 的唯一 CSS 十位缓存参数有六字节变化，直接下载不能恢复冻结版本。[后续离线还原说明](SOURCE_RECOVERY.md) 明确披露这一参数的回填；只有全文件长度与旧 SHA 完全匹配才可交给未改的 hydrate。取得响应、离线派生、组装分开留据，不把派生内容称作服务器实际返回的历史响应，也不认证历史执行；没有执行集成联网还原脚本。未来来源其他变化会失败。旧 notice 与 bootstrap 内的直接下载失败说明仍是该先前步骤的准确记录。下载、还原和组装属于科学预算外准备，不会把两公共原件变成免费输入。
