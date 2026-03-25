import re
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestDiagramTypeRouting:
    """Scenario 1: 支持多种图表类型"""

    def test_supports_architecture_type(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        assert 'architecture' in DRAW_PROMPT_TEMPLATE.lower()

    def test_supports_dataflow_type(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        assert 'dataflow' in DRAW_PROMPT_TEMPLATE.lower() or 'data flow' in DRAW_PROMPT_TEMPLATE.lower()

    def test_supports_deployment_type(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        assert 'deployment' in DRAW_PROMPT_TEMPLATE.lower()

    def test_type_detection_instruction(self):
        """Agent should be instructed to detect diagram type from user input"""
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        # Should mention auto-detection or type selection
        lower = DRAW_PROMPT_TEMPLATE.lower()
        assert ('detect' in lower or 'classify' in lower or 'identify' in lower
                or '类型' in DRAW_PROMPT_TEMPLATE or 'type' in lower)


class TestExtendedStyleDictionary:
    """Scenario 2: 扩展样式词典"""

    def test_container_group_style(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        assert 'container' in DRAW_PROMPT_TEMPLATE.lower()

    def test_external_system_style(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        lower = DRAW_PROMPT_TEMPLATE.lower()
        assert 'external' in lower or '外部' in DRAW_PROMPT_TEMPLATE

    def test_queue_bus_style(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        lower = DRAW_PROMPT_TEMPLATE.lower()
        assert 'queue' in lower or 'bus' in lower or '队列' in DRAW_PROMPT_TEMPLATE

    def test_actor_user_style(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        lower = DRAW_PROMPT_TEMPLATE.lower()
        assert 'actor' in lower or 'user' in lower or 'person' in lower

    def test_note_style(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        lower = DRAW_PROMPT_TEMPLATE.lower()
        assert 'note' in lower or 'annotation' in lower or '注释' in DRAW_PROMPT_TEMPLATE

    def test_edge_labels_supported(self):
        """Scenario 4: Edge labels with protocol names"""
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        lower = DRAW_PROMPT_TEMPLATE.lower()
        assert 'label' in lower or 'value=' in lower


class TestNoDefaultLegend:
    """Scenario 3: Legend 不再硬编码"""

    def test_no_hardcoded_legend_in_template(self):
        """XML template should NOT contain Legend cells by default"""
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        # Extract XML block from template
        xml_match = re.search(r'```xml\s*(.*?)```', DRAW_PROMPT_TEMPLATE, re.DOTALL)
        if xml_match:
            xml_content = xml_match.group(1)
            # Should not have Legend cells (L_BG, L1, L2, etc.)
            assert 'id="L_BG"' not in xml_content, 'Legend background still hardcoded'
            assert 'id="L1"' not in xml_content, 'Legend item L1 still hardcoded'

    def test_legend_mentioned_as_optional(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        lower = DRAW_PROMPT_TEMPLATE.lower()
        assert ('optional' in lower or '可选' in DRAW_PROMPT_TEMPLATE
                or 'only when' in lower or 'if' in lower)


class TestAntiBugRules:
    """Scenario 5: Anti-Bug 规则至少 5 条"""

    def test_at_least_5_anti_bug_rules(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        # Count lines that contain "Anti-Bug" pattern
        anti_bug_count = len(re.findall(r'Anti-Bug\s*\d+', DRAW_PROMPT_TEMPLATE))
        assert anti_bug_count >= 5, f'Only {anti_bug_count} Anti-Bug rules, need >= 5'

    def test_id_uniqueness_rule(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        lower = DRAW_PROMPT_TEMPLATE.lower()
        assert 'id' in lower
        assert ('unique' in lower or 'duplicate' in lower or '唯一' in DRAW_PROMPT_TEMPLATE)

    def test_parent_reference_rule(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        lower = DRAW_PROMPT_TEMPLATE.lower()
        assert 'parent' in lower

    def test_source_target_rule(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        lower = DRAW_PROMPT_TEMPLATE.lower()
        assert 'source' in lower
        assert 'target' in lower


class TestLandscapeCanvas:
    """Scenario 6: 横向画布"""

    def test_page_width_gte_page_height(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        width_match = re.search(r'pageWidth="(\d+)"', DRAW_PROMPT_TEMPLATE)
        height_match = re.search(r'pageHeight="(\d+)"', DRAW_PROMPT_TEMPLATE)
        assert width_match and height_match, 'pageWidth or pageHeight not found'
        width = int(width_match.group(1))
        height = int(height_match.group(1))
        assert width >= height, f'Canvas not landscape: {width}x{height}'


class TestLayoutPatterns:
    """布局系统按图表类型区分"""

    def test_top_down_for_architecture(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        lower = DRAW_PROMPT_TEMPLATE.lower()
        # Architecture should mention top-down or vertical layering
        assert ('top' in lower and ('down' in lower or 'bottom' in lower)
                or '上' in DRAW_PROMPT_TEMPLATE and '下' in DRAW_PROMPT_TEMPLATE
                or 'layer' in lower)

    def test_left_right_for_dataflow(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        lower = DRAW_PROMPT_TEMPLATE.lower()
        assert ('left' in lower and 'right' in lower
                or '左' in DRAW_PROMPT_TEMPLATE and '右' in DRAW_PROMPT_TEMPLATE)


class TestFewShotExample:
    """Prompt 中包含完整示例"""

    def test_has_example_section(self):
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        lower = DRAW_PROMPT_TEMPLATE.lower()
        assert ('example' in lower or 'few-shot' in lower
                or '示例' in DRAW_PROMPT_TEMPLATE or '参考' in DRAW_PROMPT_TEMPLATE)

    def test_example_contains_edge_with_label(self):
        """Example should demonstrate edge labels"""
        from pactkit.prompts import DRAW_PROMPT_TEMPLATE
        # Look for an edge mxCell that has both edge="1" and a non-empty value
        edge_with_value = re.search(
            r'<mxCell[^>]*edge="1"[^>]*value="[^"]+"', DRAW_PROMPT_TEMPLATE
        ) or re.search(
            r'<mxCell[^>]*value="[^"]+"[^>]*edge="1"', DRAW_PROMPT_TEMPLATE
        )
        assert edge_with_value, 'Example should contain an edge with a label (value attribute)'
