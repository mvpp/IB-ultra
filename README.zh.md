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

## 建议配置 — User Preference

**第一次使用前**，将以下内容粘贴进 Claude 用户偏好设置（Settings → Profile → Custom Instructions，或你的 `CLAUDE.md` 文件）。这可以防止 Context Compaction 后丢失建模状态：

```
## 3-Statements-Ultra — 断点恢复协议
当我在使用 3-statements-ultra skill 构建三表模型时，
每次发生 context compaction 后，你必须：
1. 重新读取 3-statements-ultra SKILL.md，再写任何代码
2. 打开 Excel 文件，读取 _State tab，确认精确的恢复点
3. 读取 _model_log.md，恢复上一 session 的关键输出数字
4. 读取 _pending_links.json，检查 BS→CF 的 Cash 回填是否待处理
5. 用 RAW_MAP + ASM_MAP spot-check 验证行号，再使用任何行号
6. IS/BS/CF 预测列单元格不得硬编码，每个单元格必须是字符串公式
7. 只从下一个未完成步骤继续，不重跑已完成的部分
不得依赖对话记忆来还原行号或中间计算结果。
磁盘状态（_State、_model_log.md、_pending_links.json）永远是权威来源。
```

---

## 快速开始

说出以下任意触发词，Skill 自动接管：

```
三表模型
financial model
3-statement model
建模
从零建模
build a 3-statement model for [公司名]
```

Skill 会先问你有哪些数据来源，然后引导你逐步完成 5 个 Session。

如果走完整的三阶段流程，一个实用顺序是：

```text
1. "build a 3-statement model for COHR"
2. 完成 Sessions A-E
3. "value COHR using DCF and comps"
4. 让 valuation-ultra 继续完成估值包
5. "write the investment memo for COHR"
6. 让 investment-memo-ultra 继续完成 memo pack、outline 和 QC
```

---

## 五个 Session 构建流程

| Session | 构建内容 | 做什么 | 时间 |
|---------|---------|--------|------|
| **A** | Raw_Info + Assumptions | 数据提取（NLM / Excel / Web）；颗粒度识别；假设参数设置 | 15–30 分钟 |
| **B** | IS（利润表） | 各业务线收入、中国准则 R8 插项、少数股东损益 | 15–20 分钟 |
| **C** | BS（资产负债表） | 资产负债表，货币资金暂为占位符；写入 `_pending_links.json` | 15–20 分钟 |
| **D** | CF（现金流量表） | 逐年构建现金流；R3 Others 插项；BS 货币资金回填；9 项 QC 检查 | 15–25 分钟 |
| **E** | Returns + Cross_Check + Summary | ROIC/ROE/DuPont；假设交叉验证；Summary Tab 链接 | 15–20 分钟 |

每个 Session **完全独立** — Session 之间可以关闭对话。状态保存在 Excel 的 `_State` Tab 和两个辅助文件（`_model_log.md`、`_pending_links.json`）中。

---

## 数据来源选择

| 优先级 | 来源 | 配置成本 | Token 消耗 | 说明 |
|--------|------|---------|-----------|------|
| ✅ **首选** | **SEC filings -> NotebookLM** | 需要 NotebookLM 认证 + SEC 邮箱环境变量 | 极低 | 本分叉版对美股 / SEC 披露公司默认走这条 |
| ✅ **次选** | **NotebookLM notebook**（已上传年报/财报） | 两步配置（见下方） | 极低 | 如果 filings 已经预载，这是很好的入口 |
| ✅ **第三选择** | **Excel 历史数据**（IS/BS/CF 已整理） | 无 | 低 | 非 SEC 公司或追求速度时很好用 |
| ✅ **兜底** | **Web**（Sina / Yahoo Finance） | 无 | 低 | 自动运行，始终作为交叉验证层 |
| ⚠️ **Pro 用户慎用** | **直接上传完整 PDF**（年报、招股书全文） | 无 | 🔴 极高 | 200+ 页报告快速消耗 Context |

**为什么 SEC 优先？** 这样可以先把模型锚定在原始申报文件上，再让 NotebookLM 从同一批 SEC 文件里抽取结构化财务和管理层表述，来源更统一，假设也更容易自洽和追溯。

