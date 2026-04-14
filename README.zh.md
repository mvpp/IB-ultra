# IB-ultra

[English](README.md) | **中文**

**版本：** 2026年4月  
**兼容平台：** Claude Code / Cowork（Anthropic）

---

## 这个仓库是什么

`IB-ultra` 不是一个单独的 prompt，也不是一个单独的 skill。

它是一套模块化投研工作流，用来完成：

1. Phase 1：建立真实三表经营模型
2. Phase 2：建立估值包
3. Phase 3：建立机构风格投资备忘录

整个流程是“文件驱动”的。每个 phase 都会把产物写到磁盘，下一个 phase 再读取这些产物。

所以它更适合：

- 需要重复执行的流程
- 需要断点续跑的流程
- 希望模型、估值、memo 三者前后一致的流程

它不适合：

- 一次对话就想快速糊一个粗模
- 没有底层模型和估值，直接跳到一篇看起来很完整的 memo
- 把所有行业都当成普通 DCF 公司处理

---

## 给技术小白的一分钟心智模型

如果你第一次接触这套仓库，可以这样理解：

- `3-statements-ultra-sec` 回答的是：“历史发生了什么？经营模型长什么样？”
- `valuation-ultra` 或某个 phase 2 专用扩展包回答的是：“这家公司值多少钱？”
- `investment-memo-ultra` 回答的是：“投资逻辑是什么？市场隐含了什么？后面该盯什么？”
- `investment-banking-ultra` 回答的是：“当前缺哪个 phase？下一步该调用哪个 skill？”

所以这套流程不是：

- “写一个超长 prompt，让模型一次性把所有事情都做完”

而是：

1. 先建模
2. 再估值
3. 再写 memo
4. 让各 phase 通过磁盘上的 artifacts 自动交接

---

## 这个仓库里有哪些 Skill

### 核心工作流

- `3-statements-ultra-sec.skill`
  Phase 1 经营模型，针对美股优先走 SEC + NotebookLM
- `valuation-ultra.skill`
  默认的 Phase 2 估值引擎，适用于标准经营型公司
- `investment-memo-ultra.skill`
  Phase 3 memo / monitoring / decision package
- `investment-banking-ultra.skill`
  Orchestrator，负责检查当前目录并决定下一个 phase

### Phase 2 行业扩展包

- `valuation-financials.skill`
  银行、保险、账面价值驱动型金融公司
- `valuation-reit-property.skill`
  REIT、地产平台、稳定化不动产
- `valuation-regulated-assets.skill`
  公用事业和受监管基础设施
- `valuation-asset-nav.skill`
  储量 / 资源资产净值驱动型公司
- `valuation-biotech-rnpv.skill`
  临床阶段 biotech 和 pipeline 主导 pharma
- `valuation-sotp.skill`
  conglomerate、holdco、mixed-model 公司

---

## 第一次上手的配置清单

如果你是在新机器上第一次配置，按这个顺序做：

1. 在 `~/Programs/venv` 下创建独立 Python 环境
2. 安装依赖
3. 在 `~/Programs/.env` 里写入 SEC EDGAR 邮箱
4. 在同一个环境里执行一次 `notebooklm login`
5. 把 `.skill` 文件安装到 Cowork / Claude Code
6. 跑一遍 smoke-check，确认脚本都能调用
7. 每家公司放在一个单独、干净的目录里运行

这七步完成后，这套 repo 就具备本地可运行条件。

---

## 环境配置

请使用独立环境，不要碰系统 Python。

```bash
python3 -m venv ~/Programs/venv
source ~/Programs/venv/bin/activate

pip install openpyxl yfinance pandas python-dotenv sec-edgar-downloader
pip install "notebooklm-py[browser]"
python -m playwright install chromium
pip install numpy
```

建议 Python 3.9+。

### SEC EDGAR 的 `.env`

创建 `~/Programs/.env`：

```dotenv
SEC_EDGAR_EMAIL=your-email@example.com
```

SEC bootstrap 脚本会读取这个值来下载 filings。

### NotebookLM 登录

执行一次：

```bash
source ~/Programs/venv/bin/activate
notebooklm login
notebooklm status --paths
```

预期认证文件：

```text
~/.notebooklm/storage_state.json
```

完成后，CLI 和 Python client 都会复用这份登录态。

---

## 安装方式

### 安装到 Cowork / Claude Code

安装以下 `.skill` 文件：

1. `3-statements-ultra-sec.skill`
2. `valuation-ultra.skill`
3. `valuation-financials.skill`
4. `valuation-reit-property.skill`
5. `valuation-regulated-assets.skill`
6. `valuation-asset-nav.skill`
7. `valuation-biotech-rnpv.skill`
8. `valuation-sotp.skill`
9. `investment-memo-ultra.skill`
10. `investment-banking-ultra.skill`

### 手动解压示例

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

如果你只想要最稳妥的默认入口，还是这句：

```text
Use investment-banking-ultra and let it determine the next phase.
```

---

## 第一次实跑建议

第一次跑真实公司时，建议这样做：

1. 先新建一个干净目录，比如 `~/Programs/company-work/COHR`
2. 在 Claude Code / Cowork 里打开这个目录
3. 先说这句：

```text
Use investment-banking-ultra to start an end-to-end analysis for COHR.
```

4. 让 orchestrator 告诉你现在缺的是 phase 1、phase 2，还是 phase 3
5. 按它建议的下一步继续

