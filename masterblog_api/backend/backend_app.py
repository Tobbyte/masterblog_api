"""Backend module for the Masterblog application."""

from flask import jsonify, request
from flask_cors import CORS
from werkzeug import Response

from masterblog_api.app import Masterblog


class MasterblogApi(Masterblog):
    """A simple Flask app for a blog with API support.

    Inherits from Masterblog and adds API routes.
    """

    def __init__(self) -> None:
        """Initialize the Flask app with API routes."""
        super().__init__()
        CORS(self.app)  # This will enable CORS for all routes
        self.app.add_url_rule(
            "/api/posts",
            view_func=self.get_posts_api,
            methods=["GET", "POST"],
        )

    def get_posts_api(self) -> tuple[Response, int]:
        """Return all blog posts as JSON."""
        if request.method == "POST":
            print("via post")
            post_data = request.get_json(silent=True)

            if (
                not post_data
                or not isinstance(post_data, dict)
                or not post_data.get("title", "").strip()
                or not post_data.get("content", "").strip()
            ):
                return jsonify({"error": "Invalid request data"}), 400

            new_post = self._add_post(
                {
                    "title": post_data["title"],
                    "content": post_data["content"],
                },
            )
            return jsonify(new_post), 201
        print("via get")
        return jsonify(self.blog_store.load()), 200


if __name__ == "__main__":
    MasterblogApi().run(debug=True)