**为什么这个分叉版仍然强调 NotebookLM？** 因为它不只是拿来读数字，更重要的是抽取经营驱动、管理层指引、资本开支计划、营运资本管理逻辑和竞争格局。在这个 fork 里，最佳做法是先把 SEC filings 送进 NotebookLM，再用这些回答去填 Raw_Info 和 Assumptions。

1. **先完成一次 NotebookLM 认证**，这样 CLI 和 Python client 都能复用浏览器会话。
2. **一次性 OAuth 认证**（约 5 分钟，只需做一次）：

```bash
pip install "notebooklm-py[browser]"
python -m playwright install chromium
notebooklm login
notebooklm status --paths
```

认证后，如果是美股 / SEC 公司，可直接这样启动：

```bash
python scripts/sec_nlm_bootstrap.py --ticker COHR
python scripts/nlm_extract_company_pack.py --notebook-id <NOTEBOOK_ID>
```

如果你的 env 文件就放在 `~/Programs/.env`，SEC bootstrap 脚本默认会从那里读取
`SEC_EDGAR_EMAIL`。

---

## 输出 Excel 文件结构

```
[1] Summary        ← 公司简介、财务亮点、催化剂、风险
[2] Assumptions    ← 所有预测驱动因子（唯一数据源）
[3] IS             ← 利润表
[4] BS             ← 资产负债表
[5] CF             ← 现金流量表（间接法）
[6] Returns        ← ROIC / ROE / ROA / DuPont 分析
[7] Cross_Check    ← 假设参数与外部来源交叉验证日志
[8] Raw_Info       ← 历史数据提取（建好后不再回读原始来源）
[_Registry]        ← 数据来源台账（Session E 末尾构建）
[_State]           ← Session 元数据（MODEL_COMPLETE 后删除）
```

---

## 核心规则（摘要）

| 规则 | 说明 |
|------|------|
| **Rule Zero** | IS/BS/CF 所有预测单元格必须是 Excel 公式字符串，不得为数字 |
| **R3 Others 插项** | CFO 中唯一允许的非现金调整插项；同时保证 BS CHECK 和 CF CHECK 均为 0 |
| **R6 Cash 最后** | BS 货币资金在 Session D 之前始终为 0 占位符，Session D 从 CF 期末现金回填 |
| **代码块行数限制** | 每个 Python 代码块最多 400 行，执行后再写下一块 |
| **单一来源** | Raw_Info 完成后，所有数据只通过 `=Raw_Info!` 公式引用，不再回读原始来源 |

---

## 常见问题

**Q：没有 NotebookLM 也能用吗？**
可以。NotebookLM 是可选的。没有的话，Skill 自动降级到 Web（Sina / Yahoo Finance）作为主要数据源。

**Q：我只有年度数据，但公司按季度披露，怎么处理？**
Skill 通过 yfinance 自动识别颗粒度。只要任何来源显示有季度数据，就使用季度模式。Phase 0 时也可以手动确认。

**Q：Session 中途可以暂停、下次再继续吗？**
可以。每个代码块执行后都会在 Excel 的 `_State` Tab 写入进度标记。每个 Session 启动时会自动找到上次完成的步骤并从下一步继续。

**Q：为什么要跑 5 个 Session，不能一次跑完吗？**
季报模式的利润表每个 Section 就有 300+ 行 Python 代码。一次性生成会触及大模型的输出上限，代码被静默截断，Excel 文件写到一半没有任何报错。5 个 Session 逐段执行完全规避了这个问题。

**Q：Session C 结束后 BS CHECK ≠ 0，是 bug 吗？**
不是，这是预期行为。货币资金在 Session D 之前是 0 占位符，Session D 从 CF 期末现金回填后 BS CHECK 才会归零。不要在 Session C 里强行平衡资产负债表。

**Q：US GAAP 公司（纽交所/纳斯达克）也支持吗？**
支持。Phase 0 中使用标准 ticker 格式（如 `"AAPL"`），Skill 会自动识别 IFRS/US GAAP 并套用对应的利润表模板。

---

## 与官方 `financial-analysis:3-statements` Skill 的对比

Claude 插件市场中有一个官方三表模型 Skill（`financial-analysis:3-statements`）。两者定位不同，质量标准差异显著。

### 官方 Skill 的优势

速度快。如果你已经有一个半填好的 Excel 模板，只需要把公式链接起来，官方 Skill 一个 Session 就能搞定，不需要任何配置。适合快速出一个粗略模型、对结构正确性要求不高的场景。

