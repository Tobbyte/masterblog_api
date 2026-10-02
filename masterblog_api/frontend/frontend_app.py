"""Minimalistic debug frontend for Masterblog API."""
from flask import Flask, render_template

app = Flask(__name__, template_folder="templates", static_folder="../static")


@app.route("/", methods=["GET"])
def home() -> str:
    """Render the home page."""
    return render_template("index_csr.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)  # noqa: S104, S201
