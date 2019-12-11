from itertools import combinations
from collections import Counter

import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite


def generate_edge_list(df: pd.DataFrame) -> pd.DataFrame:
    df['pairs'] = df['author'].map(lambda x: list(combinations(x, 2)))
    edge_list = pd.DataFrame(
        [(pair[0], pair[1], row.year) for row in df.itertuples() for pair in row.pairs],
        columns=['source', 'target', 'year'])
    return edge_list


def generate_author_list(df: pd.DataFrame) -> pd.DataFrame:

    # flatten the data
    df_expand = pd.DataFrame(
        [(author, row.year) for row in df.itertuples() for author in row.author], columns=['author', 'year'])

    # get unique authors and publication count
    unique_author, pub_count = np.unique(df_expand['author'].tolist(), return_counts=True)
    author_count_map = dict(zip(unique_author, pub_count))

    # build author df
    top_author = sorted(author_count_map.items(), key=lambda x: x[1], reverse=True)
    df_authors = pd.DataFrame(top_author, columns=['author', 'number_publication'])

    # get earliest publication year for each author
    author_early_year = df_expand.groupby(['author']).min()

    # join two df on author
    return df_authors.join(author_early_year, on='author')


def find_mentor(df_author: pd.DataFrame, edge_list: pd.DataFrame, mentor_difference: int) -> pd.DataFrame:
    author_year_map = dict(zip(df_author['author'].tolist(), df_author['year'].tolist()))
    mentor_candidates = {}
    for row in edge_list.itertuples():
        author1 = row.source
        author2 = row.target

        young = author1 if author_year_map[author1] > author_year_map[author2] else author2
        old = author2 if author_year_map[author1] > author_year_map[author2] else author1

        if author_year_map[young] > author_year_map[old] + mentor_difference:
            if author_year_map[young] + mentor_difference > int(row.year):
                if young in mentor_candidates:
                    mentor_candidates[young].append(old)
                else:
                    mentor_candidates[young] = []

    author_mentor_map = {}
    for author, mentor_list in mentor_candidates.items():
        if len(mentor_list) > 0:
            author_mentor_map[author] = Counter(mentor_list).most_common(1)[0][0]

    df_mentor = pd.DataFrame(author_mentor_map.items(), columns=['author', 'mentor'])

    return df_author.merge(df_mentor, on='author')


def pre_processing(file_path: str, max_coauthor: int) -> pd.DataFrame:
    df = pd.read_csv(file_path, sep=';', low_memory=False)
    df = df[['id', 'author', 'title', 'year']]
    df.dropna(inplace=True)
    df['year'] = df['year'].astype('int64')
    df['author'] = df['author'].str.split('|')
    num_author_list = df['author'].map(lambda x: len(x))
    df = df[(num_author_list > 1) & (num_author_list < max_coauthor)]
    df.reset_index(drop=True, inplace=True)
    return df


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
    # g = nx.erdos_renyi_graph(n_0, p_0, directed=False)

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


def estimate_pdf_from_ccdf(unique, pdf_empirical, sequence, k_min):
    ccdf = 1 - np.cumsum(pdf_empirical)
    ccdf_dict = dict(zip(unique, ccdf))
    x = np.log(np.array(sequence) / k_min)
    ccdf_prob = [ccdf_dict[i] for i in sequence]
    y = np.log(ccdf_prob)
    A = np.vstack([x, np.ones(len(x))]).T
    m, _ = np.linalg.lstsq(A, y, rcond=None)[0]
    alpha = 1 - m
    x_line = np.arange(min(sequence), max(sequence))
    pdf_estimated = (alpha - 1) * np.power(k_min, alpha - 1) * np.power(x_line, -alpha)
    return pdf_estimated
