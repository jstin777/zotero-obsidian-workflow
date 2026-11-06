#!/usr/bin/env python3
"""Install the pinned official QMD SDK and its native runtime privately."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request

import yaml

COMMIT = '93d211f9ef4a869a9aed0d075ca767dda552627f'
VERSION = '2.8.3'
ARCHIVE_SHA256 = '2683e5a96414b04b70b1f3c250e2b92193352398afad9ab6df208396a3b94f30'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', required=True, type=Path)
    parser.add_argument('--pnpm', required=True, type=Path)
    args = parser.parse_args()
    vault = Path(__file__).resolve().parent.parent
    runtime = vault / '.workflow/qmd-runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    builds = {name: True for name in ('better-sqlite3','node-llama-cpp','tree-sitter-go','tree-sitter-rust','tree-sitter-python','tree-sitter-typescript')}
    builds['tree-sitter-javascript'] = False
    (runtime / 'pnpm-workspace.yaml').write_text(yaml.safe_dump({'allowBuilds': builds}))
    env = dict(os.environ, PATH=str(args.node.resolve().parent) + os.pathsep + os.environ.get('PATH', ''))
    url = 'https://codeload.github.com/tobi/qmd/tar.gz/' + COMMIT
    raw = urllib.request.urlopen(url, timeout=60).read()
    if hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('Pinned QMD source archive checksum changed')
    sdk = runtime / 'sdk'
    sdk.mkdir(exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts[1:]
            if not parts:
                continue
            target = sdk.joinpath(*parts)
            if not target.resolve().is_relative_to(sdk.resolve()) or member.issym() or member.islnk():
                raise ValueError('Unsafe source archive member')
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
    source_package = json.loads((sdk / 'package.json').read_text())
    dependencies = dict(source_package['dependencies'])
    dependencies['better-sqlite3'] = '13.0.3'
    dependencies.update({'typescript': '5.9.3', '@types/node': '24.10.1', '@types/better-sqlite3': '7.6.13'})
    package = {'private': True, 'type': 'module', 'dependencies': dependencies,
        'optionalDependencies': source_package['optionalDependencies']}
    (runtime / 'package.json').write_text(json.dumps(package, indent=2) + '\n')
    shutil.copyfile(Path(__file__).with_name('qmd-pnpm-lock.yaml'), runtime / 'pnpm-lock.yaml')
    subprocess.run([str(args.pnpm.resolve()), '--dir', str(runtime), 'install', '--frozen-lockfile'], env=env, check=True)
    modules = sdk / 'node_modules'
    if not modules.exists():
        modules.symlink_to('../node_modules', target_is_directory=True)
    subprocess.run([str(args.node.resolve()), 'scripts/build.mjs'], cwd=sdk, env=env, check=True)
    provenance = {'version': VERSION, 'commit': COMMIT, 'archive_sha256': hashlib.sha256(raw).hexdigest(), 'source_url': url}
    (runtime / 'build.json').write_text(json.dumps(provenance, indent=2) + '\n')
    config_path = vault / 'config.local.json'
    config = json.loads(config_path.read_text())
    config['qmd'] = {'enabled': True, 'node': str(args.node.resolve()), 'runtime': '.workflow/qmd-runtime',
        'build': COMMIT, 'default_method': 'semantic', 'timeout': 1800}
    config_path.write_text(json.dumps(config, indent=2) + '\n')
    print(json.dumps({'installed': provenance, 'next': '.venv/bin/python tools/workflow.py index --semantic'}, indent=2))


if __name__ == '__main__':
    main()
