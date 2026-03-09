"""
ExMachina Dynamic Workflow Planner - 动态工作流生成器

提供动态工作流生成能力：
- 根据任务输入动态生成执行阶段
- 条件分支和并行任务识别
- 阶段自适应调整
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TaskContext:
    """任务上下文"""
    task: str
    keywords: list[str] = field(default_factory=list)
    raw_task: str = ""  # 保留原始任务文本用于精确匹配
    has_workspace: bool = False
    has_repo: bool = False
    has_tests: bool = False
    estimated_complexity: str = "medium"  # low, medium, high
    risk_level: str = "medium"  # low, medium, high


@dataclass
class ExecutionStage:
    """动态执行阶段"""
    name: str
    description: str
    parallel_with: list[str] = field(default_factory=list)
    conditional: bool = False
    condition: str = ""
    retry_on_fail: bool = False
    max_retries: int = 1


# 可配置的风险规则
RISK_RULES = {
    "high": [
        "删除", "drop", "rm ", "rm$", "迁移", "migrate",
        "重构", "refactor", "生产", "线上", "正式环境",
        "权限", "sudo", "chmod 777"
    ],
    "medium": [
        "修改", "update", "改", "调整"
    ]
}

# 可配置的复杂度关键词
COMPLEXITY_KEYWORDS = {
    "high": ["重构", "迁移", "架构", "系统设计", "多模块"],
    "medium": ["实现", "开发", "功能", "接口"]
}


class DynamicWorkflowPlanner:
    """动态工作流规划器"""

    # 阶段模板库
    STAGE_TEMPLATES = {
        # 基础阶段
        "analyze": {
            "name": "任务分析",
            "description": "分析任务需求、约束和边界",
            "always": True
        },
        "plan": {
            "name": "规划方案",
            "description": "制定具体执行方案",
            "always": True
        },
        "execute": {
            "name": "执行实施",
            "description": "按方案执行任务",
            "always": True
        },
        "validate": {
            "name": "验证确认",
            "description": "验证执行结果是否符合预期",
            "conditional": True
        },
        "document": {
            "name": "文档输出",
            "description": "生成文档和说明",
            "keywords": ["文档", "readme", "说明", "教程", "手册"]
        },
        "test": {
            "name": "测试验证",
            "keywords": ["测试", "test", "验证", "校验"],
            "requires": "tests"
        },
        "deploy": {
            "name": "部署上线",
            "keywords": ["部署", "发布", "上线", "deploy", "release"]
        },
        "review": {
            "name": "代码审查",
            "keywords": ["review", "审查", "pr", "merge", "code review"]
        },
        "security_check": {
            "name": "安全检查",
            "keywords": ["安全", "漏洞", "审计", "security"]
        },
        "optimize": {
            "name": "性能优化",
            "keywords": ["优化", "性能", "performance", "效率"]
        },
        "handoff": {
            "name": "知识交接",
            "description": "沉淀任务成果和经验",
            "always": True
        }
    }

    # 并行可执行阶段（对称的）
    PARALLEL_COMPATIBLE = {
        ("analyze", "analyze"),
        ("document", "document"),
        ("test", "validate"),
        ("security_check", "optimize"),
        # 添加对称版本
        ("document", "analyze"),
    }

    def __init__(self, profile: dict[str, Any] | None = None):
        self.profile = profile or {}

    def analyze_task(
        self,
        task: str,
        workspace: Any = None,
        repo: Any = None
    ) -> TaskContext:
        """分析任务上下文"""
        keywords = self._extract_keywords(task)

        has_workspace = workspace is not None
        has_repo = repo is not None
        has_tests = has_workspace and self._check_tests_exist(workspace)

        # 评估复杂度
        complexity = self._assess_complexity(task, keywords)

        # 评估风险
        risk = self._assess_risk(task)

        return TaskContext(
            task=task,
            keywords=keywords,
            raw_task=task,  # 保存原始文本
            has_workspace=has_workspace,
            has_repo=has_repo,
            has_tests=has_tests,
            estimated_complexity=complexity,
            risk_level=risk
        )

    def _extract_keywords(self, task: str) -> list[str]:
        """提取任务关键词"""
        # 常见关键词模式
        keyword_patterns = [
            (r"测试|test|验证|校验", "test"),
            (r"文档|readme|说明|教程|手册", "document"),
            (r"部署|发布|上线|deploy|release", "deploy"),
            (r"调研|分析|研究|调研", "research"),
            (r"架构|设计|重构", "architecture"),
            (r"实现|开发|编码|写代码", "implementation"),
            (r"安全|审计|漏洞|权限", "security"),
            (r"优化|性能|效率", "optimize"),
            (r"修复|bug|fix|问题", "fix"),
            (r"审查|review|pr|merge", "review")
        ]

        keywords = []
        for pattern, label in keyword_patterns:
            if re.search(pattern, task, re.IGNORECASE):
                keywords.append(label)

        return keywords

    def _check_tests_exist(self, workspace: Any) -> bool:
        """检查是否存在测试"""
        if workspace and hasattr(workspace, "test_paths"):
            return len(workspace.test_paths) > 0
        return False

    def _assess_complexity(self, task: str, keywords: list[str]) -> str:
        """评估任务复杂度"""
        score = 0

        # 长度因素
        if len(task) > 500:
            score += 2
        elif len(task) > 200:
            score += 1

        # 多关键词
        if len(keywords) > 3:
            score += 2
        elif len(keywords) > 1:
            score += 1

        # 复杂度关键词
        for kw in COMPLEXITY_KEYWORDS.get("high", []):
            if kw in task:
                score += 1
                break

        if score >= 4:
            return "high"
        elif score >= 2:
            return "medium"
        return "low"

    def _assess_risk(self, task: str) -> str:
        """评估任务风险"""
        task_lower = task.lower()

        # 高风险关键词检查
        for kw in RISK_RULES.get("high", []):
            if kw.lower() in task_lower:
                return "high"

        # 中风险关键词检查
        for kw in RISK_RULES.get("medium", []):
            if kw.lower() in task_lower:
                return "medium"

        return "low"

    def _match_stage_by_keyword(
        self,
        keyword: str,
        raw_task: str
    ) -> bool:
        """检查原始任务是否匹配阶段关键词"""
        keyword_map = self.STAGE_TEMPLATES.get(keyword, {}).get("keywords", [])
        for kw in keyword_map:
            if re.search(kw, raw_task, re.IGNORECASE):
                return True
        return False

    def generate_workflow(self, context: TaskContext) -> list[ExecutionStage]:
        """生成动态工作流"""
        stages = []

        # 始终包含的阶段
        stages.append(self._create_stage("analyze", context))
        stages.append(self._create_stage("plan", context))

        # 根据上下文动态添加阶段
        # 使用原始任务文本进行更精确的匹配
        raw_task = context.raw_task.lower() if context.raw_task else context.task.lower()

        # 测试相关
        if context.has_tests or "test" in context.keywords:
            stages.append(self._create_stage("test", context))
            stages.append(self._create_stage("validate", context))

        # 文档相关
        if self._match_stage_by_keyword("document", raw_task):
            stages.append(self._create_stage("document", context))

        # 部署相关
        if self._match_stage_by_keyword("deploy", raw_task):
            stages.append(self._create_stage("deploy", context))

        # 审查相关
        if self._match_stage_by_keyword("review", raw_task):
            stages.append(self._create_stage("review", context))

        # 安全相关
        if self._match_stage_by_keyword("security_check", raw_task):
            stages.append(self._create_stage("security_check", context))

        # 优化相关
        if self._match_stage_by_keyword("optimize", raw_task):
            stages.append(self._create_stage("optimize", context))

        # 高复杂度任务增加验证
        if context.estimated_complexity == "high":
            validate_stage = self._create_stage("validate", context)
            validate_stage.retry_on_fail = True
            validate_stage.max_retries = 2
            stages.append(validate_stage)

        # 高风险任务增加审查
        if context.risk_level == "high":
            review_stage = self._create_stage("review", context)
            review_stage.conditional = True
            review_stage.condition = "执行结果存在风险"
            stages.append(review_stage)

        # 始终包含交接阶段
        stages.append(self._create_stage("handoff", context))

        # 规划并行执行
        stages = self._plan_parallel_execution(stages)

        return stages

    def _create_stage(self, template_key: str, context: TaskContext) -> ExecutionStage:
        """从模板创建阶段"""
        template = self.STAGE_TEMPLATES.get(template_key, {})

        return ExecutionStage(
            name=template.get("name", template_key),
            description=template.get("description", ""),
            conditional=template.get("conditional", False),
            retry_on_fail=context.risk_level == "high",
            max_retries=2 if context.risk_level == "high" else 1
        )

    def _is_parallel_compatible(self, name1: str, name2: str) -> bool:
        """检查两个阶段是否可并行执行（对称检查）"""
        return (name1, name2) in self.PARALLEL_COMPATIBLE or \
               (name2, name1) in self.PARALLEL_COMPATIBLE

    def _plan_parallel_execution(
        self,
        stages: list[ExecutionStage]
    ) -> list[ExecutionStage]:
        """规划可并行执行的阶段"""
        for i, stage1 in enumerate(stages):
            for stage2 in stages[i+1:]:
                if self._is_parallel_compatible(stage1.name, stage2.name):
                    if stage2.name not in stage1.parallel_with:
                        stage1.parallel_with.append(stage2.name)

        return stages

    def export_workflow_json(
        self,
        stages: list[ExecutionStage]
    ) -> dict[str, Any]:
        """导出为 OpenClaw 可用的 JSON 格式"""
        return {
            "version": "1.0",
            "stages": [asdict(s) for s in stages]
        }


def create_dynamic_workflow(
    task: str,
    profile: dict[str, Any] | None = None,
    workspace: Any = None,
    repo: Any = None
) -> dict[str, Any]:
    """创建动态工作流的便捷函数"""
    planner = DynamicWorkflowPlanner(profile)
    context = planner.analyze_task(task, workspace, repo)
    stages = planner.generate_workflow(context)
    return planner.export_workflow_json(stages)
