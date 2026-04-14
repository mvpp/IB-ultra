# 3-Statements-Ultra — SEC 优先分叉版

[English](README.md) | **中文**

**版本：** 4.8 · SEC 优先分叉版
**发布日期：** 2026年4月
**兼容平台：** Claude Code / Cowork（Anthropic）

---

## 这个分叉版改了什么

这个 fork 保留了原始建模逻辑，但把美股 / SEC 披露公司的默认数据流改成：

- 先下载 SEC filings
- 再用 `notebooklm-py` 驱动 NotebookLM 抽取
- Excel 作为二级来源
- Web 只做 cross-check / fallback

这个仓库现在包含十个配套 skill：

- `3-statements-ultra-sec.skill`：先完成经营模型
- `valuation-ultra.skill`：再把经营模型转成估值输出
- `valuation-financials.skill`：银行、保险和账面价值驱动型金融公司的 phase-2 专用扩展包
- `valuation-reit-property.skill`：REIT、地产平台和稳定化资产开发商的 phase-2 专用扩展包
- `valuation-regulated-assets.skill`：受监管公用事业和受监管基础设施的 phase-2 专用扩展包
- `valuation-asset-nav.skill`：储量 / 资产净值驱动型资源公司的 phase-2 专用扩展包
- `valuation-biotech-rnpv.skill`：临床阶段 biotech 和 pipeline 主导 pharma 的 phase-2 专用扩展包
- `valuation-sotp.skill`：conglomerate、holdco 和 mixed-model 公司的 phase-2 专用扩展包
- `investment-memo-ultra.skill`：再把模型和估值结果整合成机构级投资备忘录
- `investment-banking-ultra.skill`：统一编排整个流程，并自动把估值产物桥接到 memo 阶段

推荐顺序：

1. 如果你想要一个统一的引导式流程，先用 `investment-banking-ultra`
2. 再用 `3-statements-ultra-sec` 建三表
3. 再用 `valuation-ultra` 处理标准经营型公司的估值
4. 如果是银行、保险或账面价值驱动型金融公司，就改用 `valuation-financials`
5. 如果是 REIT 或地产类公司，就改用 `valuation-reit-property`
6. 如果公司需要受监管资产、资产 NAV、biotech rNPV 或 SOTP 这些专门估值机制，就切到对应扩展包
7. 最后用 `investment-memo-ultra` 做 investment memo、监控面板和决策框架

## 这个 Skill 做什么

从零开始，在 Excel 中构建机构级**三表财务模型**（利润表、资产负债表、现金流量表）——所有预测单元格均为 Excel 公式（零硬编码），并内置 9 步质量控制验证。

输出质量目标：IPO 招股书 / 卖方研究 initiating coverage 级别。

核心特性：
- **中国准则 / IFRS / US GAAP** — 三套会计准则全部支持
- **季报 / 半年报 / 年报** 颗粒度自动识别
- **全公式预测** — IS/BS/CF 每一个预测单元格均为引用 Assumptions 的 Excel 公式，永不硬编码
- **断点续跑** — 5 个 Session 独立构建，支持随时中断、下次接着跑
- **9 项 QC 检查** — BS CHECK、CF CHECK、NI CHECK、REV CHECK、硬编码扫描、NCI 连续性、公式完整性、去除网格线、Summary 链接检查
- **数据台账** — 每个输入值和派生值均记录来源与公式链路

配套的估值 skill 会进一步生成：

- `Valuation_Prep`
- `Capital_Cost`
- `DCF`
- `Comps`
- `Scenarios`
- `Football_Field`
- `Target_Price`
- `Valuation_QC`

并且把所有硬计算尽量放到 Python 脚本里，而不是只靠 prompt 算术。

第一个行业扩展包还会生成：

- `financials_prep.json`
- `pb_roe_output.json`
- `residual_income_output.json`
- 可选 `embedded_value_output.json`
- `target_price_summary.json`
- `financials_qc.json`

第二个行业扩展包还会生成：

- `property_bridge.json`
- `nav_output.json`
- `affo_output.json`
- `target_price_summary.json`
- `reit_qc.json`

配套的投资备忘录 skill 会进一步生成：

- `Memo_Input_Pack`
- `Quality_Overlay`
- `Variant_View_Frame`
- `Decision_Framework`
- `Monitoring_Dashboard`
- `Investment_Memo.md`
- `Memo_QC`

