"""Class for handling blog post storage."""

import json

from config import (
    DB_FILE_PATH,
    ERR_DB_CORRUPT,
    ERR_SAVE_DATA_FAILED,
    UID_FILE_PATH,
)
from werkzeug.exceptions import InternalServerError


class BlogStore:
    """Load and save blog posts in json file."""

    def __init__(self) -> None:
        """Init storage and ensure the db file exists."""
        self.db_error = False
        self._make_sure_file_exists()

    def _make_sure_file_exists(self) -> None:
        """Ensure that the db file exists."""
        try:
            DB_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            if not DB_FILE_PATH.is_file():
                with DB_FILE_PATH.open(mode="w", encoding="utf-8") as file:
                    file.write("[]")

            if not UID_FILE_PATH.is_file():
                with UID_FILE_PATH.open(mode="w", encoding="utf-8") as file:
                    file.write("")

        except OSError as e:
            self.db_error = True
            raise InternalServerError from e

    def load(self) -> list[dict]:
        """Load posts json."""
        # db file exists, but is empty
        if DB_FILE_PATH.stat().st_size == 0:
            self.db_error = False
            return []

        try:
            with DB_FILE_PATH.open(encoding="utf-8") as f:
                posts = json.load(f)
        except json.JSONDecodeError:
            print(ERR_DB_CORRUPT)
            self.db_error = True
            return []
        else:
            # reset in case error went puff
            self.db_error = False
            return posts

    def save(self, blog_posts: list[dict]) -> None:
        """Save blog posts data."""
        try:
            with DB_FILE_PATH.open("w", encoding="utf-8") as f:
                f.write(json.dumps(blog_posts))
        except OSError as e:
            raise InternalServerError(ERR_SAVE_DATA_FAILED) from e
