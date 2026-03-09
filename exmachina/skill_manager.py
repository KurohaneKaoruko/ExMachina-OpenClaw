"""
ExMachina Skill Manager - OpenClaw Skill 深度集成

提供与 OpenClaw skill 系统的深度集成能力：
- 自动安装依赖 skill
- 动态绑定 skill 到任务上下文
- 检查 skill 状态和兼容性
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class SkillManager:
    """Skill 生命周期管理器"""

    def __init__(self, profile: dict[str, Any] | None = None):
        self.profile = profile or {}
        self.skill_catalog = self.profile.get("skill_catalog", {})
        self._cached_skills: list[dict[str, Any]] | None = None

    def _get_installed_skills(self) -> list[dict[str, Any]]:
        """获取已安装的 skill 列表（带缓存）"""
        if self._cached_skills is not None:
            return self._cached_skills

        try:
            result = subprocess.run(
                ["clawdhub", "list", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self._cached_skills = json.loads(result.stdout)
                return self._cached_skills
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

        return []

    def invalidate_cache(self) -> None:
        """清除缓存，强制重新获取"""
        self._cached_skills = None

    def get_required_skills(self, link_body_names: list[str]) -> list[str]:
        """
        根据指定的 LinkBody 获取需要启用的 skill 列表

        Args:
            link_body_names: 激活的连结体名称列表

        Returns:
            需要安装/启用的 skill ID 列表
        """
        required = set()

        # 从 skill_catalog 中匹配
        for name in link_body_names:
            if name in self.skill_catalog:
                skill_info = self.skill_catalog[name]
                required.add(skill_info.get("skill_id", name))

        return list(required)

    def check_skill_status(
        self,
        skill_id: str,
        use_cache: bool = True
    ) -> dict[str, Any]:
        """
        检查指定 skill 的安装状态

        Args:
            skill_id: Skill ID
            use_cache: 是否使用缓存（默认 True）

        Returns:
            包含 status, version, path 的字典
        """
        installed_skills = self._get_installed_skills() if use_cache else []

        for skill in installed_skills:
            if skill.get("name") == skill_id or skill.get("id") == skill_id:
                return {
                    "status": "installed",
                    "version": skill.get("version"),
                    "path": skill.get("path")
                }

        return {"status": "not_installed", "version": None, "path": None}

    def ensure_skills_installed(
        self,
        skill_ids: list[str] | None = None,
        link_body_names: list[str] | None = None
    ) -> dict[str, Any]:
        """
        确保所需的 skill 已安装

        Args:
            skill_ids: 指定的 skill ID 列表
            link_body_names: 或通过连结体名称自动推断

        Returns:
            安装结果报告
        """
        # 确定需要检查的 skill
        if skill_ids is None and link_body_names:
            skill_ids = self.get_required_skills(link_body_names)

        if not skill_ids:
            return {"installed": [], "failed": [], "skipped": []}

        # 重新获取最新状态
        self.invalidate_cache()

        installed = []
        failed = []
        skipped = []

        for skill_id in skill_ids:
            status = self.check_skill_status(skill_id, use_cache=False)

            if status["status"] == "installed":
                skipped.append(skill_id)
                continue

            # 尝试安装
            try:
                result = subprocess.run(
                    ["clawdhub", "install", skill_id],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    installed.append(skill_id)
                else:
                    failed.append({
                        "skill_id": skill_id,
                        "error": result.stderr,
                        "returncode": result.returncode
                    })
            except Exception as e:
                failed.append({
                    "skill_id": skill_id,
                    "error": str(e),
                    "returncode": -1
                })

        # 更新缓存
        self.invalidate_cache()

        return {
            "installed": installed,
            "failed": failed,
            "skipped": skipped,
            "total": len(skill_ids)
        }

    def _calculate_keyword_score(
        self,
        task_keywords: list[str],
        skill_keywords: list[str]
    ) -> int:
        """计算任务与 skill 的关键词匹配分数"""
        score = 0
        for tk in task_keywords:
            tk_lower = tk.lower()
            for sk in skill_keywords:
                sk_lower = sk.lower()
                if sk_lower in tk_lower or tk_lower in sk_lower:
                    score += 1
        return score

    def generate_skill_bindings(
        self,
        link_body_names: list[str],
        task_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        根据任务上下文生成 skill 绑定配置

        Args:
            link_body_names: 激活的连结体名称
            task_context: 任务上下文信息

        Returns:
            可直接用于 OpenClaw 的 skill 绑定配置
        """
        bindings = {
            "skills": [],
            "env": {},
            "priority": []
        }

        task_keywords = task_context.get("keywords", []) if task_context else []

        for name in link_body_names:
            if name not in self.skill_catalog:
                continue

            skill_info = self.skill_catalog[name]
            skill_keywords = skill_info.get("keywords", [])

            # 计算匹配分数
            match_score = self._calculate_keyword_score(
                task_keywords,
                skill_keywords
            )

            skill_entry = {
                "id": skill_info.get("skill_id"),
                "path": skill_info.get("skill_path"),
                "enabled": True,
                "priority": skill_info.get("priority", 50) - match_score * 10
            }

            bindings["skills"].append(skill_entry)

        # 按优先级排序（数字越小越优先）
        bindings["skills"].sort(key=lambda x: x.get("priority", 50))

        return bindings

    def export_skill_manifest(
        self,
        output_path: str | Path,
        overwrite: bool = True
    ) -> bool:
        """
        导出 skill 清单供 OpenClaw 使用

        Args:
            output_path: 输出文件路径
            overwrite: 是否覆盖已存在的文件（默认 True）

        Returns:
            是否成功导出
        """
        output = Path(output_path)

        if output.exists() and not overwrite:
            return False

        manifest = {
            "version": "1.0",
            "catalog": self.skill_catalog,
            "required_skills": [
                info.get("skill_id")
                for info in self.skill_catalog.values()
            ]
        }

        output.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return True


def load_skill_manager(profile_path: str | None = None) -> SkillManager:
    """加载 SkillManager 实例"""
    if profile_path:
        profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    else:
        from .profile import load_profile
        profile = load_profile()

    return SkillManager(profile)
