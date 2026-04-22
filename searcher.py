from ddgs import DDGS
from typing import Optional


class WebSearcher:
    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        results = []
        try:
            search_results = self.ddgs.text(query, max_results=max_results)
            for r in search_results:
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                })
        except Exception as e:
            print(f"搜索失败: {e}")
        return results

    def format_results(self, results: list[dict]) -> str:
        if not results:
            return "未找到相关搜索结果。"
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(
                f"[{i}] {r['title']}\n"
                f"    {r['snippet']}\n"
                f"    链接: {r['url']}"
            )
        return "\n\n".join(formatted)
