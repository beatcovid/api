import glob
import os
from pprint import pprint

import polib
from django.core.management.base import CommandError
from django.core.management.utils import find_command, is_ignored_path


def find_locale_paths():
    ignore_patterns = set([".venv/*"])

    basedirs = [os.path.join("conf", "locale"), "locale"]

    if os.environ.get("DJANGO_SETTINGS_MODULE"):
        from django.conf import settings

        basedirs.extend(settings.LOCALE_PATHS)

    # Walk entire tree, looking for locale directories
    for dirpath, dirnames, filenames in os.walk(".", topdown=True):
        for dirname in dirnames:
            if is_ignored_path(
                os.path.normpath(os.path.join(dirpath, dirname)), ignore_patterns
            ):
                dirnames.remove(dirname)
            elif dirname == "locale":
                basedirs.append(os.path.join(dirpath, dirname))

    # Gather existing directories.
    basedirs = set(map(os.path.abspath, filter(os.path.isdir, basedirs)))

    if not basedirs:
        raise CommandError(
            "This script should be run from the Django Git "
            "checkout or your project or app tree, or with "
            "the settings module specified."
        )

    # Build locale list
    locales = []
    for basedir in basedirs:
        # default en as base
        locale_dirs = filter(os.path.isdir, glob.glob("%s/en" % basedir))
        locales.extend(map(os.path.basename, locale_dirs))

    locations = []

    for basedir in basedirs:
        if locales:
            dirs = [os.path.join(basedir, l, "LC_MESSAGES") for l in locales]
        else:
            dirs = [basedir]
        for ldir in dirs:
            for dirpath, dirnames, filenames in os.walk(ldir):
                locations.extend((dirpath, f) for f in filenames if f.endswith(".po"))

    return locations


def parse_locales(locations):
    locs = set()
    msgstrings = []

    for i, (dirpath, f) in enumerate(locations):
        locs.add(os.path.join(dirpath, f))

    for po_path in locs:
        po = polib.pofile(po_path)
        print(f"opening {po_path}")
        valid_entries = [e for e in po if not e.obsolete]
        for entry in valid_entries:
            key = po_to_lokalise(entry)
            msgstrings.append(key)

    return msgstrings


def po_to_lokalise(poentry):
    floc = []

    for (f, l) in poentry.occurrences:
        floc.append("{}:{}".format(f, l))

    occurrences = "\n".join(floc)

    return {
        "key_name": poentry.msgid,
        "comments": {"comment": poentry.comment or occurrences},
        "platforms": ["web"],
        "tags": ["api"],
        "translations": [{"language_iso": "en", "translation": poentry.msgstr}],
    }
