from dataclasses import dataclass
from enum import Enum
from typing import Sequence, List, Optional


@dataclass
class Version:
    major: int
    minor: int
    patch: int

    def __lt__(self, other):
        if isinstance(other, Version):
            if self.major != other.major:
                return self.major < other.major
            else:
                if self.minor != other.minor:
                    return self.minor < other.minor
                else:
                    return self.patch < other.patch

        return False

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


class VersionLevel(Enum):
    Major = 0
    Minor = 1
    Patch = 2


def get_versions(version_strings: Sequence[str]) -> List[Version]:
    """
    Returns the sorted versions (from low to high) with duplicates removed
    """

    def to_version(ver_str: str):
        try:
            s = ver_str.split(".")

            return Version(int(s[0]), int(s[1]), int(s[2]))
        except:
            return None

    ret_val = []
    for vs in version_strings:
        ver = to_version(vs)
        if ver is not None:
            ret_val.append(ver)

    ret_val.sort()
    idx = 0
    while idx + 1 < len(ret_val):
        if ret_val[idx] == ret_val[idx + 1]:
            del ret_val[idx + 1]
        else:
            idx += 1

    return ret_val


def get_previous(
    v: Version, vs: Sequence[Version], level: VersionLevel
) -> Optional[Version]:
    candidate = None
    if level == VersionLevel.Major:

        def test(v, elm):
            return v.major > elm.major

    elif level == VersionLevel.Minor:

        def test(v, elm):
            return v.major == elm.major and v.minor > elm.minor

    elif level == VersionLevel.Patch:

        def test(v, elm):
            return v.major == elm.major and v.minor == elm.minor and v.patch > elm.patch

    else:

        def test(_v, _elm):
            return False

    for elm in vs:
        if test(v, elm):
            if candidate is None or candidate < elm:
                candidate = elm

    return candidate


def get_latest_release(vs: Sequence[Version]) -> Optional[Version]:
    candidate = None
    for v in vs:
        if candidate is None or candidate < v:
            candidate = v
    return candidate


def last_minor_releases(frame):
    """
    :return: a set of strings containing all distinct 'major.minor' versions with the biggest patch number
    """
    ver_dict = {}
    for version in frame["version"]:
        ver, patch = _split_version(version)
        if ver is None:
            continue  # skip invalid versions
        current = ver_dict.get(ver, 0)
        if patch > current:
            ver_dict[ver] = patch

    return {f"{k}.{v}" for k, v in ver_dict.items()}


def _split_version(release: str):
    r = release.split(".")
    try:
        return f"{r[0]}.{r[1]}", int(r[2])
    except:
        return None, None
