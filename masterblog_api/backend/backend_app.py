"""Backend module for the Masterblog application."""

import sys
from pathlib import Path

# make runnable from wherever.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from flask import jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug import Response
from werkzeug.exceptions import HTTPException

from masterblog_api.backend.backend_config import (
    API_DELETE_SUCCESS,
    API_ERR_404_NOT_FOUND,
    API_ERR_BAD_REQUEST_DATA,
    API_ERR_INTERNAL_SERVER_ERROR,
    API_ERR_INVALID_POST_ID,
    API_ERR_INVALID_REQUEST_DATA,
    API_ERR_METHOD_NOT_ALLOWED,
    API_ERR_SEARCH_QUERY_PARAM_REQUIRED,
    API_ERR_TOO_MANY_REQUESTS,
    API_PAGINATION_DEFAULT_PAGE,
    API_PAGINATION_DEFAULT_PAGE_SIZE,
    API_PAGINATION_PARAM_PAGE,
    API_PAGINATION_PARAM_PERPAGE,
    API_SEARCH_PARAM_MATCHEITHER,
    API_SEARCH_PARAM_MATCHEITHER_VALIDS,
    API_SEARCH_QUERYABLE_FIELDS,
    API_SORT_PARAM_DESC,
    API_SORT_SORTABLE_FIELDS,
    POST_FIELD_AUTHOR,
    POST_FIELD_CONTENT,
    POST_FIELD_ID,
    POST_FIELD_TITLE,
    POST_FILED_LIKEDBY,
)
from masterblog_api.backend.swagger import init_swagger_ui
from masterblog_api.config import ERR_POST_NOT_FOUND
from masterblog_api.masterblog_app import Masterblog


