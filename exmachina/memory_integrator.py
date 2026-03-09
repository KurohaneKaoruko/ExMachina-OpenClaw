"""
ExMachina Memory Integrator - OpenClaw Memory 系统集成

提供与 OpenClaw memory 系统的深度集成：
- 自动将任务知识沉淀到 MEMORY.md
- 从历史任务中检索相关上下文
- 跨任务学习和模式提取
"""
from __future__ import annotations

import fcntl
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class MemoryEntry:
    """记忆条目"""
    timestamp: str
    category: str  # task, decision, lesson, reference, todo
    title: str
    content: str
    tags: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskSummary:
    """任务总结"""
    task_id: str
    title: str
    link_bodies: list[str]
    key_decisions: list[str]
    lessons_learned: list[str]
    references: list[str]
    todos: list[str]
    status: str  # completed, failed, partial


class MemoryIntegrator:
    """OpenClaw Memory 系统集成器"""

    # 日期提取正则
    DATE_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2})')

    def __init__(self, workspace_path: str | Path | None = None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self.memory_dir = self.workspace_path / "memory"
        self.memory_file = self.workspace_path / "MEMORY.md"

    # ============ 读取相关 ============

    def read_memory(
        self,
        max_entries: int = 50,
        category: str | None = None
    ) -> list[MemoryEntry]:
        """读取 MEMORY.md 中的记忆

        Args:
            max_entries: 最大返回条目数
            category: 可选，按分类过滤

        Returns:
            记忆条目列表
        """
        if not self.memory_file.exists():
            return []

        content = self.memory_file.read_text(encoding="utf-8")
        entries = self._parse_memory_content(content)

        # 分类过滤
        if category:
            entries = [e for e in entries if e.category == category]

        # 直接截断，不读取全部再处理
        return entries[:max_entries]

    def _parse_memory_content(self, content: str) -> list[MemoryEntry]:
        """解析 MEMORY.md 内容"""
        entries = []

        # 简单解析：按 ## 分隔的章节
        sections = re.split(r'^##\s+', content, flags=re.MULTILINE)

        for section in sections[1:]:  # 跳过开头空部分
            lines = section.split('\n')
            if not lines:
                continue

            title = lines[0].strip()
            body = '\n'.join(lines[1:]).strip()

            # 提取原始日期
            timestamp = self._extract_timestamp(title) or \
                        datetime.now(timezone.utc).isoformat()

            # 识别分类
            category = self._classify_entry(title)

            entries.append(MemoryEntry(
                timestamp=timestamp,
                category=category,
                title=title,
                content=body,
                tags=self._extract_tags(body)
            ))

        return entries

    def _extract_timestamp(self, title: str) -> str | None:
        """从标题中提取时间戳"""
        match = self.DATE_PATTERN.search(title)
        if match:
            return f"{match.group(1)}T00:00:00+00:00"
        return None

    def _classify_entry(self, title: str) -> str:
        """根据标题分类"""
        title_lower = title.lower()
        if any(kw in title_lower for kw in ["lesson", "经验", "教训"]):
            return "lesson"
        elif any(kw in title_lower for kw in ["决策", "decision"]):
            return "decision"
        elif any(kw in title_lower for kw in ["todo", "待办", "计划"]):
            return "todo"
        elif any(kw in title_lower for kw in ["参考", "reference", "链接"]):
            return "reference"
        return "task"

    def _extract_tags(self, content: str) -> list[str]:
        """提取内容中的标签"""
        tag_pattern = r'#(\w+)'
        return re.findall(tag_pattern, content)

    def search_memory(
        self,
        query: str,
        max_results: int = 10
    ) -> list[MemoryEntry]:
        """搜索记忆"""
        # 只读取必要的条目数
        all_entries = self.read_memory(max_entries=max_results * 20)

        # 简单的关键词匹配
        query_lower = query.lower()
        results = []

        for entry in all_entries:
            score = 0
            if query_lower in entry.title.lower():
                score += 3
            if query_lower in entry.content.lower():
                score += 1
            for tag in entry.tags:
                if query_lower in tag.lower():
                    score += 2

            if score > 0:
                results.append((score, entry))

        # 按相关度排序
        results.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in results[:max_results]]

    def get_related_context(
        self,
        task: str,
        link_bodies: list[str]
    ) -> dict[str, Any]:
        """获取与当前任务相关的历史上下文"""
        # 收集所有搜索查询
        search_queries = [task] + list(link_bodies)
        seen_titles: set[str] = set()
        unique_entries: list[MemoryEntry] = []

        # 去重搜索
        for query in search_queries:
            results = self.search_memory(query, max_results=5)
            for entry in results:
                if entry.title not in seen_titles:
                    seen_titles.add(entry.title)
                    unique_entries.append(entry)

        return {
            "related_entries": [
                {
                    "category": e.category,
                    "title": e.title,
                    "content": e.content[:200] + "..." if len(e.content) > 200 else e.content,
                    "tags": e.tags
                }
                for e in unique_entries[:5]
            ],
            "has_relevant_history": len(unique_entries) > 0
        }

    # ============ 写入相关 ============

    def write_memory_entry(self, entry: MemoryEntry) -> None:
        """写入单条记忆（带文件锁）"""
        self._ensure_memory_file()

        content = self._format_entry(entry)

        with open(self.memory_file, 'a', encoding="utf-8") as f:
            # 获取独占锁
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(content)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def _ensure_memory_file(self) -> None:
        """确保 MEMORY.md 存在"""
        if not self.memory_file.exists():
            header = f"""# MEMORY - 长期记忆

*自动生成的任务记忆*

---
"""
            self.memory_file.write_text(header, encoding="utf-8")

    def _format_entry(self, entry: MemoryEntry) -> str:
        """格式化记忆条目"""
        lines = [
            f"## {entry.timestamp[:10]} - {entry.category.upper()} - {entry.title}",
            "",
            entry.content,
            ""
        ]

        if entry.tags:
            lines.append("Tags: " + " ".join(f"#{tag}" for tag in entry.tags))
            lines.append("")

        if entry.context:
            lines.append("```json")
            lines.append(json.dumps(entry.context, ensure_ascii=False, indent=4))
            lines.append("```")
            lines.append("")

        lines.append("---\n")

        return "\n".join(lines)

    def write_task_summary(self, summary: TaskSummary) -> None:
        """写入任务总结"""
        content_parts = [
            f"## 任务: {summary.title}",
            "",
            f"**状态**: {summary.status}",
            f"**执行连结体**: {', '.join(summary.link_bodies)}",
            "",
            "### 关键决策",
        ]

        for i, decision in enumerate(summary.key_decisions, 1):
            content_parts.append(f"{i}. {decision}")

        content_parts.extend([
            "",
            "### 经验教训"
        ])

        for i, lesson in enumerate(summary.lessons_learned, 1):
            content_parts.append(f"{i}. {lesson}")

        if summary.todos:
            content_parts.extend([
                "",
                "### 待跟进",
            ])
            for todo in summary.todos:
                content_parts.append(f"- [ ] {todo}")

        entry = MemoryEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            category="task",
            title=f"[{summary.status.upper()}] {summary.title}",
            content="\n".join(content_parts),
            context={
                "task_id": summary.task_id,
                "link_bodies": summary.link_bodies,
                "status": summary.status
            }
        )

        self.write_memory_entry(entry)

    # ============ 知识交接 ============

    def create_handover_document(
        self,
        mission_plan: dict[str, Any],
        execution_results: dict[str, Any]
    ) -> dict[str, Any]:
        """创建知识交接文档"""
        # 提取关键信息
        task = mission_plan.get("mission_title", "Untitled")
        link_bodies = []

        # 处理 primary
        primary = mission_plan.get("primary")
        if primary:
            if isinstance(primary, dict):
                link_bodies.append(primary.get("name", ""))
            elif isinstance(primary, list):
                link_bodies.extend([p.get("name", "") for p in primary if isinstance(p, dict)])

        # 处理 support_bodies
        support = mission_plan.get("support_bodies", [])
        if isinstance(support, list):
            link_bodies.extend([
                body.get("name", "")
                for body in support
                if isinstance(body, dict)
            ])

        # 从执行结果中提取教训
        lessons = []
        if "issues" in execution_results:
            for issue in execution_results["issues"]:
                lessons.append(f"问题: {issue}")
        if "learnings" in execution_results:
            lessons.extend(execution_results["learnings"])

        # 创建任务总结
        summary = TaskSummary(
            task_id=mission_plan.get("mission_id", ""),
            title=task,
            link_bodies=[lb for lb in link_bodies if lb],  # 过滤空字符串
            key_decisions=execution_results.get("decisions", []),
            lessons_learned=lessons,
            references=execution_results.get("references", []),
            todos=execution_results.get("todos", []),
            status=execution_results.get("status", "completed")
        )

        self.write_task_summary(summary)

        # 返回可附加到任务的结构化数据
        return {
            "handover_created": True,
            "memory_entries": len(lessons) + len(summary.key_decisions),
            "next_task_hints": self._generate_next_hints(summary)
        }

    def _generate_next_hints(self, summary: TaskSummary) -> list[str]:
        """生成下次任务的提示"""
        hints = []

        # 基于教训生成提示
        for lesson in summary.lessons_learned[:3]:
            hints.append(f"参考: {lesson}")

        # 基于待办生成提示
        for todo in summary.todos[:2]:
            hints.append(f"继续: {todo}")

        return hints

    # ============ 定期维护 ============

    def cleanup_old_entries(self, days: int = 90) -> int:
        """清理旧记忆条目

        Args:
            days: 保留最近多少天的记录

        Returns:
            删除的条目数
        """
        if not self.memory_file.exists():
            return 0

        content = self.memory_file.read_text(encoding="utf-8")
        cutoff_date = datetime.now(timezone.utc).timestamp() - (days * 86400)

        sections = re.split(r'^##\s+', content, flags=re.MULTILINE)

        # 保留 header 和分隔符
        header = sections[0] if sections else ""
        kept_sections = [header]

        deleted_count = 0

        for section in sections[1:]:
            lines = section.split('\n')
            if not lines:
                continue

            title = lines[0].strip()
            timestamp = self._extract_timestamp(title)

            if timestamp:
                try:
                    # 解析 ISO 格式时间戳
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    if dt.timestamp() < cutoff_date:
                        deleted_count += 1
                        continue  # 跳过这个条目
                except (ValueError, TypeError):
                    # 无法解析日期，保留
                    pass

            kept_sections.append("## " + section)

        if deleted_count > 0:
            with open(self.memory_file, 'w', encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write("\n## ".join(kept_sections))
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        return deleted_count

    def generate_memory_report(self) -> dict[str, Any]:
        """生成记忆报告"""
        entries = self.read_memory(max_entries=100)

        categories = {}
        for entry in entries:
            cat = entry.category
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_entries": len(entries),
            "by_category": categories,
            "memory_file": str(self.memory_file),
            "memory_dir": str(self.memory_dir)
        }


def create_memory_integrator(workspace_path: str | None = None) -> MemoryIntegrator:
    """创建 MemoryIntegrator 实例"""
    return MemoryIntegrator(workspace_path)
