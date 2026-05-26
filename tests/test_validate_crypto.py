import os
from pathlib import Path

from stock_analysis.reports.stages.validate import validate_html_file

BASE_DIR = Path(os.environ.get('STOCK_ANALYSIS_HOME', str(Path(__file__).resolve().parent.parent)))


def test_eth_report_validation_accepts_pos_crypto_fields():
    html_path = BASE_DIR / '分析输出' / '以太坊' / '260513_综合分析报告.html'

    issues = validate_html_file(str(html_path))
    structural_issues = [i for i in issues if not i.startswith("[Data]")]
    assert not structural_issues, '\n'.join(structural_issues)
