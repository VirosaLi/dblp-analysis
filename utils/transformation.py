import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite


def build_student_mentor_graph(edge_list, author_list, name_gender_map, bound):
    students = author_list[author_list['number_publication'] < bound]
    mentors = author_list[author_list['number_publication'] >= bound]
    student_map = {student: 'student' for student in students['author'].tolist()}
    mentor_map = {mentor: 'mentor' for mentor in mentors['author'].tolist()}
    category_map = {**student_map, **mentor_map}

    edge_list['source_category'] = edge_list['source'].map(lambda x: category_map[x])
    edge_list['target_category'] = edge_list['target'].map(lambda x: category_map[x])

    bipartite_edge_list = edge_list[edge_list['source_category'] != edge_list['target_category']]

    edge_list_in_action = bipartite_edge_list.apply(lambda x: (x[0], x[1]), axis=1)

    b = nx.Graph()
    b.add_nodes_from(
        bipartite_edge_list[bipartite_edge_list['source_category'] == 'student']['source'].unique(), bipartite=0)

    b.add_nodes_from(
        bipartite_edge_list[bipartite_edge_list['target_category'] == 'student']['target'].unique(), bipartite=0)

    b.add_nodes_from(
        bipartite_edge_list[bipartite_edge_list['source_category'] == 'mentor']['source'].unique(), bipartite=1)

    b.add_nodes_from(
        bipartite_edge_list[bipartite_edge_list['target_category'] == 'mentor']['target'].unique(), bipartite=1)

    b.add_edges_from(edge_list_in_action)

    nx.set_node_attributes(b, name_gender_map, 'gender')

    return b


def bipartite_biased_preferential_attachment(n, n_0, p_0, m_0, r, rho, g):
    # generate starting graph
    #g = nx.erdos_renyi_graph(n_0, p_0, directed=False)

    while nx.number_of_nodes(g) < n:

        # get degree list
        deg_list = [d for _, d in g.degree()]

        # calculate probability list of edge connection
        prob = deg_list / np.sum(deg_list)

        # sample from existing nodes according to the probability list
        # there is a case that number of nodes is less than the prob list,
        # but I couldn't reproduce that error.
        chosen_nodes = np.random.choice(g.nodes, m_0, replace=False, p=prob)

        # get new node
        new_node = len(deg_list)

        # add node to graph
        g.add_node(new_node)

        # add selected edges
        g.add_edges_from([(new_node, chosen) for chosen in chosen_nodes])
    return g