并把质量评分、行动价位、监控阈值和 memo QC 都尽量交给本地脚本来完成。

工作流编排 skill 还会补上：

- `workflow_state.py`：扫描当前目录，判断现在处于哪一个阶段
- `run_phase3_bundle.py`：一条命令生成 memo pack、overlay、dashboard、memo 骨架和 QC

---

## 环境配置

```bash
# 推荐：使用 ~/Programs 下的独立虚拟环境，不要碰系统 Python
python3 -m venv ~/Programs/venv
source ~/Programs/venv/bin/activate

# 三表 skill 依赖
pip install openpyxl yfinance pandas python-dotenv sec-edgar-downloader

# NotebookLM 自动化
pip install "notebooklm-py[browser]"
python -m playwright install chromium

# 估值脚本建议依赖
pip install numpy
```

需要 Python 3.9+。

### SEC EDGAR 的 `.env`

如果要自动下载 SEC filings，请创建 `~/Programs/.env`：

```dotenv
SEC_EDGAR_EMAIL=your-email@example.com
```

`sec_edgar_downloader` 需要一个邮箱用于 EDGAR 标识；本分叉版默认从这个 env 文件读取。

### NotebookLM 登录

在同一个环境里执行一次：

```bash
source ~/Programs/venv/bin/activate
notebooklm login
notebooklm status --paths
```

预期认证文件路径：

```text
~/.notebooklm/storage_state.json
```

完成后，CLI 和 Python client 都可以复用这份浏览器登录状态。

### 可选 Smoke Check

```bash
source ~/Programs/venv/bin/activate
python src/3-statements-ultra-sec/scripts/sec_nlm_bootstrap.py --help
python src/3-statements-ultra-sec/scripts/nlm_extract_company_pack.py --help
python src/valuation-ultra/scripts/dcf_valuation.py --help
python src/valuation-ultra/scripts/comps_valuation.py --help
python src/valuation-financials/scripts/financials_prep.py --help
python src/valuation-financials/scripts/pb_roe_valuation.py --help
python src/valuation-financials/scripts/residual_income.py --help
python src/valuation-reit-property/scripts/property_bridge.py --help
python src/valuation-reit-property/scripts/reit_nav.py --help
python src/valuation-reit-property/scripts/affo_valuation.py --help
python src/valuation-regulated-assets/scripts/regulatory_bridge.py --help
python src/valuation-regulated-assets/scripts/rab_valuation.py --help
python src/valuation-asset-nav/scripts/reserve_model.py --help
python src/valuation-asset-nav/scripts/asset_nav.py --help
python src/valuation-biotech-rnpv/scripts/pipeline_registry.py --help
python src/valuation-biotech-rnpv/scripts/pipeline_rnpv.py --help
python src/valuation-sotp/scripts/segment_normalizer.py --help
python src/valuation-sotp/scripts/sotp_valuation.py --help
python src/investment-banking-ultra/scripts/workflow_state.py --help
python src/investment-banking-ultra/scripts/run_phase3_bundle.py --help
python src/investment-memo-ultra/scripts/memo_input_pack.py --help
python src/investment-memo-ultra/scripts/build_memo_pack_from_artifacts.py --help
python src/investment-memo-ultra/scripts/render_memo_outline.py --help
```

---

## 安装方式

### Cowork / Claude Code（.skill 文件）

1. 下载 `3-statements-ultra-sec.skill`
2. 下载 `valuation-ultra.skill`
3. 下载全部六个 phase-2 专用扩展包：`valuation-financials.skill`、`valuation-reit-property.skill`、`valuation-regulated-assets.skill`、`valuation-asset-nav.skill`、`valuation-biotech-rnpv.skill`、`valuation-sotp.skill`
4. 下载 `investment-memo-ultra.skill`
5. 下载 `investment-banking-ultra.skill`
6. Cowork 中：**Settings → Skills → Install from file** → 依次选择这些 `.skill` 文件
7. Claude Code CLI：将解压后的文件夹放到 `.claude/skills/` 目录下

### 手动安装（Claude Code）

