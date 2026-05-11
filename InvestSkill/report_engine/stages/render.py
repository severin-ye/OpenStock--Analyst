"""Stage 3: Jinja2 模板渲染

职责: 将 StockReport JSON 渲染为完整 HTML。
纯 Python + Jinja2，不需要 LLM。
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from report_engine.schema import StockReport, ChartType
import json

TEMPLATE_DIR = Path(__file__).parent.parent / 'templates'


def _json_dumps(value):
    return json.dumps(value, ensure_ascii=False)


def _css_alpha(color: str, alpha: float) -> str:
    """将 CSS 颜色转为带 alpha 的 rgba"""
    if color.startswith('#'):
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        return f'rgba({r},{g},{b},{alpha})'
    return color


def build_env():
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )
    env.filters['tojson'] = _json_dumps
    env.filters['css_alpha'] = _css_alpha
    return env


def render(report: StockReport) -> str:
    """将 StockReport 渲染为 HTML 字符串"""
    env = build_env()
    template = env.get_template('report.jinja2')

    for chart in report.charts:
        if chart.horizontal:
            chart.chart_type = ChartType.BAR

    ctx = report.model_dump()
    ctx['SECTION_LABELS'] = {
        's1': '涨跌比例总览',
        's2': report.s2.title if report.s2 else '公司概览',
        's3': '过去一年走势',
        's4': report.s4.title if report.s4 else '竞争格局',
        's5': '估值分析',
        's6': '未来一年展望',
        's7': '风险矩阵',
        's8': '投资信号',
    }

    return template.render(**ctx)


def render_to_file(report: StockReport, output_path: str) -> str:
    """渲染并写入文件"""
    html = render(report)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding='utf-8')
    return str(path)
