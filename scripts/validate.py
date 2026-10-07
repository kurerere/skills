from pathlib import Path
import re
import sys
import yaml


def inspect(root):
    errors = []
    skills = list((root / 'skills').glob('*/SKILL.md'))
    if not skills:
        return ['No skills found']
    allowed = {'name', 'description', 'metadata', 'license', 'allowed-tools',
               'disable-model-invocation', 'argument-hint', 'user-invocable'}
    for entry in skills:
        text = entry.read_text()
        match = re.match(r'^---\n(.*?)\n---(?:\n|$)', text, re.S)
        if not match:
            errors.append(f'{entry}: missing frontmatter')
            continue
        try:
            front = yaml.safe_load(match[1])
        except yaml.YAMLError as error:
            errors.append(f'{entry}: {error}')
            continue
        if not isinstance(front, dict):
            errors.append(f'{entry}: frontmatter is not a mapping')
            continue
        name = front.get('name', '')
        description = front.get('description', '')
        if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or name != entry.parent.name or len(name) > 64:
            errors.append(f'{entry}: invalid or mismatched name')
        if not isinstance(description, str) or not description.strip() or len(description) > 1024:
            errors.append(f'{entry}: invalid description')
        if set(front) - allowed:
            errors.append(f'{entry}: unsupported fields {set(front)-allowed}')
        # Index destinations are on a single line; <> allows filename parentheses.
        for file in [entry, *entry.parent.glob('references/sitemap.md')]:
            for line in file.read_text().splitlines():
                for m in re.finditer(r'\[[^\]\n]+\]\((<[^>]+>|[^)]+)\)', line):
                    dest = m[1].strip('<>')
                    if ':' in dest or dest.startswith(('#', '/', '~', '<')):
                        continue
                    path = dest.split('#')[0]
                    if path and not (file.parent / path).exists():
                        errors.append(f'{file}: missing {dest}')
    return errors


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = inspect(root)
    if errors:
        print('\n'.join(errors))
        sys.exit(1)
    print(f'Validated {len(list((root / "skills").glob("*/SKILL.md")))} skill entries and indexes')