```bash
unzip 3-statements-ultra-sec.skill -d ~/.claude/skills/3-statements-ultra-sec/
unzip valuation-ultra.skill -d ~/.claude/skills/valuation-ultra/
unzip valuation-financials.skill -d ~/.claude/skills/valuation-financials/
unzip valuation-reit-property.skill -d ~/.claude/skills/valuation-reit-property/
unzip valuation-regulated-assets.skill -d ~/.claude/skills/valuation-regulated-assets/
unzip valuation-asset-nav.skill -d ~/.claude/skills/valuation-asset-nav/
unzip valuation-biotech-rnpv.skill -d ~/.claude/skills/valuation-biotech-rnpv/
unzip valuation-sotp.skill -d ~/.claude/skills/valuation-sotp/
unzip investment-memo-ultra.skill -d ~/.claude/skills/investment-memo-ultra/
unzip investment-banking-ultra.skill -d ~/.claude/skills/investment-banking-ultra/
```

---

## 这两个 Skill 怎么配合

### 第一阶段：建模（`3-statements-ultra-sec`）

SEC 优先 skill 会：

1. 对于美股 / SEC 公司，先下载 SEC filings
2. 把这些 filings 放进专用 NotebookLM notebook
3. 把历史财务和经营驱动抽到 `Raw_Info`
4. 构建 `Assumptions`、`IS`、`BS`、`CF`、`Returns` 和 summary 输出

关键脚本：

- `src/3-statements-ultra-sec/scripts/sec_nlm_bootstrap.py`
- `src/3-statements-ultra-sec/scripts/nlm_extract_company_pack.py`

### 第二阶段：估值（`valuation-ultra`）

经营模型完成后，再进入估值 skill。

它的执行顺序是：

1. `valuation_prep.py`：把模型输出标准化成 NOPAT、UFCF、ROIC、净债务、稀释股数
2. `cost_of_capital.py`：计算 cost of equity、税后债务成本和 WACC
3. `dcf_valuation.py`、`comps_valuation.py`：输出 primary / secondary valuation
4. `reverse_dcf.py`、`football_field.py`：输出 implied expectations 和区间聚合
5. `valuation_qc.py`：在给 target price 前做硬校验

估值 skill 对硬计算采用 script-first，prompt 主要负责：

- 方法选择
- peer 选择
- 会计口径判断
- 投资叙事、风险和催化剂

如果覆盖的是金融企业，不要硬把它塞进通用 DCF 流程，而是优先使用首个行业扩展包：

- `valuation-financials`：面向银行、保险和账面价值驱动型 specialty finance
- 主要方法：`P/B` 或 `P/TBV` 对 `ROE` / `ROTCE`，以及 residual income；在披露允许时再补 embedded value

如果覆盖的是地产企业，也不要硬套通用 DCF，而是优先使用第二个行业扩展包：

- `valuation-reit-property`：面向 REIT、地产平台和稳定化资产开发商
- 主要方法：`NAV`、`AFFO` multiple、cap-rate sensitivity，以及 development / stabilized asset split

如果公司属于其他需要专门估值机制的家族，就使用对应扩展包，而不是硬把它塞进通用流程：

- `valuation-regulated-assets`：面向受监管公用事业和受监管基础设施
- `valuation-asset-nav`：面向储量 / 资产净值驱动型资源公司
- `valuation-biotech-rnpv`：面向临床阶段 biotech 和 pipeline 主导 pharma
- `valuation-sotp`：面向 conglomerate、holdco 和 mixed-model 公司

当前架构是：

- 一个核心 `valuation-ultra`，负责共享的 `DCF + comps + reverse DCF + QC`
- 六个已经实现的专用扩展包：
- `valuation-financials`
- `valuation-reit-property`
- `valuation-regulated-assets`
- `valuation-asset-nav`
- `valuation-biotech-rnpv`
- `valuation-sotp`

### 第三阶段：投资备忘录（`investment-memo-ultra`）

估值包完成后，再进入 memo skill。

它的执行顺序是：

1. `build_memo_pack_from_artifacts.py`：自动发现第一阶段 workbook 和第二阶段 JSON，先生成 memo-ready pack
2. `memo_input_pack.py`：如果你已经手头有标准化 JSON 片段，也可以继续手动拼 pack
3. `quality_overlay.py`：计算四维质量交叉评分
4. `variant_view_frame.py`：把市场隐含假设和我们承保假设并排展示
5. `decision_engine.py`：生成 action bands、action price 和 sizing ranges
6. `monitoring_dashboard.py`：把 drivers、risks、catalysts 转成监控面板
7. `render_memo_outline.py`：先生成一个带硬事实的 markdown 骨架
8. `memo_qc.py`：检查最终 memo 是否包含必需章节并和核心数字对得上

