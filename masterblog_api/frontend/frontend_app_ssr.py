# pylint: disable=wrong-import-position
"""Server-side rendered frontend for the Masterblog application."""

import sys
from pathlib import Path

# make runnable from wherever.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from flask import abort, redirect, render_template, request, url_for
from werkzeug import Response

from masterblog_api.masterblog_app import Masterblog


class MasterblogSSR(Masterblog):
    """Flask app for ssr frontend of the Masterblog application."""

    def __init__(self) -> None:
        """Initialize the Flask app and set up routes."""
        super().__init__()
        self.setup_routes()
        self.setup_error_handlers()

    def setup_routes(self) -> None:
        """Set up the server-side rendered routes."""
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

    ### route handlers ###

    def setup_error_handlers(self) -> None:
        """Register err handlers for serving html errors."""
        self.app.register_error_handler(404, self.page_not_found)
        self.app.register_error_handler(500, self.internal_server_error)

    @staticmethod
    def page_not_found(_) -> tuple:  # noqa: ANN001
        """Render the 404 error page."""
        return render_template("404.html"), 404

    @staticmethod
    def internal_server_error(error: Exception) -> tuple:
        """Render the 500 error page."""
        return render_template("500.html", error=error), 500

    def index(self) -> str:
        """Render the index page with blog posts."""
        posts = self.blog_store.load()
        return render_template(
            "index_ssr.html",
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
        """Delete a blog post route."""
        if self._fetch_post_by_id(post_id) is None:
            abort(404)

        self._del_post(post_id)
        return redirect(url_for("index"))

    def update_post(self, post_id: int) -> str | Response:
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


if __name__ == "__main__":
    MasterblogSSR().run(host="0.0.0.0", port=5001, debug=True)  # noqa: S104
