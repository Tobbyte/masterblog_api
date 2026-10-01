"""A simple Flask app for a blog.

~ Made with ❤️ and without ai or code completion ~
"""

import uuid
from copy import deepcopy
from typing import Any

from blog_store import BlogStore
from config import (
    ERR_NO_POST_UID,
    ERR_SAVE_POST_UID,
    UID_FILE_PATH,
)
from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug import Response
from werkzeug.exceptions import InternalServerError


class Masterblog:
    """A simple Flask app for a blog.

    Allows users to add, update, delete, and like blog posts.
    """

    def __init__(self) -> None:
        """Initialize the Flask app.

        Sets routes, loads initial data.
        """
        self.app = Flask(__name__)

        self.blog_store = BlogStore()

        # Would normally live in .env
        self.app.secret_key = "super-geheimer-uid-keyseed"  # noqa: S105

        # db error throws on startup (not as request). so set flag in db
        # startup (not raise there) and abort per before_request.
        self.app.before_request(self.check_db_health)

        self.app.add_url_rule("/", view_func=self.index)

        self.app.add_url_rule(
            "/add",
            view_func=self.add,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/delete/<int:post_id>",
            view_func=self.delete,
            # note: exercise says "access route directly", which
            # implies GET. Won't do, bad practice.
            methods=["POST"],
        )

        self.app.add_url_rule(
            "/update/<int:post_id>",
            view_func=self.update_post,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/like/<int:post_id>",
            view_func=self.like_post,
            methods=["POST"],
        )

        self.app.register_error_handler(404, self.page_not_found)
        self.app.register_error_handler(500, self.internal_server_error)

        # load data here (not only in index route) to prevent failing
        # when accessing f.e. /update directly
        self.blog_store.load()

    def check_db_health(self) -> None:
        """Check db health before every request.

        Raises InternalServerError if db is corrupted.
        Gets called before every request.
        """
        if request.endpoint == "static":
            return

        self.blog_store.load()  # call fresh to update on the fly
        if self.blog_store.db_error:
            raise InternalServerError

    @staticmethod
    def page_not_found(_) -> tuple:  # noqa: ANN001
        """Render the 404 error page."""
        return render_template("404.html"), 404

    @staticmethod
    def internal_server_error(error: Exception) -> tuple:
        """Render the 500 error page."""
        return render_template("500.html", error=error), 500

    def _get_last_uid_from_posts(self) -> int:
        """Cycles through all blog posts to get last id."""
        posts = self.blog_store.load()
        if posts:
            return max(post["id"] for post in posts)
        return 0

    def _get_uid(self) -> int:
        """Get a unique identifier for a new blog post.

        Reads the last used UID from a file and increments it for
        the next post.
        If the file does not exist or is empty, it finds the last id
        in existing posts and increases by +1. Saves to uid file.

        Note: This can lead to links to posts directing to the wring
        post if posts got deleted and the blog is setup fresh with
        empty uid file.
        """
        try:
            with UID_FILE_PATH.open(encoding="utf-8") as f:
                last_uid = f.read()
        except OSError:
            print(ERR_NO_POST_UID)
            last_uid = ""

        try:
            new_uid = int(last_uid) + 1
        except ValueError:
            new_uid = self._get_last_uid_from_posts() + 1
        self._save_uid(new_uid)
        return new_uid

    def _save_uid(self, new_uid: int) -> None:
        """Save the new UID to a file for future use."""
        try:
            with UID_FILE_PATH.open("w", encoding="utf-8") as f:
                f.write(str(new_uid))
        except OSError as e:
            print(ERR_SAVE_POST_UID)
            raise InternalServerError from e

    def _get_user_uid(self) -> str:
        """Get or create a user uid (for the current session)."""
        if "user_uid" not in session:
            session["user_uid"] = str(uuid.uuid4())
        return session["user_uid"]

    def _fetch_post_by_id(self, post_id: int) -> dict | None:
        """Fetch a blog post from runtime data by its ID."""
        posts = self.blog_store.load()
        return next(
            filter(lambda post: post["id"] == post_id, posts),
            None,
        )

    ### route handlers ###

    def index(self) -> str:
        """Render the index page with blog posts."""
        posts = self.blog_store.load()
        return render_template(
            "index.html",
            posts=posts,  # refresh
            uuid=self._get_user_uid(),
            blogtitle="Mein Blog",
        )

    def add(self) -> str | Response:
        """Render form on get or save post on post."""
        if request.method == "POST":
            self._add_post(request.form.to_dict())  # use flat=False for multi
            return redirect(url_for("index"))

        return render_template("add.html")

    def delete(self, post_id: int) -> Response:
        """Delete blog post route."""
        if self._fetch_post_by_id(post_id) is None:
            abort(404)

        if request.method == "POST":
            self._del_post(post_id)

        return redirect(url_for("index"))

    def update_post(self, post_id: int) -> str | tuple | Response:
        """Update post route."""
        post = self._fetch_post_by_id(post_id)
        if post is None:
            abort(404)
        if request.method == "POST":
            self._update_post_data(post_id, request.form.to_dict())
            return redirect(url_for("index"))
        return render_template("update.html", post=post)

    def like_post(self, post_id: int) -> Response:
        """Toggle like route."""
        if self._fetch_post_by_id(post_id) is None:
            abort(404)

        user_uid = self._get_user_uid()
        self._toggle_like(post_id, user_uid)
        return redirect(url_for("index"))

    ### routes logic ###

    def _add_post(self, new_post: dict) -> None:
        """Add a new blog post."""
        new_id = self._get_uid()
        new_post["id"] = new_id
        posts_copy = deepcopy(self.blog_store.load())
        posts_copy.append(new_post)
        self.blog_store.save(posts_copy)

    def _del_post(self, post_id: int) -> None:
        """Delete a blog post by its ID."""
        posts_copy = deepcopy(self.blog_store.load())
        posts = [post for post in posts_copy if post["id"] != post_id]
        self.blog_store.save(posts)

    def _update_post_data(self, post_id: int, new_post_data: dict) -> None:
        """Update the data of a blog post by its ID."""
        posts_copy = deepcopy(self.blog_store.load())

        # Ensure id cant be changed, f.e. hidden input field in form
        new_post_data.pop("id", None)

        posts = [
            {**post_copy, **new_post_data}
            if post_copy["id"] == post_id
            else post_copy
            for post_copy in posts_copy
        ]
        self.blog_store.save(posts)

    def _toggle_like(self, post_id: int, user_uid: str) -> None:
        """Toggle the like status for a post by its ID."""
        posts_copy = deepcopy(self.blog_store.load())

        for post in posts_copy:
            if post["id"] == post_id:
                likes = post.setdefault("liked_by", [])
                if user_uid in likes:
                    likes.remove(user_uid)
                else:
                    likes.append(user_uid)
                break

        self.blog_store.save(posts_copy)

    ###

    def run(self, **kwargs: Any) -> None:  # noqa: ANN401
        """Start the Flask app."""
        self.app.run(**kwargs)


if __name__ == "__main__":
    Masterblog().run(debug=True)
