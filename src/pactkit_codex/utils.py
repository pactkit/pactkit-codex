import os


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(content, encoding='utf-8')
    os.replace(tmp, path)
    print(f'   -> Wrote {path.name}')