memo skill 对以下部分采用 script-first：

- 硬事实表格
- 质量评分
- action price 计算
- 监控阈值
- memo QC

prompt 主要负责：

- thesis 写作
- key forces
- 管理层与竞争格局判断
- pre-mortem 和风险排序

### 工作流编排（`investment-banking-ultra`）

如果你不想手动记住现在该跑哪个 phase，就用这个 skill。

执行顺序：

1. `workflow_state.py` 先扫描当前工作目录，识别 phase 1、phase 2、phase 3 的产物
2. 如果 phase 1 缺失，就转去 `3-statements-ultra-sec`
3. 如果 phase 1 已完成但 phase 2 缺失，就转去 `valuation-ultra`
4. 如果 phase 1 和 phase 2 都已完成，就用 `run_phase3_bundle.py` 一条命令生成确定性的 memo bundle
5. 最后再用 `investment-memo-ultra` 补 narrative 和 judgment-heavy 部分

推荐桥接命令：

```bash
source ~/Programs/venv/bin/activate
python src/investment-banking-ultra/scripts/run_phase3_bundle.py --workdir .
```

---

## 如何使用这个仓库

这个仓库现在不是“一个大而全的三表 skill”，而是一套模块化工作流：

1. `investment-banking-ultra` 先检查当前目录，判断应该从哪个 phase 开始。
2. `3-statements-ultra-sec` 负责完成 phase 1 的经营模型。
3. `valuation-ultra` 或对应的 phase 2 行业扩展包负责完成估值。
4. `investment-memo-ultra` 再把模型和估值产物整理成机构级 memo 包。

如果你想走最稳定的端到端流程，建议从 orchestrator 开始，让它决定下一步该跑哪个 skill。

---

## 给技术小白的一分钟心智模型

如果你第一次接触这套仓库，可以这样理解：

- Phase 1 回答的是：“历史发生了什么？经营模型长什么样？”
- Phase 2 回答的是：“在明确估值方法下，这家公司值多少钱？”
- Phase 3 回答的是：“投资逻辑是什么？市场隐含了什么？后续该盯什么指标？”
- Orchestrator 回答的是：“当前缺哪个 phase？下一步应该调用哪个 skill？”

所以这套流程不是：

- “写一个超长 prompt，让模型一次性把所有事都做完”

而是：

1. 先建模
2. 再估值
3. 再写 memo
4. skill 之间通过磁盘上的 artifacts 自动交接

---

## 第一次上手的配置清单

如果你是在一台新机器上第一次配置，最短路径是：

1. 在 `~/Programs/venv` 下创建独立 Python 环境
2. 安装 README 里 `环境配置` 章节列出的依赖
3. 在 `~/Programs/.env` 里写入 `SEC_EDGAR_EMAIL=...`
4. 在同一个环境里执行一次 `notebooklm login`
5. 把 `.skill` 文件安装到 Cowork / Claude Code
6. 跑一遍 smoke-check 命令，确认脚本都能调用
7. 每家公司单独放在一个干净目录里运行

这七步完成后，这套 repo 就具备了本地可运行条件。

---

## 这些 Skill 应该怎么调用

如果你不确定从哪里开始，先用 orchestrator：

```text
Use investment-banking-ultra to start an end-to-end analysis for COHR.
```

如果你想直接调用某个 phase：

- Phase 1：
  `Use 3-statements-ultra-sec to build a 3-statement model for COHR from SEC filings.`
- Phase 2 通用：
  `Use valuation-ultra to value COHR with DCF, comps, and reverse DCF.`
- Phase 2 专用扩展包：
  `Use valuation-financials for JPM.`
  `Use valuation-reit-property for PLD.`
  `Use valuation-regulated-assets for a regulated utility.`
  `Use valuation-asset-nav for an E&P company.`
  `Use valuation-biotech-rnpv for a clinical-stage biotech.`
  `Use valuation-sotp for a conglomerate.`
- Phase 3：
  `Use investment-memo-ultra to write the investment memo once phase 1 and phase 2 are complete.`

如果你只是想要最稳妥的默认入口，还是这句：

```text
Use investment-banking-ultra and let it determine the next phase.
```

---

## Phase 1 的定位

