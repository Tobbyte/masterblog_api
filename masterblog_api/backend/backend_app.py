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

        self.app.add_url_rule(
            "/api/posts/<id>",
            view_func=self.delete_post_api,
            methods=["DElETE"],
        )

        self.app.add_url_rule(
            "/api/posts/<id>",
            view_func=self.update_post_api,
            methods=["PUT"],
        )

        self.app.add_url_rule(
            "/api/posts/search",
            view_func=self.search_posts_api,
            methods=["GET"],
        )

    def get_posts_api(self) -> tuple[Response, int]:
        """Return all blog posts as JSON.

        Via GET: Returns all posts.
        Via POST: Adds a new post and returns it.

        Accepts optional query params 'sort' and 'direction'.
        """
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

        all_posts = self.blog_store.load()

        sort_by_field = request.args.get("sort", "").strip()
        sort_direction_field = request.args.get("direction", "").strip()

        if sort_by_field:
            if sort_by_field not in {"id", "title", "content"}:
                return jsonify({"error": "Invalid sort field"}), 400

            reverse = False
            if sort_direction_field and sort_direction_field in {
                "asc",
                "desc",
            }:
                # ignore bad sort parameter, default to asc
                reverse = sort_direction_field == "desc"

            all_posts.sort(
                key=lambda post: post[sort_by_field],
                reverse=reverse,
            )

        return jsonify(all_posts), 200

    def delete_post_api(self, id: str) -> tuple[Response, int]:
        """Delete a blog post by ID and return the result as JSON."""
        try:
            self._delete_post(int(id))
            return jsonify({
                "message": f"Post with id {id} has been deleted successfully.",
            }), 200
        except ValueError:
            return jsonify({"error": "Invalid post ID"}), 400
        except KeyError:
            return jsonify({"error": "Post not found"}), 404

    def _delete_post(self, post_id: int) -> None:
        """Delete a blog post by ID."""
        if self._fetch_post_by_id(post_id) is None:
            raise KeyError(f"Post with id {post_id} not found.")
        super()._del_post(post_id)

    def update_post_api(self, id: str) -> tuple[Response, int]:
        """Update a blog post by ID and return the result as JSON."""
        if request.method == "PUT":
            raw_post_data = request.get_json(silent=True)
            print(raw_post_data)
            if (
                not raw_post_data
                or not isinstance(raw_post_data, dict)
                or (
                    not raw_post_data.get("title", "").strip()
                    and not raw_post_data.get("content", "").strip()
                )
            ):
                return jsonify({"error": "Invalid request data"}), 400

            try:
                post_id = int(id)
                old_post = self._fetch_post_by_id_with_error(post_id)
                updated_post = self._update_post(
                    post_id,
                    old_post,
                    raw_post_data,
                )
                return jsonify({
                    "id": post_id,
                    "title": updated_post["title"],
                    "content": updated_post["content"],
                }), 200

            except ValueError:
                return jsonify({"error": "Invalid post ID"}), 400
            except KeyError:
                return jsonify({"error": "Post not found"}), 404

        else:
            # should already be handled by Flask's method routing, jic
            return jsonify({"error": "Method not allowed"}), 405

    def _update_post(
        self,
        post_id: int,
        old_post: dict,
        raw_new_post_data: dict,
    ) -> dict:
        """Update a blog post by ID."""
        # clean empty fields of new posts data for merging.
        new_post_data = {
            k: v for k, v in raw_new_post_data.items() if v.strip()
        }

        new_post_data = {**old_post, **new_post_data}

        return super()._update_post_data(post_id, new_post_data)

    def _fetch_post_by_id_with_error(self, post_id: int) -> dict:
        """Fetch a blog post by ID or raise an error if not found."""
        post = self._fetch_post_by_id(post_id)
        if post is None:
            raise KeyError(f"Post with id {post_id} not found.")
        return post

    def search_posts_api(self) -> tuple[Response, int]:
        """Search for blog posts by title and/or content.

        Accepts query parameters:
        - title: The title to search for (optional).
        - content: The content to search for (optional).
        - match_either: If "true", matches posts that contain either
          the title or content (default: False). Ignored if only one of
          title or content is provided.
        """
        title_query = request.args.get("title", "").strip()
        content_query = request.args.get("content", "").strip()

        if not title_query and not content_query:
            return jsonify({"error": "Query parameter is required"}), 400

        match_either = request.args.get("match_either")

        if match_either:
            match_either = match_either.lower().strip()
            if match_either not in {
                "true",
                "false",
            }:
                return jsonify({
                    "error": "Invalid value for match_either",
                }), 400

            match_either = match_either == "true"

        matching_posts = self._search_posts(
            title_query,
            content_query,
            match_either,  # pyright: ignore[reportArgumentType]
        )
        return jsonify(matching_posts), 200

    def _search_posts(
        self,
        title_query: str | None = None,
        content_query: str | None = None,
        match_either: bool | None = False,
    ) -> list[dict]:
        """Search for blog posts by title and/or content."""
        all_posts = self.blog_store.load()

        if title_query and not content_query:
            return [
                post
                for post in all_posts
                if title_query.lower() in post["title"].lower()
            ]
        if content_query and not title_query:
            return [
                post
                for post in all_posts
                if content_query.lower() in post["content"].lower()
            ]
        if content_query and title_query and not match_either:
            return [
                post
                for post in all_posts
                if title_query.lower() in post["title"].lower()  # pyright: ignore[reportOptionalMemberAccess]
                and content_query.lower() in post["content"].lower()  # pyright: ignore[reportOptionalMemberAccess]
            ]
        return [
            post
            for post in all_posts
            if title_query.lower() in post["title"].lower()  # pyright: ignore[reportOptionalMemberAccess]
            or content_query.lower() in post["content"].lower()  # pyright: ignore[reportOptionalMemberAccess]
        ]


if __name__ == "__main__":
    MasterblogApi().run(debug=True)
