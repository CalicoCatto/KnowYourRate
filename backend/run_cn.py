"""
KnowYourRate CN Edition standalone entry point.

Sets EDITION=cn before importing and running the main entry point.
"""

import os

os.environ["EDITION"] = "cn"

from run import main  # noqa: E402

if __name__ == "__main__":
    main()
