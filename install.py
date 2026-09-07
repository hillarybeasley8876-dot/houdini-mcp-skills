"""Install the portable Houdini package; generate, never overwrite, client config."""
from pathlib import Path
import argparse, datetime, json, os, shutil, struct, subprocess, sys

ROOT = Path(__file__).resolve().parent

def backup(path):
    if path.exists():
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        target = ROOT / 'backups' / stamp / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            shutil.copytree(path, target)
        else:
            shutil.copy2(path, target)
        print('Backup:', target)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--houdini-pref-dir', required=True, type=Path)
    ap.add_argument('--skills-dir', type=Path, default=Path.home()/'.agents/skills')
    ap.add_argument('--port', type=int, default=9877)
    ap.add_argument('--online', action='store_true', help='Use pip index instead of bundled wheels')
    ap.add_argument('--skip-skills', action='store_true')
    args = ap.parse_args()
    if os.name != 'nt' or sys.version_info[:2] != (3,12) or struct.calcsize('P') != 8:
        ap.error('Run with Windows x64 Python 3.12 (py -3.12 install.py ...)')
    if not 1024 <= args.port <= 65535:
        ap.error('port must be between 1024 and 65535')
    plugin = ROOT/'houdini-mcp'
    env = plugin/'.venv'
    python = env/'Scripts/python.exe'
    if not python.exists():
        subprocess.run([sys.executable,'-m','venv',str(env)],check=True)
    pip_args=[str(python),'-m','pip','install','--disable-pip-version-check']
    if not args.online:
        wheels=ROOT/'dependencies/wheels-win64-py312'
        if not list(wheels.glob('*.whl')):
            ap.error('Bundled wheels not found; use --online with an Internet connection')
        pip_args += ['--no-index','--find-links',str(wheels)]
    subprocess.run(pip_args+['-r',str(plugin/'requirements.lock.txt')],check=True)
    subprocess.run([str(python),'-m','pip','check'],check=True)
    package=args.houdini_pref_dir.expanduser().resolve()/'packages/houdinimcp.json'
    package.parent.mkdir(parents=True,exist_ok=True)
    backup(package)
    package.write_text(json.dumps({'enable':True,'load_package_once':True,'hpath':plugin.as_posix(),
        'env':[{'HOUDINI_MCP_ROOT':plugin.as_posix()},{'HOUDINI_MCP_PORT':str(args.port)}]},indent=2)+'\n',encoding='utf-8')
    bridge=plugin/'scripts/python/houdinimcp/houdini_mcp_server.py'
    generated=ROOT/'config/generated'
    generated.mkdir(parents=True,exist_ok=True)
    # JSON basic strings are also valid TOML strings for these Windows paths.
    snippet='[mcp_servers.houdini]\ncommand = '+json.dumps(str(python))+'\nargs = '+json.dumps([str(bridge),'--port',str(args.port)])+'\n'
    (generated/'codex.houdini.toml').write_text(snippet,encoding='utf-8')
    (generated/'claude-desktop.mcp.json').write_text(json.dumps({'mcpServers':{'houdini':{
        'command':str(python),'args':[str(bridge),'--port',str(args.port)]}}},indent=2)+'\n',encoding='utf-8')
    (generated/'claude-code.houdini.json').write_text(json.dumps({'type':'stdio','command':str(python),'args':[str(bridge),'--port',str(args.port)]},indent=2)+'\n',encoding='utf-8')
    if not args.skip_skills:
        dest=args.skills_dir.expanduser().resolve()
        for source in sorted((ROOT/'skills').iterdir()):
            if not (source/'SKILL.md').exists():
                continue
            target=dest/source.name
            if target.resolve()==source.resolve():
                ap.error('skills-dir must not be the bundle skills directory')
            backup(target)
            shutil.copytree(source,target,dirs_exist_ok=True)
        print('Skills:',dest)
    print('Houdini package:',package)
    print('Merge only the houdini entry from:',generated)
    print('Restart Houdini and your MCP client. Keep this bundle at its current path.')

if __name__ == '__main__':
    main()
