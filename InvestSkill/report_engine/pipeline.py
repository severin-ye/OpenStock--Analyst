"""
LangGraph 编排 — 简化版: scaffold → search(含analyze) → render → validate

用法:
  python -m report_engine.pipeline 小米
"""

import sys
from pathlib import Path
from typing import TypedDict
from datetime import datetime

from langgraph.graph import StateGraph, END

from report_engine.schema import StockReport
from report_engine.stages.scaffold import scaffold
from report_engine.stages.search import run_search
from report_engine.stages.render import render_to_file
from report_engine.stages.validate import validate

BASE_DIR = Path('/home/severin/Codelib/股市分析')


class PipelineState(TypedDict):
    company_name: str
    report: dict
    html_path: str
    errors: list[str]
    stage: str


def stage_scaffold(state: PipelineState) -> PipelineState:
    report = scaffold(state['company_name'])
    state['report'] = report.model_dump()
    state['stage'] = 'scaffold'
    print(f'[Stage 0] {report.ticker} ({report.company_name}) | {report.asset_category.value}')
    return state


def stage_search(state: PipelineState) -> PipelineState:
    report = StockReport(**state['report'])
    report = run_search(report)
    state['report'] = report.model_dump()
    state['stage'] = 'search'
    return state


def stage_render(state: PipelineState) -> PipelineState:
    report = StockReport(**state['report'])
    today = datetime.now().strftime('%y%m%d')
    output_path = BASE_DIR / state['company_name'] / f'{today}_综合分析报告.html'
    path = render_to_file(report, str(output_path))
    state['html_path'] = str(path)
    state['stage'] = 'render'
    print(f'[Stage 3] HTML: {path}')
    return state


def stage_validate(state: PipelineState) -> PipelineState:
    report = StockReport(**state['report'])
    passed, issues = validate(report, state.get('html_path', ''))
    state['errors'] = issues
    state['stage'] = 'validate'
    for i in issues:
        print(f'  {i}')
    return state


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("scaffold", stage_scaffold)
    graph.add_node("search", stage_search)
    graph.add_node("render", stage_render)
    graph.add_node("validate", stage_validate)

    graph.set_entry_point("scaffold")
    graph.add_edge("scaffold", "search")
    graph.add_edge("search", "render")
    graph.add_edge("render", "validate")
    graph.add_edge("validate", END)

    return graph.compile()


def run(company_name: str):
    app = build_graph()
    initial = PipelineState(company_name=company_name, report={}, html_path='', errors=[], stage='init')
    result = app.invoke(initial)

    print(f'\n{"="*60}')
    ok = not any('缺失' in e for e in result.get('errors', []))
    print(f'{"✅ 完成" if ok else "⚠️ 部分完成"} — {company_name}')
    print(f'HTML: {result.get("html_path", "未生成")}')
    if result.get('errors'):
        print('\n问题:')
        for e in result['errors']:
            print(f'  {e}')
    print(f'{"="*60}')
    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python -m report_engine.pipeline <公司名>')
        sys.exit(1)
    run(sys.argv[1])
