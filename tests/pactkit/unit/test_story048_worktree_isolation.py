"""STORY-048: Worktree Isolation for Subagent Sprint Tests"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# =============================================================================
# AC1 / R1: All subagent Task calls include isolation="worktree"
# =============================================================================
class TestWorktreeIsolationPresent:
    """R1: Sprint playbook MUST include isolation='worktree' for all subagent stages."""

    def test_sprint_prompt_contains_isolation_worktree(self):
        from pactkit.prompts import SPRINT_PROMPT
        assert 'isolation' in SPRINT_PROMPT, \
            'SPRINT_PROMPT 缺少 isolation 参数'

    def test_sprint_prompt_contains_worktree_keyword(self):
        from pactkit.prompts import SPRINT_PROMPT
        assert 'worktree' in SPRINT_PROMPT.lower(), \
            'SPRINT_PROMPT 缺少 worktree 关键词'

    def test_stage_a_has_isolation(self):
        """Stage A (Build) Task call must include isolation='worktree'."""
        from pactkit.prompts import SPRINT_PROMPT
        # Find Stage A section and verify isolation parameter
        stage_a_start = SPRINT_PROMPT.find('Stage A')
        assert stage_a_start != -1, '缺少 Stage A 定义'
        stage_b_start = SPRINT_PROMPT.find('Stage B', stage_a_start)
        stage_a_section = SPRINT_PROMPT[stage_a_start:stage_b_start]
        assert 'isolation' in stage_a_section, \
            'Stage A 的 Task 调用缺少 isolation 参数'

    def test_stage_b_has_isolation(self):
        """Stage B (Check) Task calls must include isolation='worktree'."""
        from pactkit.prompts import SPRINT_PROMPT
        stage_b_start = SPRINT_PROMPT.find('Stage B')
        assert stage_b_start != -1, '缺少 Stage B 定义'
        stage_c_start = SPRINT_PROMPT.find('Stage C', stage_b_start)
        stage_b_section = SPRINT_PROMPT[stage_b_start:stage_c_start]
        assert 'isolation' in stage_b_section, \
            'Stage B 的 Task 调用缺少 isolation 参数'

    def test_stage_c_has_isolation(self):
        """Stage C (Close) Task call must include isolation='worktree'."""
        from pactkit.prompts import SPRINT_PROMPT
        stage_c_start = SPRINT_PROMPT.find('Stage C')
        assert stage_c_start != -1, '缺少 Stage C 定义'
        # Stage C extends to end of Phase 2 or Error Handling
        end_marker = SPRINT_PROMPT.find('Error Handling', stage_c_start)
        stage_c_section = SPRINT_PROMPT[stage_c_start:end_marker]
        assert 'isolation' in stage_c_section, \
            'Stage C 的 Task 调用缺少 isolation 参数'


# =============================================================================
# AC1-AC2 / R2: Worktree change recovery strategy
# =============================================================================
class TestWorktreeRecoveryStrategy:
    """R2: Sprint playbook MUST include worktree change recovery instructions."""

    def test_contains_merge_instruction(self):
        """Build stage changes must be merged back to working branch."""
        from pactkit.prompts import SPRINT_PROMPT
        content_lower = SPRINT_PROMPT.lower()
        has_merge = 'merge' in content_lower or 'cherry-pick' in content_lower
        assert has_merge, \
            'SPRINT_PROMPT 缺少 worktree 变更合并指引 (merge/cherry-pick)'

    def test_contains_report_recovery(self):
        """Check stage reports must be copied back from worktree."""
        from pactkit.prompts import SPRINT_PROMPT
        content_lower = SPRINT_PROMPT.lower()
        has_copy = 'copy' in content_lower or 'recover' in content_lower \
            or 'collect' in content_lower
        assert has_copy, \
            'SPRINT_PROMPT 缺少报告文件回收指引'


# =============================================================================
# R3: Auto-cleanup for no-change worktrees
# =============================================================================
class TestWorktreeAutoCleanup:
    """R3: Sprint playbook SHOULD explain auto-cleanup behavior."""

    def test_mentions_auto_cleanup(self):
        from pactkit.prompts import SPRINT_PROMPT
        content_lower = SPRINT_PROMPT.lower()
        has_cleanup = 'auto' in content_lower and 'clean' in content_lower
        assert has_cleanup, \
            'SPRINT_PROMPT 缺少 worktree 自动清理说明'


# =============================================================================
# AC3 / R4: Error handling for worktree scenarios
# =============================================================================
class TestWorktreeErrorHandling:
    """R4: Sprint playbook MUST handle worktree-specific errors."""

    def test_handles_merge_conflict(self):
        """Must mention merge conflict handling."""
        from pactkit.prompts import SPRINT_PROMPT
        content_lower = SPRINT_PROMPT.lower()
        assert 'conflict' in content_lower, \
            'SPRINT_PROMPT 缺少合并冲突处理指引'

    def test_handles_worktree_residue(self):
        """Must mention worktree cleanup on error."""
        from pactkit.prompts import SPRINT_PROMPT
        assert 'git worktree' in SPRINT_PROMPT.lower(), \
            'SPRINT_PROMPT 缺少 git worktree 清理命令提示'


# =============================================================================
# AC4 / R5: Backward compatibility — fallback for unsupported environments
# =============================================================================
class TestWorktreeFallback:
    """R5: Sprint MUST NOT fail in environments without worktree support."""

    def test_mentions_fallback(self):
        from pactkit.prompts import SPRINT_PROMPT
        content_lower = SPRINT_PROMPT.lower()
        has_fallback = 'fallback' in content_lower or 'fall back' in content_lower
        assert has_fallback, \
            'SPRINT_PROMPT 缺少 worktree 不可用时的回退指引'

    def test_mentions_shallow_clone_scenario(self):
        from pactkit.prompts import SPRINT_PROMPT
        content_lower = SPRINT_PROMPT.lower()
        assert 'shallow' in content_lower, \
            'SPRINT_PROMPT 缺少 shallow clone 场景说明'


# =============================================================================
# AC5: Existing sprint behavior — no regression
# =============================================================================
class TestNoRegression:
    """AC5: All existing sprint keywords and structures must still be present."""

    def test_existing_team_keywords_preserved(self):
        from pactkit.prompts import SPRINT_PROMPT
        for keyword in ['TeamCreate', 'TaskCreate', 'SendMessage', 'TeamDelete']:
            assert keyword in SPRINT_PROMPT, \
                f'现有关键词 {keyword} 在修改后丢失'

    def test_existing_subagent_types_preserved(self):
        from pactkit.prompts import SPRINT_PROMPT
        for agent in ['system-architect', 'qa-engineer', 'security-auditor', 'repo-maintainer']:
            assert agent in SPRINT_PROMPT, \
                f'现有 subagent_type {agent} 在修改后丢失'

    def test_existing_stage_structure_preserved(self):
        from pactkit.prompts import SPRINT_PROMPT
        for stage in ['Stage A', 'Stage B', 'Stage C']:
            assert stage in SPRINT_PROMPT, \
                f'现有阶段 {stage} 在修改后丢失'

    def test_existing_frontmatter_preserved(self):
        from pactkit.prompts import SPRINT_PROMPT
        assert SPRINT_PROMPT.strip().startswith('---'), \
            'SPRINT_PROMPT frontmatter 丢失'

    def test_existing_arguments_placeholder_preserved(self):
        from pactkit.prompts import SPRINT_PROMPT
        assert '$ARGUMENTS' in SPRINT_PROMPT, \
            'SPRINT_PROMPT $ARGUMENTS 占位符丢失'
