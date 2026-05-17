# Phase 2: 稳健性加固 Implementation Plan

**Goal:** 修复 6 个稳健性缺陷，提高 pipeline 的容错能力和数据质量

---

### Task P2-1: Logger handler 泄漏修复

**问题:** `build_logger()` 每次调用添加 handler，多次调用后日志重复输出 N 倍
**文件:** `stock_kit/tools/pipeline.py:38-56`
**修复:** 先清理 logger 现有 handler，再添加新 handler

### Task P2-2: PEG 负值映射修复

**问题:** 负 PEG（亏损公司）被映射为 10/10 分（"最划算"）
**文件:** `stock_kit/tools/ranker.py:88-90`
**修复:** PEG < 0 时返回 None，不参与排名计算

### Task P2-3: yfinance 超时保护

**问题:** `yf.Ticker(sym).info` 无 timeout，网络挂起时阻塞全流程
**文件:** `stock_kit/tools/fetcher.py:127`
**修复:** 用 `concurrent.futures.ThreadPoolExecutor` + `timeout=30` 包裹 yfinance 请求

### Task P2-4: Pipeline 部分失败恢复

**问题:** LLM 失败后仍渲染几乎为空的 HTML
**文件:** `stock_kit/tools/pipeline.py:870-1008`
**修复:** LLM 失败时标记 `llm_failed=True`，跳过 render 或生成降级报告

### Task P2-5: Validate 数据完整性增强

**问题:** `[Data]` issue 中仅 `价格校验通过` 不影响 passed，缺失 EBIT/EV 不触发失败
**文件:** `stock_kit/tools/runtime/report_engine/stages/validate.py:93-98`
**修复:** 增加关键字段缺失检查（ebit_ev, roic, f_score），缺失 → FAIL

### Task P2-6: 消除重复 TICKER_MAP

**问题:** `pipeline.py:59-68` 维护独立的 `TICKER_NAME_MAP`，与 `company_registry` 不同步
**文件:** `stock_kit/tools/pipeline.py:59-68`
**修复:** 删除独立映射，改用 `company_registry.ticker_to_name_zh()`