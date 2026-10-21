from pathlib import Path
import json
import re
import sys
import yaml


def inspect_groups(root, skills):
    path = root / '.claude-plugin/marketplace.json'
    try:
        manifest = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        return [f'{path}: {error}']
    if not isinstance(manifest, dict) or not isinstance(manifest.get('plugins'), list):
        return [f'{path}: plugins must be a list']
    errors = []
    known = {entry.parent.resolve() for entry in skills}
    grouped = set()
    names = set()
    root = root.resolve()

    def relative_path(base, value):
        if not isinstance(value, str) or not value.startswith('./'):
            errors.append(f'{path}: expected ./ relative path, got {value!r}')
            return None
        target = (base / value).resolve()
        if not target.is_relative_to(root):
            errors.append(f'{path}: path escapes repository: {value}')
            return None
        return target

    for plugin in manifest['plugins']:
        if not isinstance(plugin, dict):
            errors.append(f'{path}: group must be an object')
            continue
        name = plugin.get('name')
        if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
            errors.append(f'{path}: invalid group name {name!r}')
        elif name in names:
            errors.append(f'{path}: duplicate group {name}')
        else:
            names.add(name)
        base = relative_path(root, plugin.get('source'))
        members = plugin.get('skills')
        if not isinstance(members, list) or not members:
            errors.append(f'{path}: group {name} must declare its skills')
            continue
        if base is None:
            continue
        for member in members:
            target = relative_path(base, member)
            if target is None:
                continue
            if target not in known:
                errors.append(f'{path}: unknown skill {member}')
            elif target in grouped:
                errors.append(f'{path}: skill appears in multiple groups: {member}')
            else:
                grouped.add(target)
    for target in sorted(known - grouped):
        errors.append(f'{path}: skill has no group: {target.name}')
    return errors


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
        metadata = front.get('metadata')
        if isinstance(metadata, dict) and metadata.get('internal') is True:
            errors.append(f'{entry}: grouped skills must be visible to the installer')
        # Index destinations are on a single line; <> allows filename parentheses.
        for file in entry.parent.rglob('*.md'):
            for line in file.read_text().splitlines():
                for m in re.finditer(r'\[[^\]\n]+\]\((<[^>]+>|[^)]+)\)', line):
                    dest = m[1].strip('<>')
                    if ':' in dest or dest.startswith(('#', '/', '~', '<')):
                        continue
                    path = dest.split('#')[0]
                    if path and not (file.parent / path).exists():
                        errors.append(f'{file}: missing {dest}')
    return errors + inspect_groups(root, skills)


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = inspect(root)
    if errors:
        print('\n'.join(errors))
        sys.exit(1)
    print(f'Validated {len(list((root / "skills").glob("*/SKILL.md")))} skill entries, indexes and groups')
