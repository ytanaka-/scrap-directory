import numpy as np
import networkx as nx
np.seterr(divide='ignore', invalid='ignore')

class ScrapDirectory:

    def in_degree(self, G):
        authorities = []
        for node in set(G.nodes()):
            in_degrees = set(G.predecessors(node))
            authorities.append({
                "name": node,
                "neighbors": list(in_degrees),
                "authority_score": len(list(in_degrees))
            })

        return authorities

    def in_in_degree(self, G, alfa=2):
        authorities = []
        for node in set(G.nodes()):
            in_degrees = set(G.predecessors(node))
            if (len(in_degrees) == 0):
                continue
            authority_score = len(in_degrees)
            for backed in in_degrees:
                backed_in_degrees = set(G.predecessors(backed))
                authority_score += (1 / (alfa ** 1)) * len(backed_in_degrees)

            authorities.append({
                "name": node,
                "neighbors": list(in_degrees),
                "authority_score": authority_score
            })

        return authorities

    def BFS(self, G, alfa=2):
        authorities = []
        # RootとなるNodeを起点に、入リンク, 出リンク, 入リンクを辿って幅優先探索する
        # Back + ForwardBack + BackForwardBackの順に計算
        for node in set(G.nodes()):
            in_degrees = set(G.predecessors(node))
            if (len(in_degrees) == 0):
                continue
            neighbors = list(in_degrees)
            authority_score = len(in_degrees)
            for backed in in_degrees:
                backed_out_degrees = set(G.successors(backed))
                authority_score += (1 / (alfa ** 1)) * len(backed_out_degrees)
                for forwarded in backed_out_degrees:
                    forwarded_in_degrees = set(G.predecessors(forwarded))
                    authority_score += (1 / ((alfa) ** 2)) * len(forwarded_in_degrees)
            authorities.append({
                "name": node,
                "neighbors": neighbors,
                "authority_score": authority_score
            })

        return authorities

    def salsa(self, G, max_iter=50, tol=1.0e-8):
        a = dict.fromkeys(G, 1.0 / G.number_of_nodes())
        for _ in range(max_iter):
            alast = a
            a = dict.fromkeys(alast.keys(), 0)
            for u in a:
                u_ins = set(G.predecessors(u))
                for v in u_ins:
                    v_outs = set(G.successors(v))
                    for w in v_outs:
                        v_w_ins = set(G.predecessors(w))
                        a[u] += alast[w] * (1 / len(v_outs)) * (1 / len(v_w_ins)) 
            err = sum([abs(a[n] - alast[n]) for n in a])
            if err < tol:
                break
        return a

    def create_facets_by_indegree(self, G, SIZE=200, topN=50):
        facets = []
        authorities = self.in_degree(G)
        sorted_authorities = sorted(authorities, key=lambda x:-x["authority_score"])
        sorted_authorities = sorted_authorities[0:topN]
        for node in sorted_authorities:
            name = node["name"]
            neighbors = node["neighbors"]
            facets.append({
                "name": name,
                "neighbors_size": len(neighbors)
            })

        return facets

    def create_facets_by_indegree_mmr(self, G, SIZE=500, topN=50):
        facets = []
        authorities = self.in_degree(G)
        sorted_authorities = sorted(authorities, key=lambda x:-x["authority_score"])
        sorted_authorities = sorted_authorities[0:SIZE]
        max_score = -1
        for node in sorted_authorities:
            name = node["name"]
            neighbors = node["neighbors"]
            score = len(neighbors)
            if max_score == -1 and score != 0:
                max_score = score
            facets.append({
                "name": name,
                "neighbors": neighbors,
                "score": score / max_score
            })
        
        return self.MMR(facets)

    def create_facets_by_pagerank(self, G, topN=50):
        facets = []
        pr = nx.pagerank(G)
        pr = sorted(pr.items(), key=lambda x:-x[1])
        pr = pr[0:topN]
        for node in pr:
            name = node[0]
            facets.append({
                "name": name,
                "neighbors_size": len(set(G.predecessors(name)))
            })
        return facets

    def create_facets_by_pagerank_mmr(self, G, SIZE = 200, topN=50):
        facets = []
        pr = nx.pagerank(G)
        pr = sorted(pr.items(), key=lambda x:-x[1])
        pr = pr[0:SIZE]
        max_score = -1
        for node in pr:
            name = node[0]
            score = node[1]
            neighbors = set(G.predecessors(name))
            if max_score == -1 and score != 0:
                max_score = score
            facets.append({
                "name": name,
                "neighbors": neighbors,
                "score": score / max_score
            })
        
        return self.MMR(facets)

    def MMR(self, nodes, weight=0.5, topN=50):
        _sorted = []
        _selected_item_neighbors = []
        if len(nodes) < topN:
            topN = len(nodes)
        for i in range(topN):
            _max = {
                "name": None,
                "neighbors": None,
                "score": -1,
                "index": -1
            }
            for index,node in enumerate(nodes):
                neighbors = node["neighbors"]
                sim = self.max_sim(neighbors, _selected_item_neighbors)
                # scoreとsimは互いに正規化しておく必要がある
                score = node["score"] * weight - sim * (1 - weight)
                if (score > _max["score"]):
                    _max["name"] = node["name"]
                    _max["neighbors"] = neighbors
                    _max["score"] = score
                    _max["index"] = index
            
            _sorted.append({
                "name": _max["name"],
                "neighbors_size": len(_max["neighbors"])
            })
            _selected_item_neighbors.append(_max["neighbors"])
            del nodes[_max["index"]]

        return _sorted

    def max_sim(self, target, selected):
        max = 0
        for s in selected:
            sim = self.simpson_similarity(target, s)
            if sim > max:
                max = sim
        return max

    def jaccard_similarity(self, x, y):
        x = set(x)
        y = set(y)
        if (len(x) == 0 and len(y) == 0):
            return 0
        intersection = len(set.intersection(*[x, y]))
        union = len(set.union(*[x, y]))
        return intersection / float(union)

    def dice_similarity(self, x, y):
        x = set(x)
        y = set(y)
        if (len(x) == 0 and len(y) == 0):
            return 0
        intersection = len(set.intersection(*[x, y]))
        return 2 * intersection / (len(x) + len(y))

    def simpson_similarity(self, x, y):
        x = set(x)
        y = set(y)
        if (len(x) == 0 or len(y) == 0):
            return 0
        intersection = len(set.intersection(*[x, y]))
        return intersection / min(len(x), len(y))
