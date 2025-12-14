
import requests
import sys
from datetime import datetime
from pprint import pprint
from dataclasses import dataclass, fields, field
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
# User Endpoints
# https://www.reddit.com/user/[username]/about.json
# https://www.reddit.com/user/[username]/submitted.json
# https://www.reddit.com/user/[username]/comments.json

# General / Stats
# https://www.reddit.com/subreddits/new.json
# https://www.reddit.com/subreddits/popular.json
# https://www.reddit.com/r/all/top/.json

# Subreddit
# https://www.reddit.com/r/[subreddit]/rising/.json
# https://www.reddit.com/r/[subreddit]/new/.json
# https://www.reddit.com/r/[subreddit]/top/.json

ROOT_URL="https://www.reddit.com/"
HEADERS = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0 Safari/537.36"
}

@dataclass 
class RedditUser:
    is_gold: bool 
    is_mod: bool
    name: str 
    link_karma: int
    comment_karma: int 
    total_karma: int 

    created_utc: float # Will be converted to datetime in post_init

    def __post_init__(self):
        self.created_utc = datetime.fromtimestamp(self.created_utc)


@dataclass 
class RedditComment:
    subreddit: str 
    author: str
    body: str
    ups: int 
    downs: int
    created_utc: float  # Will be converted to datetime in post_init
    permalink: str 
    sentiment: dict = None
    replies: dict = field(default_factory=dict, repr=False)
    extra_data: dict = field(default_factory=dict, repr=False)


    def __post_init__(self):
        self.created_utc = datetime.fromtimestamp(self.created_utc)
        self.body = self.body.replace('\n', ' ')
        self.sentiment = SentimentIntensityAnalyzer().polarity_scores(self.body)
             

    @classmethod
    def from_dict(cls, data: dict) -> 'RedditComment':
        """Filter unknown fields before initialization"""
        valid_fields = {f.name for f in fields(cls) if f.name != 'extra_data'}

        return cls(**{k: v for k, v in data.items() if k in valid_fields}, extra_data={k: v for k, v in data.items() if k not in valid_fields})    
    
    def get_replies(self):
        if self.replies == '':
            return []
        else:
            return [RedditComment.from_dict(reply['data']) for reply in self.replies['data']['children'] if reply['kind'] == "t1"]


    
@dataclass
class RedditPost:
    subreddit: str 
    author: str
    title: str 
    name: str 
    ups: int 
    created_utc: float  # Will be converted to datetime in post_init
    permalink: str 
    extra_data: dict = field(default_factory=dict, repr=False)
    comments: list[RedditComment] = field(default_factory=dict, repr=False)
    
    def __post_init__(self):
        self.created_utc = datetime.fromtimestamp(self.created_utc)
        self.comments = []

    def get_comments(self):
        url = f"https://www.reddit.com{self.permalink}/.json"
        res = requests.get(url, headers=HEADERS, timeout=5)
        data = res.json()
        for comment in data[1]['data']['children']:
            if comment['kind'] == "t1":
                self.comments.append(RedditComment.from_dict(comment['data']))   

        return self.comments             

    @classmethod
    def from_dict(cls, data: dict) -> 'RedditPost':
        """Filter unknown fields before initialization"""
        valid_fields = {f.name for f in fields(cls) if f.name != 'extra_data' and f.name != "new_posts" and f.name != "comments"}

        return cls(**{k: v for k, v in data.items() if k in valid_fields}, extra_data={k: v for k, v in data.items() if k not in valid_fields})
    
@dataclass
class SubReddit:
    display_name: str
    title: str 
    subscribers: float 
    url: str
    advertiser_category: str
    over18: bool
    id: str
    created_utc: float  # Will be converted to datetime in post_init
    extra_data: dict = field(default_factory=dict, repr=False)
    description: str = field(default_factory=str, repr=False)
    posts: list[RedditPost] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> 'SubReddit':
        """Filter unknown fields before initialization"""
        valid_fields = {f.name for f in fields(cls) if f.name != 'extra_data' and f.name != "posts"}

        return cls(**{k: v for k, v in data.items() if k in valid_fields}, extra_data={k: v for k, v in data.items() if k not in valid_fields})

    def __post_init__(self):
        self.created_utc = datetime.fromtimestamp(self.created_utc)
        self.posts = []

    def get_posts(self):
        self.posts = []
        try:
            url = f"https://www.reddit.com/{self.url}/top.json?limit=50"
            res = requests.get(url, headers=HEADERS, timeout=4)
            data = res.json()
            for post in data['data']['children']:
                self.posts.append(RedditPost.from_dict(post['data']))
        
        except Exception as e:
            print(f"Error getting RedditPost: {e}")
        return self.posts



def getSubreddits(url: str): 
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        data = res.json()
        return [SubReddit.from_dict(i['data']) for i in data['data']['children']] 
    else:
        print(res)
        return []
    
def getRedditPosts(url: str): 
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        data = res.json()
        return [RedditPost.from_dict(i['data']) for i in data['data']['children']] 
    else:
        print(res)
        return []

if __name__=="__main__":
    
    pos = []
    neg = []
    nu = []
    res = requests.get("https://www.reddit.com/r/politics/about.json", headers=HEADERS)
    subreddit = SubReddit.from_dict(res.json()['data'])
    posts = subreddit.get_posts()
    # posts = getRedditPosts("https://www.reddit.com/r/all/top/.json?limit=50")
    for i, post in enumerate(posts): 
        for c in post.get_comments():
            if c.sentiment['compound'] < -.05: neg.append(c)
            if c.sentiment['compound'] > .05: pos.append(c)
            else: nu.append(c)


        sys.stdout.write(f"\rProcessing posts: {i}/{len(posts)}")
        sys.stdout.flush()

    print("")
    print(f"--- Summary ---")
    print(f"pos: {len(pos)}")
    print(f"neg: {len(neg)}")
    print(f"neu: {len(nu)}")
    print()
    print(f"Total: {sum([len(pos), len(neg), len(nu)])}")

    neg.sort(key=lambda x: x.sentiment['compound'])
    pos.sort(key=lambda x: x.sentiment['compound'], reverse=True)
    pprint(neg[0])
    pprint(pos[0])



    # pprint(subreddit)
    
    # posts = subreddit.get_posts()
    
    # pprint(posts[11])

    # comments = post.get_comments()
    # for c in comments:
    #     pprint(c)
    #     pprint(c.get_replies())
