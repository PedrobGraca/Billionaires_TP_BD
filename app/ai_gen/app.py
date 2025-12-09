from flask import Flask, render_template
from db_mock import get_query1, get_query2

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/query1")
def query1():
    results = get_query1()
    description = "Query 1: Example data from dataset."
    return render_template(
        "query.html",
        title="Query 1",
        description=description,
        results=results,
        columns=["Column A", "Column B", "Column C"]
    )

@app.route("/query2")
def query2():
    results = get_query2()
    description = "Query 2: Another example query."
    return render_template(
        "query.html",
        title="Query 2",
        description=description,
        results=results,
        columns=["ID", "Name", "Value"]
    )

if __name__ == "__main__":
    app.run(debug=True)
