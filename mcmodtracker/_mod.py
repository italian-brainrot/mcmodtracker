"""this for scanning local MOD"""
import warnings
import os
import shutil
import tempfile
import tomllib
from pathlib import Path
import yaml as yaml_

import ruamel.yaml
from ._get_project import get_latest_version, download_version, getproject
from ._common import Loader
from ._scanner import is_mcreator_mod, uses_mcfunction


def yamlread(file: str | os.PathLike) -> dict:
    yaml = ruamel.yaml.YAML(typ='safe')
    with open(file, 'r', encoding = 'utf8') as f:
        r = yaml.load(f)
        if r is None: r = {}
        return r

def _reorder_dict(d: dict, key_order):
    proc = d.copy()
    for k in key_order:
        if k in d:
            proc[k] = d[k]
    return proc

def yamlwrite(file: str | os.PathLike, d: dict, ):#, sequence = 4, offset = 2):
    # yaml = ruamel.yaml.YAML()
    # yaml.indent(sequence=sequence, offset=offset)
    with open(file, 'w', encoding = 'utf8') as f:
        yaml_.dump(d, f, sort_keys=False, default_flow_style=False)

class MOD:
    def __init__(self, jar: str | os.PathLike):
        if not str(jar).lower().endswith(".jar"):
            raise RuntimeError(f"got {jar=} it doesnt have JAR extension")

        self.jar = Path(jar)

        with tempfile.TemporaryDirectory() as tmpdir:
            contents = Path(tmpdir) / "contents"
            shutil.unpack_archive(jar, contents, format='zip')

            manifest = contents / "META-INF" / "neoforge.mods.toml"
            if not manifest.is_file():
                raise RuntimeError(f"mcmodtracker currently only support NeoForge MOD and {jar} is not NeoForge")

            with open(manifest, "rb") as f:
                data = tomllib.load(f)

            self.manifest = data
            self.modId = data["mods"][0]["modId"]
            self.version = data["mods"][0]["version"]
            self.displayName = data["mods"][0]["displayName"]

    def __repr__(self):
        return f'MOD(modId={self.modId}, version={self.version}, displayName="{self.displayName}")'

# ----------------------------- add slug to modid ---------------------------- #
ROOT = Path(os.path.dirname(__file__))
_SLUG_TO_MODID_PATH = ROOT / "__SLUG_TO_MODID.txt"
if not _SLUG_TO_MODID_PATH.exists():
    with open(_SLUG_TO_MODID_PATH, "w", encoding='utf-8') as _slug_to_modid:
        _slug_to_modid.write("")

SLUG_TO_MODID: dict[str, str] = {}
with open(_SLUG_TO_MODID_PATH, "r", encoding='utf-8') as _slug_to_modid:
    for line in _slug_to_modid.readlines():
        if len(line.strip()) == 0: continue
        key, value = line.strip().split("/")
        SLUG_TO_MODID[key.strip()] = value.strip()

# ---------------------------- add slug to version --------------------------- #
_SLUG_TO_VERSION_PATH = ROOT / "__SLUG_TO_VERSION.yaml"
if not _SLUG_TO_VERSION_PATH.exists():
    with open(_SLUG_TO_VERSION_PATH, "w", encoding='utf-8') as _slug_to_version:
        _slug_to_version.write("")

SLUG_TO_VERSIONS = yamlread(_SLUG_TO_VERSION_PATH)
KEY_ORDER = ("url", "modId", "title", "summary", "description", "good")


def MOD_str(mod_str, yaml: dict):
    title = yaml.get("title", mod_str)
    txt = f"{f' {title} '.center(76, '-')}"
    txt = f"# {txt} #\n"
    txt = f"{txt}{mod_str}:\n"

    def addline(k):
        if k in yaml: return f"{txt}  {k}: {yaml[k].replace(":", "").replace("'", "").replace('"', "")}\n"
        return txt

    txt = addline("url")
    txt = addline("modId")
    txt = addline("title")
    txt = addline("summary")

    if "title" in yaml: txt = f'{txt}\n'
    txt = addline("description")
    txt = addline("good")
    return f"{txt}\n"

