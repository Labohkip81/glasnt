import os
import httpx
import json
import textwrap 
from github import Github
import emoji

from datetime import datetime

starttime = datetime.now()

def remove_emoji(text):
    return emoji.get_emoji_regexp().sub(u'', text)

# Automatically provided by GitHub Actions. For local testing, provide your own. 
# https://docs.github.com/en/actions/configuring-and-managing-workflows/authenticating-with-the-github_token#about-the-github_token-secret
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def sidebyside(a, b):
    al = a.split("\n")
    bl = b.split("\n")

    if len(al) > len(bl):
        bl = bl +  [""] * (len(al) - len(bl))
    
    if len(bl) > len(al):
        al +=  [(len(al[0]) - 4) * " " ] * (len(bl) - len(al))

    if len(al) != len(bl): 
        print(f"Blocks must be same height: {len(al)} vs {len(bl)}")
        breakpoint()
    
    res = []
    for n in range(len(al)):
       res.append(f"{al[n]}{bl[n]}")
    return "\n".join(res)


def short(n, w=32, p=""):
    return textwrap.shorten(n, width=w, placeholder=p)

def table(s, w=40, l="|", r="|", t="_", b="_"): 
    ll = w - len(l) - len(r) 
    s = remove_emoji(s)
    lli = ll - 2
    res = []
    if t != "":
        res.append(f" {t * ll} ")
    for line in s.split("\n"):
        if len(line) > lli:
            nline = textwrap.shorten(line, width=lli, placeholder="").ljust(lli)
        else: 
            nline = line.ljust(lli)
        res.append(f"{l} {nline} {r}")
    if b != "": 
        res.append(f"{l}{b * ll}{r}\n")
    return "\n".join(res)

def flattable(s, w=40):
    return table(s, w, l="", r="", t="", b="")


def graphql(query):
    json = {"query": query} 
    uri = "https://api.github.com/graphql"
    headers = {"Authorization": f"bearer {GITHUB_TOKEN}"}
    r = httpx.post(uri, headers=headers, json=json)
    return r.text 

g = Github(GITHUB_TOKEN)
user = g.get_user()
USERNAME = user.login

# https://manytools.org/hacker-tools/convert-images-to-ascii-art/, width 32
avatar_art = """
              ...              
           .,,//. ..,(%@&       
           (     . ...*%%&%(    
                 .*(....,&#*,,  
           ..,../#&&%&&*,*.*.** 
  .       , .,*,/....#,,**,,//**
.           ., ,*(**,,,,**&%(/**
 .     .  ...../...(...,//(*&&/*
     . .###%&%&(.....,*//*,,#&&&
  .. .(%%%%%%%&%..**.,,,....&&& 
   . #%&%&%&&%&&&..,.......&&&  
     #&&%&&%&%&&&&%......&&#    
        (&&%%&&&&&&&&&&&
"""

userq = """query
{
  user(login: "%s") {
    followers {
      totalCount
    }
    starredRepositories {
      totalCount
    }
  }
}
""" % USERNAME

resp = graphql(userq)
data = json.loads(resp)["data"]["user"]
followers = data["followers"]["totalCount"]
starred = data["starredRepositories"]["totalCount"]

avatar = flattable(avatar_art, w=36)
userblock = avatar +"\n" + flattable(f"""
{user.name}
{user.login}
{short(user.bio, w=36)}
¤ {followers} followers · ✭ {starred} 
""", w=36)


pinnedq = """ query
{
  user(login: "%s") {
    pinnedItems(first: 6, types: [REPOSITORY, GIST]) {
      totalCount
      edges {
        node {
          ... on Repository {
            nameWithOwner, description
            primaryLanguage {
              name
            }
            stargazers {
              totalCount
            }
            forks {
              totalCount
            }
          }
          ... on Gist {
            description
          }
        }
      }
    }
  }
}
""" % USERNAME

resp = graphql(pinnedq)
data = json.loads(resp)
pinned = []
for node in data["data"]["user"]["pinnedItems"]["edges"]:
    n = node["node"]
    if "nameWithOwner" in n.keys(): 
        pinned_block = textwrap.dedent(f"""
        [] {short(n["nameWithOwner"], p='')}
        {short(remove_emoji(n["description"]).strip())}

        {n["primaryLanguage"]["name"]} ✭ {n["stargazers"]["totalCount"]} ↡ {n["forks"]["totalCount"]}""")
    else:
        pinned_block = textwrap.dedent(f"""
        <> {n["description"]}


        """)
    
    pinned.append(pinned_block)


# hacks

pinnedheader = " Pinned                                                     Customize your pins\n"
pinnedblock = (pinnedheader + sidebyside(table(pinned[0]), table(pinned[1])) + 
              sidebyside(table(pinned[2], t=""), table(pinned[3], t="")) + 
              sidebyside(table(pinned[4], t=""), table(pinned[5], t="")))

final = sidebyside(userblock, pinnedblock)

delta = datetime.now() - starttime

print(f"```\n{final}\n```\n<!--- generated in {delta} -->")