class MasterblogApi(Masterblog):
    """A simple Flask app for a blog with API support.

    Inherits from Masterblog and adds API routes.

    Apart from the original Masterblog class being refactored into a
    shared and a sole ssr class, the following class extends the
    original with a full RESTFULapi, extending the original
    functionalities with search, pagination, rate limiting, CORS support
    and swagger documentation.

    TODOs:
    - the KeyError for post-not-found should be refactored into a custom
    exception class.
    - routes like f.e. update_post_api expect all fields as str. Simply
    ignoring mis-formatted, unneeded fields would be more friendly.
    - search results ignore sorting params.
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

        self.setup_routes()
        self.setup_error_handlers()

    def setup_error_handlers(self) -> None:
        """Register JSON error handlers for the API application."""
        self.app.register_error_handler(404, self.api_page_not_found)
        self.app.register_error_handler(405, self.api_method_not_allowed)
        self.app.register_error_handler(429, self.api_too_many_requests)
        self.app.register_error_handler(500, self.api_internal_server_error)

    @staticmethod
    def api_page_not_found(_: HTTPException) -> tuple[Response, int]:
        """Return a JSON response for 404."""
        return jsonify({"error": API_ERR_404_NOT_FOUND}), 404

    @staticmethod
    def api_method_not_allowed(_: HTTPException) -> tuple[Response, int]:
        """Return a JSON response for method forbidden."""
        return jsonify({"error": API_ERR_METHOD_NOT_ALLOWED}), 405

    @staticmethod
    def api_too_many_requests(_: HTTPException) -> tuple[Response, int]:
        """Return JSON for when rate limit is exceeded."""
        return jsonify({"error": API_ERR_TOO_MANY_REQUESTS}), 429

    @staticmethod
    def api_internal_server_error(_: Exception) -> tuple[Response, int]:
        """Return a JSON response for internal API errors."""
        return jsonify({"error": API_ERR_INTERNAL_SERVER_ERROR}), 500

    def setup_routes(self) -> None:
        """Set up the API routes for the Flask app."""
        self.app.add_url_rule(
            "/api/posts",
            view_func=self.get_posts_api,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/api/posts/<int:post_id>",
            view_func=self.delete_post_api,
            methods=["DELETE"],
        )

        self.app.add_url_rule(
            "/api/posts/<int:post_id>",
            view_func=self.update_post_api,
            methods=["PUT"],  # should be PATCH, but exercise says PUT
        )

        self.app.add_url_rule(
            "/api/posts/<int:post_id>/like",
            view_func=self.like_post_api,
            methods=["POST"],
        )

        self.app.add_url_rule(
            "/api/posts/search",
            view_func=self.search_posts_api,
            methods=["GET"],
        )

    ### route handlers ###

    def get_posts_api(self) -> tuple[Response, int]:
        """Return all blog posts as JSON or adds new post.

        Via GET: Returns all posts.
        Via POST: Adds a new post and returns it.

        Accepts optional query params 'sort' and 'direction' on GET.
        """
        if request.method == "POST":
            return self._create_post_api()

        all_posts = self.blog_store.load()  # load here to keep sorting static
        sorted_posts = self._sort_posts(all_posts, request.args)

        if sorted_posts is not None:
            pagination = self._paginate_posts(sorted_posts)
            if pagination is not None:
                return jsonify(pagination), 200

        return jsonify({"error": API_ERR_BAD_REQUEST_DATA}), 400

    def _create_post_api(self) -> tuple[Response, int]:
        """Create a blog post from the current request."""
        post_data = request.get_json(silent=True)

        if (
            not post_data
            or not isinstance(post_data, dict)
            or not all(isinstance(cont, str) for cont in post_data.values())
            or not post_data.get(POST_FIELD_TITLE, "").strip()
            or not post_data.get(POST_FIELD_CONTENT, "").strip()
            or not post_data.get(POST_FIELD_AUTHOR, "").strip()
        ):
            return jsonify({"error": API_ERR_INVALID_REQUEST_DATA}), 400

        new_post = self._add_post(
            {
                POST_FIELD_AUTHOR: post_data[POST_FIELD_AUTHOR],
                POST_FIELD_TITLE: post_data[POST_FIELD_TITLE],
                POST_FIELD_CONTENT: post_data[POST_FIELD_CONTENT],
            },
        )
        return jsonify(new_post), 201

    def delete_post_api(self, post_id: int) -> tuple[Response, int]:
        """Delete a blog post by ID.

        Returns the result as JSON.
        """
        try:
            self._delete_post(post_id)
            return jsonify({
                "message": API_DELETE_SUCCESS.format(id=post_id),
            }), 200
        except ValueError:
            return jsonify({"error": API_ERR_INVALID_POST_ID}), 400
        except KeyError:
            return jsonify({"error": ERR_POST_NOT_FOUND}), 404

    def update_post_api(self, post_id: int) -> tuple[Response, int]:
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
            ):
                return jsonify({"error": API_ERR_INVALID_REQUEST_DATA}), 400

            try:
                self._fetch_post_by_id_with_error(post_id)
                updated_post = self._update_post(
                    post_id,
                    raw_post_data,
                )
                return jsonify({
                    POST_FIELD_ID: post_id,
                    POST_FIELD_TITLE: updated_post[POST_FIELD_TITLE],
                    POST_FIELD_CONTENT: updated_post[POST_FIELD_CONTENT],
                }), 200

            except ValueError:
                return jsonify({"error": API_ERR_INVALID_POST_ID}), 400
            except KeyError:
                return jsonify({"error": ERR_POST_NOT_FOUND}), 404

        else:
            # should already be handled by Flask's method routing, jic
            return jsonify({"error": API_ERR_METHOD_NOT_ALLOWED}), 405

    def like_post_api(self, post_id: int) -> tuple[Response, int]:
        """Toggle the current user's like for a post."""
        try:
            user_uid = self._get_user_uid()
            updated_post = self._toggle_like(post_id, user_uid)
            likes = updated_post.get(POST_FILED_LIKEDBY, [])
            return jsonify({
                "id": post_id,
                "liked": user_uid in likes,
                "like_count": len(likes),
            }), 200
        except KeyError:
            return jsonify({"error": ERR_POST_NOT_FOUND}), 404

    def search_posts_api(self) -> tuple[Response, int]:
        """Search for blog posts by title and/or content.

        Accepts query parameters:
        - title: The title to search for (optional).
        - content: The content to search for (optional).
        - match_either: If "true", matches posts that contain either
          the title or content (default: False). Ignored if only one of
          title or content is provided.
        - ignores invalid query parameters
        """
        if not request.args:
            return jsonify({"error": API_ERR_SEARCH_QUERY_PARAM_REQUIRED}), 400

        all_posts = self.blog_store.load()  # load here to keep sorting static

        matching_posts = self._search_posts(all_posts, request.args)

        if matching_posts is None:
            return jsonify({"error": API_ERR_BAD_REQUEST_DATA}), 400

        pagination = self._paginate_posts(matching_posts)

        # TODO: bad paginatino fails searching.
        if pagination is None:
            return jsonify({"error": API_ERR_BAD_REQUEST_DATA}), 400

        return jsonify(pagination), 200

    ### routes logic ###

    def _delete_post(self, post_id: int) -> None:
        """Delete a blog post by ID."""
        self._fetch_post_by_id_with_error(post_id)  # raise if none

        super()._del_post(post_id)

    def _update_post(
        self,
        post_id: int,
        raw_new_post_data: dict,
    ) -> dict:
        """Update a blog post by ID."""
        # clean empty fields of new post_data for merging.
        new_post_data = {
            k: v
            for k, v in raw_new_post_data.items()
            if k in {POST_FIELD_TITLE, POST_FIELD_CONTENT} and v.strip()
        }

        return super()._update_post_data(post_id, new_post_data)

    @staticmethod
    def _search_posts(
        posts: list[dict],
        search_args: dict,
    ) -> list[dict] | None:
        """Search for blog posts by title and/or content."""
        search_query = {  # {where:what}, eg {"content":"hurtz"}
            k: v.lower()
            for k, v in search_args.items()
            if k in API_SEARCH_QUERYABLE_FIELDS and v.strip()
        }

        if not search_query:
            # bad request, no params (excl. match_either)
            return None

        match_either = API_SEARCH_PARAM_MATCHEITHER_VALIDS.get(
            search_args.get(API_SEARCH_PARAM_MATCHEITHER, "").strip(),
            False,
        )

        any_or_all = any if match_either else all

        return [
            post
            for post in posts
            if any_or_all(
                q in post[f].lower() for f, q in search_query.items()
            )
        ]

    ### statics ###

    @staticmethod
    def _sort_posts(posts: list[dict], search_args: dict) -> list[dict] | None:
        """Sort posts by parameters.

        Sorts ascending by default, breaks tie on id.
        Ignores invalid parameters.
        """
        sortby_field = search_args.get("sort", "").strip()
        sort_direction_field = search_args.get("direction", "").strip()

        if not sortby_field:
            # bad request (ignoring direction)
            return posts

        if sortby_field not in API_SORT_SORTABLE_FIELDS:
            return None

        reverse = sort_direction_field == API_SORT_PARAM_DESC

        return sorted(
            posts,
            key=lambda post: (post[sortby_field], post[POST_FIELD_ID]),
            reverse=reverse,
        )

    @staticmethod
    def _paginate_posts(posts: list[dict]) -> dict | None:
        """Return one page of posts with pagination metadata."""
        try:
            page = int(
                request.args.get(
                    API_PAGINATION_PARAM_PAGE,
                    API_PAGINATION_DEFAULT_PAGE,
                ),
            )
            per_page = int(
                request.args.get(
                    API_PAGINATION_PARAM_PERPAGE,
                    str(API_PAGINATION_DEFAULT_PAGE_SIZE),
                ),
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
            API_PAGINATION_PARAM_PAGE: page,
            API_PAGINATION_PARAM_PERPAGE: per_page,
            "total": total,
            "total_pages": total_pages,
        }


if __name__ == "__main__":
    MasterblogApi().run(host="0.0.0.0", port=5002, debug=True)  # noqa: S104
