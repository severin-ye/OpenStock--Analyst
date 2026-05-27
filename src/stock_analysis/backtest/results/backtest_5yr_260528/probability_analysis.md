# 概率加权分析报告

**生成时间**: 2026-05-28 01:58

## 信号类型统计

| 信号类型 | 观测数 | 预测概率 | 实际正确率 | 校准度 |
|---------|:------:|:-------:|:---------:|:-----:|
| BULLISH | 5 | 64.7% | 60.0% (3/5) | 95.3% |
| BEARISH | 8 | 35.8% | 12.5% (1/8) | 76.7% |
| NEUTRAL | 5 | 51.1% | 40.0% (2/5) | 88.9% |

## 公司统计

| 公司 | 观测数 | 平均预测概率 | 6月正确率 | 平均回报 |
|------|:------:|:----------:|:--------:|:-------:|
| 英伟达 | 6 | 54.4% | 50.0% (3/6) | +36.56% |
| 小米 | 6 | 49.0% | 33.3% (2/6) | +nan% |
| 特斯拉 | 6 | 40.8% | 16.7% (1/6) | +18.85% |

## 预测 vs 实际对比

```json
[
  {
    "ticker": "NVDA",
    "period": "0.5yr",
    "predicted_prob": 0.656,
    "actual_return": 17.27,
    "direction_correct": true
  },
  {
    "ticker": "1810.HK",
    "period": "0.5yr",
    "predicted_prob": 0.656,
    "actual_return": NaN,
    "direction_correct": false
  },
  {
    "ticker": "TSLA",
    "period": "0.5yr",
    "predicted_prob": 0.367,
    "actual_return": 3.62,
    "direction_correct": false
  },
  {
    "ticker": "NVDA",
    "period": "1.0yr",
    "predicted_prob": 0.656,
    "actual_return": 31.25,
    "direction_correct": true
  },
  {
    "ticker": "1810.HK",
    "period": "1.0yr",
    "predicted_prob": 0.533,
    "actual_return": -21.75,
    "direction_correct": false
  },
  {
    "ticker": "TSLA",
    "period": "1.0yr",
    "predicted_prob": 0.344,
    "actual_return": 15.57,
    "direction_correct": false
  },
  {
    "ticker": "NVDA",
    "period": "1.5yr",
    "predicted_prob": 0.633,
    "actual_return": -0.38,
    "direction_correct": false
  },
  {
    "ticker": "1810.HK",
    "period": "1.5yr",
    "predicted_prob": 0.533,
    "actual_return": 82.86,
    "direction_correct": true
  },
  {
    "ticker": "TSLA",
    "period": "1.5yr",
    "predicted_prob": 0.467,
    "actual_return": 7.21,
    "direction_correct": false
  },
  {
    "ticker": "NVDA",
    "period": "2.0yr",
    "predicted_prob": 0.633,
    "actual_return": 27.78,
    "direction_correct": true
  },
  {
    "ticker": "1810.HK",
    "period": "2.0yr",
    "predicted_prob": 0.533,
    "actual_return": 54.01,
    "direction_correct": true
  },
  {
    "ticker": "TSLA",
    "period": "2.0yr",
    "predicted_prob": 0.489,
    "actual_return": 88.9,
    "direction_correct": false
  },
  {
    "ticker": "NVDA",
    "period": "2.5yr",
    "predicted_prob": 0.344,
    "actual_return": 120.73,
    "direction_correct": false
  },
  {
    "ticker": "1810.HK",
    "period": "2.5yr",
    "predicted_prob": 0.344,
    "actual_return": 21.8,
    "direction_correct": false
  },
  {
    "ticker": "TSLA",
    "period": "2.5yr",
    "predicted_prob": 0.389,
    "actual_return": -24.08,
    "direction_correct": true
  },
  {
    "ticker": "NVDA",
    "period": "3.0yr",
    "predicted_prob": 0.344,
    "actual_return": 22.7,
    "direction_correct": false
  },
  {
    "ticker": "1810.HK",
    "period": "3.0yr",
    "predicted_prob": 0.344,
    "actual_return": 42.86,
    "direction_correct": false
  },
  {
    "ticker": "TSLA",
    "period": "3.0yr",
    "predicted_prob": 0.389,
    "actual_return": 21.89,
    "direction_correct": false
  }
]
```
