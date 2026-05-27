"""pytest shared fixtures and configuration"""
import os
from pathlib import Path

import pytest


@pytest.fixture
def base_dir() -> Path:
    """项目根目录 fixture"""
    return Path(os.environ.get(
        'STOCK_ANALYSIS_HOME',
        str(Path(__file__).resolve().parent.parent)
    ))


@pytest.fixture
def output_dir(base_dir) -> Path:
    """分析输出目录 fixture"""
    return base_dir / '分析输出'


@pytest.fixture
def src_dir(base_dir) -> Path:
    """src/stock_analysis 目录 fixture"""
    return base_dir / 'src' / 'stock_analysis'


@pytest.fixture
def prices_json(src_dir) -> Path:
    """prices.json 路径 fixture"""
    return src_dir / 'data' / 'prices.json'
