"""Backend module for the Masterblog application."""

from flask import jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
from werkzeug import Response

from masterblog_api.app import Masterblog
from masterblog_api.backend.backend_config import (
    API_DEFAULT_PAGE_SIZE,
    API_DELETE_SUCCESS,
    API_ERR_BAD_REQUEST_DATA,
    API_ERR_INVALID_POST_ID,
    API_ERR_INVALID_REQUEST_DATA,
    API_ERR_METHOD_NOT_ALLOWED,
    API_ERR_POST_NOT_FOUND,
    API_ERR_SEARCH_QUERY_PARAM_REQUIRED,
)


def init_swagger_ui(app):
    SWAGGER_URL = (
        "/api/docs"  # (1) swagger endpoint e.g. HTTP://localhost:5002/api/docs
    )
    API_URL = "/static/swagger_masterblog.json"  # (2) ensure you create this dir and file

    swagger_ui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            "app_name": "Masterblog_api",  # (3) You can change this if you like
        },
    )
    app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)


class MasterblogApi(Masterblog):
    """A simple Flask app for a blog with API support.

    Inherits from Masterblog and adds API routes.

    Apart from two non-breaking changes in the original masterblog app
    (update and add returns the respective posts), the following class
    extends the original solely ssr approach with a full RESTFULapi
    set for managing blog posts, extending it with search, pagination,
    rate limiting, CORS support and swagger documentation.


    """

    def __init__(self) -> None:
        """Initialize the Flask app with API routes."""
        super().__init__()
        CORS(self.app, supports_credentials=True)
        Limiter(
            key_func=get_remote_address,
            app=self.app,
            default_limits=["100 per minute"],
        )
        init_swagger_ui(self.app)
        self.app.add_url_rule(
            "/api/posts",
            view_func=self.get_posts_api,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/api/posts/<int:id>",
            view_func=self.delete_post_api,
            methods=["DELETE"],
        )

        self.app.add_url_rule(
            "/api/posts/<int:id>",
            view_func=self.update_post_api,
            methods=["PUT"],
        )

        self.app.add_url_rule(
            "/api/posts/<int:id>/like",
            view_func=self.like_post_api,
            methods=["POST"],
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

        Accepts optional query params 'sort' and 'direction' on GET.
        """
        if request.method == "POST":
            print("via post")
            post_data = request.get_json(silent=True)

            if (
                not post_data
                or not isinstance(post_data, dict)
                or not all(
                    isinstance(cont, str) for cont in post_data.values()
                )
                or not post_data.get("title", "").strip()
                or not post_data.get("content", "").strip()
                or not post_data.get("author", "").strip()
            ):
                return jsonify({"error": API_ERR_INVALID_REQUEST_DATA}), 400

            new_post = self._add_post(
                {
                    "author": post_data["author"],
                    "title": post_data["title"],
                    "content": post_data["content"],
                },
            )
            return jsonify(new_post), 201

        all_posts = self.blog_store.load()

        sortby_field = request.args.get("sort", "").strip()
        sort_direction_field = request.args.get("direction", "").strip()

        if sortby_field:
            if sortby_field not in {"id", "title", "content"}:
                return jsonify({"error": API_ERR_BAD_REQUEST_DATA}), 400

            reverse = False
            if sort_direction_field and sort_direction_field not in {
                "asc",
                "desc",
            }:
                return jsonify({"error": API_ERR_BAD_REQUEST_DATA}), 400

            reverse = sort_direction_field == "desc"

            all_posts.sort(
                key=lambda post: (post[sortby_field], post["id"]),
                reverse=reverse,
            )

        pagination = self._paginate_posts(all_posts)
        if pagination is None:
            return jsonify({"error": API_ERR_BAD_REQUEST_DATA}), 400

        return jsonify(pagination), 200

    def delete_post_api(self, id: int) -> tuple[Response, int]:  # noqa: A002
        """Delete a blog post by ID.

        Returns the result as JSON.
        """
        try:
            self._delete_post(id)
            return jsonify({
                "message": API_DELETE_SUCCESS.format(id=id),
            }), 200
        except ValueError:
            return jsonify({"error": API_ERR_INVALID_POST_ID}), 400
        except KeyError:
            return jsonify({"error": API_ERR_POST_NOT_FOUND}), 404

    def _delete_post(self, post_id: int) -> None:
        """Delete a blog post by ID."""
        self._fetch_post_by_id_with_error(post_id)  # raise if none

        super()._del_post(post_id)

    def update_post_api(self, id: int) -> tuple[Response, int]:  # noqa: A002
        """Update a blog post by ID.

        Returns the result as JSON.
        """
        if request.method == "PUT":
            raw_post_data = request.get_json(silent=True)

            if (
                not raw_post_data
                or not isinstance(raw_post_data, dict)
                or not all(
                    isinstance(cont, str) for cont in raw_post_data.values()
                )
                or not raw_post_data.get("title", "").strip()
            ):
                return jsonify({"error": API_ERR_INVALID_REQUEST_DATA}), 400

            try:
                old_post = self._fetch_post_by_id_with_error(id)
                updated_post = self._update_post(
                    id,
                    old_post,
                    raw_post_data,
                )
                return jsonify({
                    "id": id,
                    "title": updated_post["title"],
                    "content": updated_post["content"],
                }), 200

            except ValueError:
                return jsonify({"error": API_ERR_INVALID_POST_ID}), 400
            except KeyError:
                return jsonify({"error": API_ERR_POST_NOT_FOUND}), 404

        else:
            # should already be handled by Flask's method routing, jic
            return jsonify({"error": API_ERR_METHOD_NOT_ALLOWED}), 405

    def like_post_api(self, id: int) -> tuple[Response, int]:  # noqa: A002
        """Toggle the current user's like for a post."""
        try:
            self._fetch_post_by_id_with_error(id)
            user_uid = self._get_user_uid()
            self._toggle_like(id, user_uid)
            updated_post = self._fetch_post_by_id_with_error(id)
            likes = updated_post.get("liked_by", [])
            return jsonify({
                "id": id,
                "liked": user_uid in likes,
                "like_count": len(likes),
            }), 200
        except KeyError:
            return jsonify({"error": API_ERR_POST_NOT_FOUND}), 404

    def _update_post(
        self,
        post_id: int,
        old_post: dict,
        raw_new_post_data: dict,
    ) -> dict:
        """Update a blog post by ID."""
        # clean empty fields of new post_data for merging.
        new_post_data = {
            k: v
            for k, v in raw_new_post_data.items()
            if k in {"title", "content"} and v.strip()
        }

        new_post_data = {**old_post, **new_post_data}

        return super()._update_post_data(post_id, new_post_data)

    def _fetch_post_by_id_with_error(self, post_id: int) -> dict:
        """Fetch a blog post by ID or raise an error if not found."""
        post = self._fetch_post_by_id(post_id)
        if post is None:
            raise KeyError(API_ERR_POST_NOT_FOUND)
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
            return jsonify({"error": API_ERR_SEARCH_QUERY_PARAM_REQUIRED}), 400

        match_either = request.args.get("match_either")

        if match_either:
            match_either = match_either.lower().strip()
            if match_either not in {
                "true",
                "false",
            }:
                return jsonify({
                    "error": API_ERR_BAD_REQUEST_DATA,
                }), 400

            match_either = match_either == "true"

        matching_posts = self._search_posts(
            title_query,
            content_query,
            match_either=match_either,  # pyright: ignore[reportArgumentType]
        )
        pagination = self._paginate_posts(matching_posts)
        if pagination is None:
            return jsonify({"error": API_ERR_BAD_REQUEST_DATA}), 400

        return jsonify(pagination), 200

    @staticmethod
    def _paginate_posts(posts: list[dict]) -> dict | None:
        """Return one page of posts with pagination metadata."""
        try:
            page = int(request.args.get("page", "1"))
            per_page = int(
                request.args.get("per_page", str(API_DEFAULT_PAGE_SIZE)),
            )
        except ValueError:
            return None

        if page < 1 or per_page < 1:
            return None

        total = len(posts)
        total_pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page

        return {
            "posts": posts[start : start + per_page],
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        }

    def _search_posts(
        self,
        title_query: str | None = None,
        content_query: str | None = None,
        *,
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
