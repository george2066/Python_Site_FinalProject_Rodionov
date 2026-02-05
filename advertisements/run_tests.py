import os
import sys

import django

sys.path.insert(0, r"C:\Users\George\Desktop\diplom")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "diplom.settings")
django.setup()

from django.test.runner import DiscoverRunner

if __name__ == "__main__":
    test_runner = DiscoverRunner()
    failures = test_runner.run_tests(["advertisements"])
    sys.exit(bool(failures))