这是最不容易跳过关键 artifacts 的使用方式。

---

## 各 Phase 是怎么工作的

### Phase 1：经营模型

Skill：

- `3-statements-ultra-sec`

它负责：

- 对美股 / SEC 公司下载 filings
- 把 filings 放进 NotebookLM
- 抽取历史财务和经营驱动
- 构建 `Raw_Info`、`Assumptions`、`IS`、`BS`、`CF`、`Returns`、`Summary`、`Cross_Check`

标准输出：

- 一个 Excel workbook，包含
  `Summary`、`Assumptions`、`IS`、`BS`、`CF`、`Returns`、`Cross_Check`、`Raw_Info`、`_Registry`、`_State`
- `_model_log.md`
- `_pending_links.json`

现在 phase 1 是否完成，不再只看 workbook 有没有 tab，还会检查 sidecar 和 `_State` checkpoint。

### Phase 2：估值

默认 skill：

- `valuation-ultra`

典型输出：

- `valuation_prep.json`
- `capital_cost.json`
- `dcf_output.json`
- `comps_output.json`
- `reverse_dcf.json`
- `football_field.json`
- `valuation_qc.json`
- `valuation_summary.json`

什么时候切到行业扩展包：

- 银行 / 保险：`valuation-financials`
- REIT / 地产：`valuation-reit-property`
- 公用事业 / 受监管资产：`valuation-regulated-assets`
- 储量 NAV 公司：`valuation-asset-nav`
- biotech / pipeline：`valuation-biotech-rnpv`
- conglomerate / holdco：`valuation-sotp`

Phase 2 是 script-first。重计算部分应该由仓库里的 Python 脚本完成。

### Phase 3：Memo

Skill：

- `investment-memo-ultra`

它负责：

- 读取已完成的 phase 1 / phase 2 artifacts
- 生成标准化 memo input pack
- 计算 quality overlay、variant view、decision framework、monitoring dashboard
- 输出 memo draft 并跑 memo QC

典型输出：

- `memo_input_pack.json`
- `quality_overlay.json`
- `variant_view_frame.json`
- `decision_framework.json`
- `monitoring_dashboard.json`
- `Investment_Memo.md`
- `memo_qc.json`

### Orchestrator

Skill：

- `investment-banking-ultra`

它负责：

- 扫描当前目录
- 判断 phase 1 / 2 / 3 哪个缺失
- 告诉你下一步该用哪个 skill
- 在 phase 1 和 phase 2 就绪后，一条命令跑完 deterministic phase 3 bridge

关键脚本：

- `src/investment-banking-ultra/scripts/workflow_state.py`
- `src/investment-banking-ultra/scripts/run_phase3_bundle.py`

---

## Artifact Handoff

这套流程的标准交接链路是：

1. Phase 1 写 workbook 和 sidecars
2. Phase 2 写 valuation artifact set
3. bridge 脚本把这些文件标准化成 memo-ready pack
4. Phase 3 再写 memo bundle

整个仓库的核心设计就是：通过磁盘上的 artifacts 交接，而不是依赖长对话记忆。

---

## Smoke Check

配置完成后跑一遍：

```bash
source ~/Programs/venv/bin/activate
python src/3-statements-ultra-sec/scripts/sec_nlm_bootstrap.py --help
python src/3-statements-ultra-sec/scripts/nlm_extract_company_pack.py --help
python src/valuation-ultra/scripts/dcf_valuation.py --help
python src/valuation-ultra/scripts/comps_valuation.py --help
python src/valuation-financials/scripts/financials_prep.py --help
python src/valuation-reit-property/scripts/property_bridge.py --help
python src/valuation-regulated-assets/scripts/regulatory_bridge.py --help
python src/valuation-asset-nav/scripts/reserve_model.py --help
python src/valuation-biotech-rnpv/scripts/pipeline_registry.py --help
python src/valuation-sotp/scripts/segment_normalizer.py --help
python src/investment-banking-ultra/scripts/workflow_state.py --help
python src/investment-banking-ultra/scripts/run_phase3_bundle.py --help
python src/investment-memo-ultra/scripts/build_memo_pack_from_artifacts.py --help
```

这些命令能跑，就说明你的机器配置基本正确。

---

## Upstream 来源

这是一个 fork + extension 项目。

- Phase 1 fork 自 [`willpowerju-lgtm/3-statement-ultra-for-finance`](https://github.com/willpowerju-lgtm/3-statement-ultra-for-finance)
- Phase 3 的 memo 结构和风格来源于 [`star23/Day1Global-Skills`](https://github.com/star23/Day1Global-Skills)，尤其是 `tech-earnings-deepdive` 和 `us-value-investing`
- 各个 phase 2 行业扩展包、artifact bridge 和 `investment-banking-ultra` orchestrator 是本仓库新增的原生模块

---

## 当前适用范围

最适合：

- 机构风格建模 / 估值 / memo 一体化流程
- 需要重复 phase handoff 的工作方式
- 希望模型、估值、memo 彼此对齐的场景

不适合：

- 20 分钟快速粗模
- 跳过 phase 直接出一篇“看起来完整”的 memo
- 把所有行业都硬套成普通 DCF 公司

---

## 许可证

供个人和研究使用，不提供任何保证。任何财务模型或估值输出在用于真实投资决策前，都应独立核实。
