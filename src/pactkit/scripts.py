# pactkit/scripts.py
# 存放要注入到用户 ~/.claude/scripts/ 下的工具源码

TASK_MANAGER_CODE = r"""#!/usr/bin/env python3
import sys
import re
import os
import argparse
from pathlib import Path

def update_task(board_path, story_id, task_name):
    # Expand user path (e.g. ~)
    path = Path(board_path).expanduser().resolve()
    if not path.exists():
        print(f"Error: {board_path} not found.")
        sys.exit(1)

    content = path.read_text(encoding='utf-8')

    # 1. 定位 Story (### [STORY-ID])
    story_pattern = rf"(### \[{re.escape(story_id)}\].*?)(?=\n### |$)"
    story_match = re.search(story_pattern, content, re.DOTALL)

    if not story_match:
        print(f"Error: Story {story_id} not found.")
        sys.exit(1)

    story_block = story_match.group(1)

    # 2. 定位并替换 Task (- [ ] Task Name)
    task_pattern = rf"(\-\s*\[\s*\]\s*{re.escape(task_name)})"

    if not re.search(task_pattern, story_block):
        # Check if already done
        if re.search(rf"(\-\s*\[x\]\s*{re.escape(task_name)})", story_block, re.IGNORECASE):
            print(f"Info: Task '{task_name}' is already marked as done.")
            sys.exit(0)
        print(f"Error: Task '{task_name}' not found in {story_id}.")
        sys.exit(1)

    # 3. 内存替换
    new_story_block = re.sub(task_pattern, f"- [x] {task_name}", story_block, count=1)
    new_content = content.replace(story_block, new_story_block)

    # 4. 原子写入
    tmp_path = path.with_suffix('.tmp')
    tmp_path.write_text(new_content, encoding='utf-8')
    os.replace(tmp_path, path)

    print(f"Success: Marked '{task_name}' as done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", default="docs/product/sprint_board.md")
    parser.add_argument("--story", required=True)
    parser.add_argument("--task", required=True)
    args = parser.parse_args()

    update_task(args.board, args.story, args.task)
"""

# DEPRECATED: archive logic has been migrated to TOOLS_SOURCE (prompts.py::archive_stories).
# Kept for reference only. See STORY-003.
ARCHIVER_CODE = r"""#!/usr/bin/env python3
import sys
import re
import os
import datetime
from pathlib import Path

def archive_completed():
    board_path = Path("docs/product/sprint_board.md")
    archive_dir = Path("docs/product/archive")

    if not board_path.exists():
        return

    content = board_path.read_text(encoding='utf-8')

    # Split stories
    parts = re.split(r'(?=^### \[STORY)', content, flags=re.MULTILINE)

    active_parts = []
    archived_parts = []

    header = parts[0]
    active_parts.append(header)

    for part in parts[1:]:
        # 如果包含 "- [ ]" 则说明未完成，保留
        if "- [ ]" in part:
            active_parts.append(part)
        else:
            archived_parts.append(part)

    if not archived_parts:
        print("No completed stories to archive.")
        sys.exit(0)

    # 写入归档
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m")
    archive_file = archive_dir / f"archive_{timestamp}.md"

    with open(archive_file, "a", encoding='utf-8') as f:
        for part in archived_parts:
            f.write("\n" + part.strip() + "\n")

    # 重写 Board
    new_content = "".join(active_parts)
    # 去除多余空行 (超过3个换行符变成2个)
    new_content = re.sub(r'\n{3,}', '\n\n', new_content)

    tmp_path = board_path.with_suffix('.tmp')
    tmp_path.write_text(new_content, encoding='utf-8')
    os.replace(tmp_path, board_path)

    print(f"🧹 Archived {len(archived_parts)} stories to {archive_file}")

if __name__ == "__main__":
    archive_completed()
"""
