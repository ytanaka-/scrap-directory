import os
import re
import json
import random
import networkx as nx
import pymongo
import collections
from bottle import route, run, request, abort, template, static_file
from bson.objectid import ObjectId
from pymongo import MongoClient
from directory import ScrapDirectory
directory = ScrapDirectory()

HOST = os.getenv('HOST', 'localhost')
PORT = int(os.getenv('PORT', 8080))
DEBUG_FLAG = os.getenv('DEBUG_FLAG', True)
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017/')
ROOT_SET_LIMIT = 10000
PAGE_SIZE = 50
STOPWORD_THRESHOLD = 0.5

# set mongo config
client = MongoClient(MONGO_URL)
Page = client["scrap-directory"].pages
Project = client["scrap-directory"].projects

def create_graph_from_root_set(root_set, isSampling=False):
    base_set = { page["title"]: page for page in root_set }
    base_set_size = len(base_set)
    G = nx.DiGraph()
    G.add_nodes_from(base_set.keys())

    for page in base_set.values():
        title = page['title']
        olinks = page['olinks']
        if isSampling:
            random.shuffle(olinks)
            if len(olinks) > 5:
                olinks = olinks[:5]
            else:
                olinks = olinks[:1]
        for link in olinks:
            if not G.has_node(link):
                G.add_node(link)
            G.add_edge(title, link)

    # remove stop-word
    for node in set(G.nodes()):
        in_degree_size = len(set(G.predecessors(node)))
        if in_degree_size/base_set_size > STOPWORD_THRESHOLD:
            G.remove_node(node)
    
    # 入と出次数が共に少なすぎるものは削除
    for node in set(G.nodes()):
        in_degree_size = len(set(G.predecessors(node)))
        out_degree_size = len(set(G.successors(node)))
        if in_degree_size < 1 and out_degree_size < 1:
            G.remove_node(node)

    return G

def create_facet(root_set, algorithm, base_facet_size=200, facet_size=50):
    if (algorithm == "Random"):
        G = create_graph_from_root_set(root_set,True)
    else:
        G = create_graph_from_root_set(root_set)
    
    if (algorithm == "InDegree"):
        return directory.create_facets_by_indegree(G)
    if (algorithm == "InDegree-MMR"):
        return directory.create_facets_by_indegree_mmr(G)
    if (algorithm == "PageRank"):
        return directory.create_facets_by_pagerank(G)
    if (algorithm == "Random"):
        return directory.create_facets_by_indegree(G)

    return []

def create_page_response(pages):
    _pages = []
    for page in pages:
        title = page["title"]
        url = page["url"]
        text = page["text"].replace("\n", "")
        if len(text) >= 200:
            text = text[0:200] + "..." 
        _pages.append({
            "url": url,
            "title": title,
            "description": text
        })
    
    return _pages

@route("/")
def index():
    return template('index')

@route("/js/bundle.js")
def js():
    return static_file("bundle.js", "./static/js")

@route('/img/<file_path:path>')
def img(file_path):
    return static_file(file_path, root='./static/img')

@route('/api/projects')
def get_projects():
    projects = list(Project.find())
    projects = [{"name": project["name"]} for project in projects]
    return json.dumps({ "projects": projects }, ensure_ascii=False)

@route('/api/pages')
def get_pages():
    project = request.query.project
    algorithm = request.query.algorithm

    root_set = Page.find({"project": project}, projection={'title':1, 'olinks':1}).limit(ROOT_SET_LIMIT)
    facets = create_facet(list(root_set), algorithm)
    
    # 検索結果で表示する分
    pages = Page.find({"project": project}, projection={'title':1, 'text':1, 'url': 1}).limit(PAGE_SIZE).sort('updated', pymongo.DESCENDING)
    pages = create_page_response(list(pages))

    return json.dumps({ "facets": facets, "pages": pages }, ensure_ascii=False)

@route('/api/search')
def search():
    project = request.query.project
    algorithm = request.query.algorithm
    q = request.query.q
    if not q:
        q = ""
    _q = q.split(" ")
    text_and_query = []
    title_and_query = []
    for __q in _q:
        text_and_query.append({
            "text": re.compile(__q)
        })
        title_and_query.append({
            "title": re.compile(__q)
        })

    root_set = Page.find({"project": project, "$or": [{"$and": title_and_query},{"$and": text_and_query}] }, projection={'title':1, 'olinks':1}).limit(ROOT_SET_LIMIT)
    facets = create_facet(list(root_set), algorithm)

    pages = Page.find({"project": project, "$or": [{"$and": title_and_query},{"$and": text_and_query}] }, projection={'title':1, 'text':1, 'url': 1}).limit(PAGE_SIZE).sort('updated', pymongo.DESCENDING)
    pages = create_page_response(list(pages))

    return json.dumps({ "facets": facets, "pages": pages }, ensure_ascii=False)


@route('/api/search/facet')
def facetedSearch():
    project = request.query.project
    algorithm = request.query.algorithm
    query_facets = request.query.facets
    if not query_facets:
        abort(500)
    _query_facets = query_facets.split(" ")

    q = request.query.q
    if not q:
        q = ""
    _q = q.split(" ")
    text_and_query = []
    title_and_query = []
    for __q in _q:
        text_and_query.append({
            "text": re.compile(__q)
        })
        title_and_query.append({
            "title": re.compile(__q)
        })

    # search-queryを含む場合とそうでない場合の2種類がある
    # root_setとpagesで分けているのはユーザに返すpagesの件数はPAGE_SIZEだけあればよいため
    if q == "":
        root_set = Page.find({"project": project, "olinks": { "$all": _query_facets }}, projection={'title':1, 'olinks':1}).limit(ROOT_SET_LIMIT)
        pages = Page.find({"project": project, "olinks": { "$all": _query_facets }}, projection={'title':1, 'text':1, 'url': 1}).limit(PAGE_SIZE).sort('updated', pymongo.DESCENDING)
    else:
        root_set = Page.find({"project": project, "$or": [{"$and": title_and_query},{"$and": text_and_query}], "olinks": { "$all": _query_facets }}, projection={'title':1, 'olinks':1}).limit(ROOT_SET_LIMIT)
        pages = Page.find({"project": project, "$or": [{"$and": title_and_query},{"$and": text_and_query}], "olinks": { "$all": _query_facets }}, projection={'title':1, 'text':1, 'url': 1}).limit(PAGE_SIZE).sort('updated', pymongo.DESCENDING)
    facets = create_facet(list(root_set), algorithm)
    _facets = []
    # facetsのqueryに含まれているものは除く
    for facet in facets:
        if not facet["name"] in query_facets:
            _facets.append(facet)
    
    pages = create_page_response(list(pages))

    return json.dumps({ "facets": _facets, "pages": pages }, ensure_ascii=False)

run(host=HOST, port=PORT, debug=DEBUG_FLAG)