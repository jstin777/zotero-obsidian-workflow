#!/usr/bin/env python3
"""Check the tracked release surface, never enumerate private research content."""
import json
from pathlib import Path
import re
import subprocess
import sys
import yaml
root=Path(__file__).resolve().parents[1]
paths=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0');paths=[p for p in paths if p]
allowed_roots={'workflow','tools','tests','docs','examples','templates','dashboards','.github','.obsidian'}
allowed_top={'README.md','AGENTS.md','LICENSE','THIRD_PARTY.md','CHANGELOG.md','requirements.txt','config.example.json','.gitignore','.gitattributes'}
errors=[]
for name in paths:
 p=root/name;parts=Path(name).parts
 if len(parts)==1:
  if name not in allowed_top:errors.append('Unexpected top-level file: '+name)
 elif parts[0] not in allowed_roots and name not in ('papers/.gitkeep','notes/.gitkeep','zotero-notes/.gitkeep','sources/.gitkeep'):
  errors.append('Unexpected release path: '+name)
 if any(x in parts for x in ('.workflow','.venv','.marker-venv','node_modules','__pycache__')) or name.endswith('.local.json'):
  errors.append('Private/runtime path: '+name)
 if p.is_symlink():errors.append('Release symlink: '+name)
 if p.suffix=='.pdf':
  if name!='examples/demonstration.pdf':errors.append('Unexpected PDF: '+name)
  continue
 try:text=p.read_text()
 except UnicodeDecodeError:errors.append('Unexpected binary: '+name);continue
 for pattern in (r'/' + r'Users/[^\s/]+/',r'gh[pousr]_[A-Za-z0-9]{25,}',r'sk-[A-Za-z0-9]{25,}',r'BEGIN (?:RSA |OPENSSH )?PRIVATE KEY'):
  if re.search(pattern,text):errors.append('Possible personal path/secret in '+name)
 if p.suffix=='.json':
  try:json.loads(text)
  except ValueError:errors.append('Invalid JSON: '+name)
 if p.suffix in ('.yaml','.yml','.base'):
  try:yaml.safe_load(text)
  except yaml.YAMLError:errors.append('Invalid YAML: '+name)
 if p.suffix=='.md':
  for target in re.findall(r'\]\(([^)]+)\)',text):
   if '://' in target or target.startswith('#') or target.startswith('mailto:'):continue
   dest=target.split('#',1)[0]
   if dest and not (p.parent/dest).exists():errors.append('Broken local Markdown link in '+name+': '+target)
print(json.dumps({'tracked_files':len(paths),'errors':errors},indent=2))
sys.exit(bool(errors))