# ---------------------------------- analyze --------------------------------- #
def 恒等函数(X):return(X)
def analyze_mods(db_dir: str | os.PathLike, mod_dir: str | os.PathLike, game_version: str, loader: Loader | str, pbar=恒等函数):
    db_dir = Path(db_dir)
    mod_dir = Path(mod_dir)

    yaml_paths = [f for f in db_dir.iterdir() if str(f).lower().endswith((".yaml", ".yml"))]
    yamls = {p: yamlread(p) for p in yaml_paths}

    all_mod = [(yaml_path, mod_str) for yaml_path, yaml in yamls.items() for mod_str in yaml]

    # check duplicate
    all_mod_str = {}
    for yaml_path, yaml in yamls.items():
        mod_strs = list(yaml.keys())
        for mod_str in mod_strs:
            if mod_str in all_mod_str:
                print(f"WARNING duplicate MOD in {yaml_path.name} and {all_mod_str[mod_str].name}")
            all_mod_str[mod_str] = yaml_path

    # i download all MOD？ to get modId
    # add modIds
    print("-----------DOWNLOADING MOD INFO-----------")
    for yaml_path, mod_str in pbar(all_mod):

        site, slug = mod_str.split("/")
        if site != "modrinth":
            print(f"WARNING unsupported SITE in {mod_str}")
            continue

        # load modId
        mod_dict = yamls[yaml_path][mod_str]

        project = None
        if "title" not in mod_dict:
            project = getproject(slug)
            mod_dict["url"] = f'https://modrinth.com/mod/{slug}'
            mod_dict["summary"] = project.get("description", "NO_DESCRIPTION")
            mod_dict["title"] = project.get("title", "NO_TITLE")
            # yamlwrite(yaml_path, {k: _reorder_dict(v, KEY_ORDER) for k, v in yamls[yaml_path].items()})
            text = "\n".join([MOD_str(k, d) for k, d in yamls[yaml_path].items()])
            with open(yaml_path, "w", encoding='utf-8') as f:
                f.write(text)

        if "modId" not in mod_dict:

            # load from SLUG to modId
            if slug in SLUG_TO_MODID:
                mod_dict["modId"] = SLUG_TO_MODID[slug]

            # download Modrinth
            else:
                version = get_latest_version(slug, loaders=loader, game_versions=game_version)
                if version is None:
                    continue # no version for game version and loader

                with tempfile.TemporaryDirectory() as tmpdir:
                    # download MOD
                    tmpfile = Path(tmpdir) / "MOD.jar"

                    try:
                        download_version(version, file=tmpfile)
                        mod = MOD(tmpfile)
                    except Exception as e:
                        warnings.warn(f"fail when download MOD {slug}: {e}")
                        continue

                    # update SLUG to modId
                    SLUG_TO_MODID[slug] = mod.modId
                    with open(_SLUG_TO_MODID_PATH, "a", encoding='utf-8') as f:
                        f.write(f"\n{slug}/{mod.modId}")

                    # update YAML
                    mod_dict["modId"] = mod.modId
                    if project is None: project = getproject(slug)
                    mod_dict["url"] = f'https://modrinth.com/mod/{slug}'
                    mod_dict["summary"] = project.get("description", "NO_DESCRIPTION")
                    mod_dict["title"] = project.get("title", "NO_TITLE")
                    # yamlwrite(yaml_path, {k: _reorder_dict(v, KEY_ORDER) for k, v in yamls[yaml_path].items()})

                    text = "\n".join([MOD_str(k, d) for k, d in yamls[yaml_path].items()])
                    with open(yaml_path, "w", encoding='utf-8') as f:
                        f.write(text)

    # add all MOD
    print("\n-----------LOADING MOD-----------")
    mods = {}
    for jar in pbar(list(mod_dir.iterdir())):
        if jar.is_file() and str(jar).lower().endswith(".jar"):
            try:
                mod = MOD(jar)
                mods[mod.modId] = mod
            except Exception as e:
                print(f"fail when load MOD {os.path.basename(jar)}: {e}")

    print("\n-----------SCAN-----------")
    # check MC Creater MOD and MC Function MOD
    for mod in mods.values():
        is_mcreator, msg = is_mcreator_mod(mod.jar)
        if is_mcreator: print(f'DETECT MC CREATER MOD: {mod.displayName} "{mod.jar.name}" {msg}')
        if uses_mcfunction(mod.jar): print(f'DETECT MC FUNCTION MOD {mod.displayName}: "{mod.jar.name}"')

    # check installed MOD
    print("\n-----------CHECKING INSTALLED MOD-----------")
    for yaml_path, mod_str in all_mod:
        mod_dict = yamls[yaml_path][mod_str]
        if "modId" not in mod_dict: continue
        site, slug = mod_str.split("/")
        if mod_dict['modId'] not in mods:
            if mod_dict.get("good", True):
                if slug in SLUG_TO_VERSIONS:
                    if f"{game_version}/{loader}" in SLUG_TO_VERSIONS[slug]:
                        print(f"{yaml_path.name}: MOD {mod_dict['title']} is available: {mod_dict['url']}")

                else:
                    latest = get_latest_version(slug, loaders=loader, game_versions=game_version)
                    if latest is None: continue
                    if slug not in SLUG_TO_VERSIONS: SLUG_TO_VERSIONS[slug] = []
                    SLUG_TO_VERSIONS[slug].append(f"{game_version}/{loader}")
                    yamlwrite(_SLUG_TO_VERSION_PATH, SLUG_TO_VERSIONS)
                    print(f"{yaml_path.name}: MOD {mod_dict['title']} is available: {mod_dict['url']}")

        if mod_dict['modId'] in mods:
            if mod_dict.get("good", True) is False:
                print(f"{yaml_path.name}: bad MOD {mod_dict['title']} is installed: {mods[mod_dict['modId']].jar}")

    print("-----------DONE-----------")