`3-statements-ultra-sec` 是经营模型引擎。

适合这些场景：

- 你要的是完整三表模型，不是快速填模板
- 美股 / SEC 公司，希望以 SEC filings 为第一来源
- 想用 NotebookLM 从同一批 filings 中抽历史财务和经营驱动
- 希望支持多 session 断点续跑

它的标准输出是：

- 一个包含 `Summary`、`Assumptions`、`IS`、`BS`、`CF`、`Returns`、`Cross_Check`、`Raw_Info`、`_Registry`、`_State` 的 Excel workbook
- `_model_log.md`
- `_pending_links.json`

现在 orchestrator 会把这些 sidecar 和 `_State` checkpoint 视为 phase 1 完成标准的一部分，而不是可有可无的附件。

---

## Phase 2 的定位

`valuation-ultra` 是默认的 phase 2 估值引擎，适用于标准经营型公司。它覆盖：

- valuation prep
- cost of capital
- DCF
- comps
- reverse DCF
- football field
- valuation QC

如果公司需要不同的估值机制，就不要硬套通用 DCF，而应切到对应扩展包：

- `valuation-financials`：银行、保险、账面价值驱动型金融公司
- `valuation-reit-property`：REIT、地产平台、稳定化不动产
- `valuation-regulated-assets`：公用事业和受监管基础设施
- `valuation-asset-nav`：储量 / 资产净值驱动型资源公司
- `valuation-biotech-rnpv`：临床阶段 biotech 和 pipeline 主导 pharma
- `valuation-sotp`：conglomerate、holdco、mixed-model 公司

Phase 2 是 script-first。计算量大的部分应该由仓库里的 Python 脚本完成，模型主要负责方法选择、peer 判断和投资解释。

---

## Phase 3 的定位

`investment-memo-ultra` 是配套 memo skill，不是 phase 1 / phase 2 的替代品。

它期望先有完整的 phase 1 和 phase 2 产物，然后生成：

- `memo_input_pack.json`
- `quality_overlay.json`
- `variant_view_frame.json`
- `decision_framework.json`
- `monitoring_dashboard.json`
- `Investment_Memo.md`
- `memo_qc.json`

memo 层同样是 script-first，像质量评分、行动区间、监控阈值和 memo QC 都尽量交给本地脚本做。

---

## Artifact Handoff

这套系统的标准交接链路是：

1. Phase 1 先生成 workbook 和 sidecars。
2. Phase 2 再生成通用估值产物，或某个行业扩展包的估值产物。
3. bridge 脚本把这些文件标准化成 memo-ready pack。
4. Phase 3 再从这个标准化 pack 生成 memo bundle。

这也是本仓库最核心的设计：skill 之间通过磁盘上的 artifacts 协作，而不是依赖对话记忆。

---

## Upstream 来源

这是一个 fork + extension 项目。

- Phase 1 fork 自 [`willpowerju-lgtm/3-statement-ultra-for-finance`](https://github.com/willpowerju-lgtm/3-statement-ultra-for-finance)，然后在这里改造成 SEC-first / NotebookLM-first 的工作流，并补上更严格的 artifact gating 和 resume 逻辑。
- Phase 3 的 memo 结构和风格来源于 [`star23/Day1Global-Skills`](https://github.com/star23/Day1Global-Skills)，尤其是 `tech-earnings-deepdive` 和 `us-value-investing`，但在这里已经被重写成以 artifact 和本地脚本为核心的 memo workflow。
- 各个 phase 2 行业扩展包、artifact bridge 和 `investment-banking-ultra` orchestrator 是这个仓库里新增的原生模块。

---

## 当前适用范围

这个仓库最适合：

- 机构风格的建模、估值、memo 一体化流程
- 需要可重复 phase handoff 的工作方式
- 希望模型、估值、memo 三者彼此对齐的场景

这个仓库不适合：

- 追求“一次对话 20 分钟出粗模”的场景
- 跳过 phase 产物，直接生成一篇看起来完整的 memo
- 把所有行业都当成普通 DCF 公司处理

---

## 许可证

本 Skill 供个人和研究使用，不提供任何保证。由本 Skill 生成的财务模型在用于投资决策前，应经过独立核实。

---

## 许可证

本 Skill 供个人和研究使用，不提供任何保证。由本 Skill 生成的财务模型在用于投资决策前，应经过独立核实。
