import sys

# Fail with a clear message, not a confusing error deep inside a library
if sys.version_info < (3, 10):  # noqa: UP036 (on purpose: this runs on the old Python we warn about)
    sys.exit(
        f"❌ Python 3.10 or newer is needed (this is {sys.version.split()[0]}).\n"
        "   Install it, then run make setup from the main folder (see docs/SETUP_GUIDE.md)."
    )
