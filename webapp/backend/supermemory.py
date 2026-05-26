"""Supermemory 集成 — 持久化投资分析记忆

功能:
  - 保存分析历史和决策
  - 搜索相关分析记录
  - 追踪投资观点变化
  - 跨会话记忆持久化
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("supermemory")

# 本地记忆存储路径
MEMORY_DIR = Path(__file__).parent.parent.parent / ".supermemory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

MEMORY_FILE = MEMORY_DIR / "investments.json"


class SupermemoryClient:
    """Supermemory 本地客户端 - 使用文件系统持久化"""

    def __init__(self):
        self.memories: list[dict] = []
        self._load()

    def _load(self):
        """从文件加载记忆"""
        if MEMORY_FILE.exists():
            try:
                self.memories = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"加载记忆失败: {e}")
                self.memories = []

    def _save(self):
        """保存记忆到文件"""
        try:
            MEMORY_FILE.write_text(
                json.dumps(self.memories, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"保存记忆失败: {e}")

    def add_memory(
        self,
        content: str,
        memory_type: str = "analysis",
        ticker: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """添加新记忆"""
        memory = {
            "id": f"mem_{len(self.memories) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "content": content,
            "type": memory_type,
            "ticker": ticker,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "tags": self._extract_tags(content),
        }
        self.memories.append(memory)
        self._save()
        return memory

    def search(
        self,
        query: str,
        memory_type: Optional[str] = None,
        ticker: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """搜索记忆"""
        results = []
        query_lower = query.lower()

        for mem in reversed(self.memories):  # 最新的优先
            # 类型过滤
            if memory_type and mem.get("type") != memory_type:
                continue
            # 标的过滤
            if ticker and mem.get("ticker") != ticker:
                continue
            # 内容匹配
            if query_lower in mem.get("content", "").lower():
                results.append(mem)
                if len(results) >= limit:
                    break

        return results

    def get_by_ticker(self, ticker: str, limit: int = 20) -> list[dict]:
        """获取指定标的的所有记忆"""
        return [
            mem for mem in reversed(self.memories)
            if mem.get("ticker") == ticker
        ][:limit]

    def get_recent(self, limit: int = 10) -> list[dict]:
        """获取最近的记忆"""
        return list(reversed(self.memories[-limit:]))

    def _extract_tags(self, content: str) -> list[str]:
        """从内容中提取标签"""
        tags = []
        keywords = {
            "买入": "buy",
            "卖出": "sell",
            "持有": "hold",
            "看多": "bullish",
            "看空": "bearish",
            "低估": "undervalued",
            "高估": "overvalued",
            "风险": "risk",
            "机会": "opportunity",
        }
        for cn, en in keywords.items():
            if cn in content:
                tags.append(en)
        return tags

    def get_stats(self) -> dict:
        """获取记忆统计"""
        if not self.memories:
            return {"total": 0, "by_type": {}, "by_ticker": {}}

        by_type = {}
        by_ticker = {}
        for mem in self.memories:
            t = mem.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
            ticker = mem.get("ticker")
            if ticker:
                by_ticker[ticker] = by_ticker.get(ticker, 0) + 1

        return {
            "total": len(self.memories),
            "by_type": by_type,
            "by_ticker": by_ticker,
        }


# 全局客户端实例
_client: Optional[SupermemoryClient] = None


def get_client() -> SupermemoryClient:
    """获取全局 Supermemory 客户端"""
    global _client
    if _client is None:
        _client = SupermemoryClient()
    return _client


def add_analysis_memory(
    ticker: str,
    company_name: str,
    score: float,
    rank: str,
    verdict: str,
    key_metrics: dict,
):
    """添加分析记忆"""
    client = get_client()
    content = f"{company_name}({ticker}) 分析结果: 评分 {score:.1f}/10, 排名 {rank}, 判断: {verdict}"
    return client.add_memory(
        content=content,
        memory_type="analysis",
        ticker=ticker,
        metadata={
            "score": score,
            "rank": rank,
            "verdict": verdict,
            "key_metrics": key_metrics,
        },
    )


def search_analysis(query: str, ticker: Optional[str] = None) -> list[dict]:
    """搜索分析记录"""
    client = get_client()
    return client.search(query, memory_type="analysis", ticker=ticker)
