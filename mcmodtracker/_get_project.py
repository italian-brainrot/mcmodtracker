import datetime
import json
import os, shutil
from collections.abc import Sequence

import requests

from ._common import HEADERS, Loader

GETPROJECT_BASE_URL = "https://api.modrinth.com/v2/project"

def getproject(id_or_slug: str, timeout:float=30) -> dict:
    # https://docs.modrinth.com/api/operations/getproject/
    response = requests.get(f"{GETPROJECT_BASE_URL}/{id_or_slug}", headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    if response.status_code != 200:
        raise RuntimeError(f"request failed with status code {response.status_code}")

    return response.json()

GETPROJECTS_BASE_URL = "https://api.modrinth.com/v2/projects"

def getprojects(ids_or_slugs: Sequence[str], timeout:float=30) -> list[dict]:
    # https://docs.modrinth.com/api/operations/getprojects/
    if isinstance(ids_or_slugs, str):
        raise RuntimeError(f'"{ids_or_slugs}" is a string, use `getproject`.')

    response = requests.get(
        f"{GETPROJECTS_BASE_URL}",
        params={"ids": json.dumps(list(ids_or_slugs))},
        headers=HEADERS,
        timeout=timeout,
    )
    response.raise_for_status()
    if response.status_code != 200:
        raise RuntimeError(f"request failed with status code {response.status_code}")

    return response.json()


def getprojectversions(
    id_or_slug: str,
    loaders: Loader | Sequence[Loader] | None = None,
    game_versions: str | Sequence[str] | None = None,
    timeout: float = 30,
) -> list[dict]:
    params = {}

    if loaders is not None:
        if isinstance(loaders, str): loaders = [loaders]
        params["loaders"] = json.dumps(loaders)

    if game_versions is not None:
        if isinstance(game_versions, str): game_versions = [game_versions]
        params["game_versions"] = json.dumps(game_versions)

    response = requests.get(
        f'{GETPROJECT_BASE_URL}/{id_or_slug}/version',
        params=params,
        headers=HEADERS,
        timeout=timeout,
    )
    response.raise_for_status()
    if response.status_code != 200:
        raise RuntimeError(f"request failed with status code {response.status_code}")

    return response.json()


def get_latest_version(
    id_or_slug: str,
    loaders: Loader | Sequence[Loader] | None = None,
    game_versions: str | Sequence[str] | None = None,
    timeout: float = 30,
) -> dict | None:
    versions = getprojectversions(id_or_slug=id_or_slug, loaders=loaders, game_versions=game_versions, timeout=timeout)
    if len(versions) == 0: return None

    return sorted(versions, key=lambda d: datetime.datetime.fromisoformat(d["date_published"]))[-1]

def download_version(version: dict, file: str | os.PathLike, timeout=30) -> None:
    url = version["files"][0]["url"]

    # --------------------------------- download --------------------------------- #
    response = requests.get(url, stream=True, timeout=timeout)
    response.raise_for_status()
    if response.status_code != 200:
        raise RuntimeError(f"request failed with status code {response.status_code}")

    # ----------------------------------- save ----------------------------------- #
    with open(file, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file) # type:ignore
