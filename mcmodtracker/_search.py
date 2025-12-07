import json
from collections.abc import Iterable, Sequence
from typing import Literal

import requests

from ._common import HEADERS, Category, Index, Loader, ProjectType

SEARCH_BASE_URL = "https://api.modrinth.com/v2/search"


def _get_tags(tag: Literal["project_type", "category", "loader", "game_version"]):
    return requests.get(f"https://api.modrinth.com/v2/tag/{tag}", timeout=30).json()

def _tree_map(s, fn):
    if isinstance(s, str) or (not isinstance(s, Iterable)): return fn(s)
    return [_tree_map(el, fn) for el in s]

def _ensure_list_of_list(x) -> list[list[str]]:
    if x is None: return []
    if isinstance(x, str): return [[x]]
    if isinstance(x[0], str): return [list(x)]
    return [list(el) for el in x]

def search(
    query: str,
    project_type: ProjectType,
    categories: Category | Sequence[Category] | Sequence[Sequence[Category]] | None = None,
    versions: str | Sequence[str] | Sequence[Sequence[str]] | None = None,
    loaders: Loader | Sequence[Loader] | Sequence[Sequence[Loader]] | None = None,
    title: str | None = None,
    author: str | None = None,
    project_id: str | None = None,
    index: Index | None = None,
    limit: int | None = None,
    timeout: float = 30,
):
    """
    - OR: All elements in a single array are considered to be joined by OR statements. For example, the search ``[["technology", "transportation"]]`` translates to Projects with "technology" OR "transportation" tags.

    - AND: All elements in a single array are considered to be joined by OR statements. For example, the search ``[["technology"], ["transportation"]]`` translates to Projects with "technology" AND "transportation" tags.
    """
    # create facets
    facets: list[list[str]] = [[f"project_type:{project_type}"]]

    # -------------------------------- categories -------------------------------- #
    # loaders are lumped in with categories in search
    categories = _ensure_list_of_list(categories)
    loaders = _ensure_list_of_list(loaders)

    # add with "categories:" prefix
    facets.extend(_tree_map(categories + loaders, fn=lambda s: f'categories:{s}'))

    # --------------------------------- versions --------------------------------- #
    versions = _ensure_list_of_list(versions)
    facets.extend(_tree_map(versions, fn=lambda s: f'versions:{s}'))

    # ------------------------------- other facets ------------------------------- #
    if title is not None: facets.append([f'title:{title}'])
    if author is not None: facets.append([f'author:{author}'])
    if project_id is not None: facets.append([f'project_id:{project_id}'])

    # ---------------------------------- params ---------------------------------- #
    params: dict = {
        "query": query,
        "facets": json.dumps(facets),
    }

    if index is not None: params["index"] = index
    if limit is not None: params["limit"] = limit

    # ------------------------------ get a response ------------------------------ #
    response = requests.get(SEARCH_BASE_URL, params=params, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    if response.status_code != 200:
        raise RuntimeError(f"request failed with status code {response.status_code}")

    return response.json()

