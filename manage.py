#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Add the project root directory and apps directory to the Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(project_root)
    sys.path.append(os.path.join(project_root, "apps"))

    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
    try:
        # --- DIAGNOSTIC PRINT --- # REMOVED
        # print("--- sys.path --- DUMP ---")
        # import pprint
        # pprint.pprint(sys.path)
        # print("--- END sys.path DUMP ---")
        # ----------------------- # REMOVED
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
