import glob
import os
from pprint import pprint

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

    for basedir in basedirs:
        if locales:
            dirs = [os.path.join(basedir, l, "LC_MESSAGES") for l in locales]
        else:
            dirs = [basedir]
        locations = []
        for ldir in dirs:
            for dirpath, dirnames, filenames in os.walk(ldir):
                locations.extend((dirpath, f) for f in filenames if f.endswith(".po"))
        if locations:
            pprint(locations)
            # self.compile_messages(locations)


def parse_locales(locations):
    for i, (dirpath, f) in enumerate(locations):
        po_path = os.path.join(dirpath, f)