### 本 Skill 的核心差异 — 为什么这些差异对严肃工作至关重要

**1. 货币资金永不倒推。**

这是最根本的结构差异。官方 Skill 用倒推法计算货币资金：`Cash = 负债合计 + 所有者权益 − 非现金资产`。这样资产负债表表面上平衡了，但结构上是错的。用这种方式算出来的货币资金和实际现金生成能力毫无关系——它只是一个残差，只要任何其他科目稍有偏差，这个数就会把所有偏差吸收进去，严重失真。正确的做法是，货币资金必须等于现金流量表的期末现金，由完整的现金流量瀑布推导得出。本 Skill 无条件强制执行这一规则：Session C 中货币资金保留为占位符，Session D 从现金流量表回填，没有例外。

**2. 收入按业务线拆分，各自独立驱动。**

官方 Skill 将收入作为一行处理。本 Skill 为每条业务线单独构建行，配有各自的 YoY 增速假设、量价拆分结构（如适用）以及季度模型的季节性比例。单行收入假设对于粗略估算尚可接受，但用于卖方研究或 IC Memo 时完全不够，因为你需要能单独压力测试各产品线或地区的表现。

**3. 所有预测单元格均为 Excel 公式，没有例外。**

本 Skill 的 Rule Zero：IS/BS/CF 中没有任何预测单元格可以存数字。每个单元格必须是引用 Assumptions Tab 或其他单元格的字符串公式。官方 Skill 经常直接把数值写入预测单元格，这意味着一旦修改任何假设，受影响的单元格不会重新计算，因为它存的是数字不是公式。

**4. 原生支持中国会计准则。**

中国会计准则利润表在"营业总成本"和"营业利润"之间存在若干科目（其他收益、信用减值损失、资产减值损失等），IFRS 和 US GAAP 中没有对应项。本 Skill 用专门的 R8 插项行来捕捉这部分差额——即来源中的营业利润与模型推导的 EBIT 之间的残差。用通用模板忽略这些科目，会导致 A 股和港股中国准则公司的 EBIT 系统性偏差。

**5. 9 项 QC 检查必须全部通过，模型才能标记为完成。**

没有通过全部检查，模型无法写入 MODEL_COMPLETE 状态：BS CHECK = 0、CF CHECK = 0、NI CHECK ≈ 0、REV CHECK = 0、预测列硬编码扫描、NCI 连续性检查、公式完整性抽样检查、去除网格线检查、Summary Tab 零硬编码检查。官方 Skill 没有对应的质量门控。

**6. 少数股东权益始终滚动计算。**

如果公司存在少数股东，资产负债表上的少数股东权益必须每期复利累计：`NCI_期末 = NCI_期初 + 归属少数股东净利润 − 少数股东分红`。将预测期 NCI 设为零或直接用最后一期历史值延续是常见错误，会同时影响资产负债表和利润表中的归属计算。本 Skill 强制执行滚动公式，并在 QC-5 中验证。

### 对比表

| | `3-statements-ultra`（本 Skill） | `financial-analysis:3-statements`（官方） |
|---|---|---|
| 货币资金来源 | `= CF 期末现金`（始终如此） | 资产负债表残差倒推 |
| 收入结构 | 按业务线拆分，各自独立驱动 | 单行 |
| 预测单元格 | 100% Excel 公式 | 公式与硬编码混用 |
| 中国准则支持 | 原生（R8 插项、营业利润对账） | 通用模板 |
| QC 验证 | 9 项强制检查 | 无 |
| NCI 滚动计算 | 强制执行 | 不保证 |
| 季度颗粒度 | 完整支持（每年 35 列） | 仅年度 |
| 配置成本 | 5 个 Session，约 1–2 小时 | 单 Session |
| 适用场景 | IPO / 卖方研究质量模型 | 快速填充模板 |

### 如何选择

如果你需要在 20 分钟内出一个粗略模型，数字不需要经得起推敲，用官方 Skill。

如果模型将用于 IC Memo、研究报告、投资者材料，或者任何会被人仔细检查是否平衡、假设是否正确传导的场景，用本 Skill。

---

## 许可证

本 Skill 供个人和研究使用，不提供任何保证。由本 Skill 生成的财务模型在用于投资决策前，应经过独立核实。
