from flask import Flask, render_template
from Reddit import *


app = Flask(__name__)




# top = getSubreddits("https://www.reddit.com/r/all/top/.json")
# top.sort(key=lambda x: x.subscribers, reverse=True)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/popular")
def popular():
    popular_subs = getSubreddits("https://www.reddit.com/subreddits/popular.json")
    popular_subs.sort(key=lambda x: x.subscribers, reverse=True)
    return render_template("subreddits.html", subreddits=popular_subs)

@app.route("/new")
def new():
    new_subs = getSubreddits("https://www.reddit.com/subreddits/new.json")
    new_subs.sort(key=lambda x: x.subscribers, reverse=True)    
    return render_template("subreddits.html", subreddits=new_subs)

@app.route("/top")
def top():
    top_posts = getRedditPosts("https://www.reddit.com/r/all/top/.json")
    top_posts.sort(key=lambda x: x.ups, reverse=True)
    return render_template("posts.html", posts=top_posts)


# Status
@app.errorhandler(404)
def not_found(e):
    return render_template("status/404.html", error=e)


if __name__ == "__main__":
    app.run(debug=True)
