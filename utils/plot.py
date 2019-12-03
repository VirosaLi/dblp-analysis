import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from utils.transformation import estimate_pdf_from_ccdf


def degree_distribution_comparison_plot(g):

    # get node list and node-degree map
    node_list = list(g.nodes(data=True))
    degree_map = dict(list(g.degree()))

    # select female and male nodes and create degree sequence
    female_node = [node[0] for node in node_list if node[1]['gender'] == 'female']
    female_degree_sequence = [degree_map[node] for node in female_node]

    male_node = [node[0] for node in node_list if node[1]['gender'] == 'male']
    male_degree_sequence = [degree_map[node] for node in male_node]

    unique_female, counts_female = np.unique(female_degree_sequence, return_counts=True)
    counts_map = np.asarray((unique_female, counts_female)).T
    pdf_empirical_female = counts_map[:, 1] / np.sum(counts_map[:, 1])

    unique_male, counts_male = np.unique(male_degree_sequence, return_counts=True)
    counts_map = np.asarray((unique_male, counts_male)).T
    pdf_empirical_male = counts_map[:, 1] / np.sum(counts_map[:, 1])

    pdf_estimated_female = estimate_pdf_from_ccdf(unique_female, pdf_empirical_female, female_degree_sequence, 1)
    pdf_estimated_male = estimate_pdf_from_ccdf(unique_male, pdf_empirical_male, male_degree_sequence, 1)
    x_line_female = np.arange(min(female_degree_sequence), max(female_degree_sequence))
    x_line_male = np.arange(min(male_degree_sequence), max(male_degree_sequence))

    _, ax = plt.subplots()
    ax.loglog(unique_female, pdf_empirical_female, 'r.', label='female')
    ax.loglog(x_line_female, pdf_estimated_female, 'r-')
    ax.loglog(unique_male, pdf_empirical_male, 'b.', label='male')
    ax.loglog(x_line_male, pdf_estimated_male, 'b-')
    ax.legend(loc='upper right', shadow=True, fontsize='x-large')
    plt.title('Degree Distribution')
    plt.xlabel('k')
    plt.ylabel('p_k')
    plt.show()


def female_degree_fraction_plot(g, upper_bound):

    # get node list and degree map
    node_list = list(g.nodes(data=True))
    degree_list = list(g.degree())
    degree_map = dict(degree_list)

    # count all nodes
    total_degree = [node[1] for node in degree_list]
    unique_total, counts_total = np.unique(total_degree, return_counts=True)
    counts_total = np.cumsum(counts_total[::-1])[::-1]

    # count female nodes
    female_node = [node[0] for node in node_list if node[1]['gender'] == 'female']
    female_degree_sequence = [degree_map[node] for node in female_node]
    _, counts_female = np.unique(female_degree_sequence, return_counts=True)
    padded_female_counts = np.zeros_like(counts_total)
    padded_female_counts[:counts_female.shape[0]] = counts_female
    padded_female_counts = np.cumsum(padded_female_counts[::-1])[::-1]

    p = padded_female_counts / counts_total
    _, ax = plt.subplots()
    ax.loglog(unique_total[:upper_bound], p[:upper_bound], 'r.')
    plt.title('Percentage of Female...')
    plt.xlabel('Degree')
    plt.ylabel('Percentage')
    plt.show()


def stacked_degree_fraction_over_year(df, name_gender, year_start, year_end):

    years = range(year_start, year_end + 1, 5)
    female = []
    male = []
    female_expected = []
    for year in years:
        data_filtered = df[df['year'] <= year]
        g = nx.from_pandas_edgelist(data_filtered)
        nx.set_node_attributes(g, name_gender, 'gender')

        # get node list and degree map
        node_list = list(g.nodes(data=True))
        degree_map = dict(list(g.degree()))

        # select female and male nodes and create degree sequence
        female_node = [node[0] for node in node_list if node[1]['gender'] == 'female']
        female_degree_sequence = [degree_map[node] for node in female_node]

        male_node = [node[0] for node in node_list if node[1]['gender'] == 'male']
        male_degree_sequence = [degree_map[node] for node in male_node]

        female_degree_sum = sum(female_degree_sequence)
        male_degree_sum = sum(male_degree_sequence)
        total_degree_sum = female_degree_sum + male_degree_sum

        female_fraction = female_degree_sum / total_degree_sum
        male_fraction = male_degree_sum / total_degree_sum
        female.append(female_fraction)
        male.append(male_fraction)

        num_female = len(female_node)
        num_male = len(male_node)
        num_total = num_female + num_male
        female_expected.append(num_female / num_total)

    n = len(years)
    ind = np.arange(n)
    width = 0.35
    p_female = plt.bar(ind, female, width, color='r')
    p_male = plt.bar(ind, male, width, bottom=female, color='b')
    plt.plot(ind, female_expected)
    plt.ylabel('Cumulative Degree Sum as Percentage of Total Degree Sum')
    plt.xlabel('Year')
    plt.xticks(ind, years)
    plt.legend((p_female[0], p_male[0]), ('Female', 'Male'))
    plt.show()


def mixed_edges_over_year(df, name_gender, year_start, year_end):

    result = []
    exp = []
    exp_norm = []
    years = range(year_start, year_end + 1, 5)
    for year in years:
        data_filtered = df[df['year'] <= year]

        # expected num of mixed
        g = nx.from_pandas_edgelist(data_filtered)
        nx.set_node_attributes(g, name_gender, 'gender')
        node_list = list(g.nodes(data=True))
        female_node = [node[0] for node in node_list if node[1]['gender'] == 'female']
        male_node = [node[0] for node in node_list if node[1]['gender'] == 'male']
        num_female = len(female_node)
        num_male = len(male_node)
        num_total = num_female + num_male
        degree_map = dict(list(g.degree()))
        female_degree_sequence = [degree_map[node] for node in female_node]
        male_degree_sequence = [degree_map[node] for node in male_node]
        female_degree_sum = sum(female_degree_sequence)
        male_degree_sum = sum(male_degree_sequence)
        total_degree_sum = female_degree_sum + male_degree_sum

        r = num_female / num_total
        exp.append(r * (1 - r) * total_degree_sum)

        # normalized expected
        r_norm = female_degree_sum / total_degree_sum
        exp_norm.append(r_norm * (1 - r_norm) * total_degree_sum)

        # observed mixed edges
        data_mixed_edge = data_filtered[data_filtered['gender_source'] != data_filtered['gender_target']]
        g = nx.from_pandas_edgelist(data_mixed_edge)
        result.append(nx.number_of_edges(g))

    _, ax = plt.subplots()
    plt.plot(years, result, 'k.', label='observed mixed edges')
    plt.plot(years, exp, color='b', label='E[mixed edges] observed female frac, assume equal degree and no homophily')
    plt.plot(years, exp_norm, color='g', label='E[mixed edges] observed degree, assume no homophily')
    ax.legend(loc='upper right', shadow=True, fontsize='x-large')
    plt.ylabel('Cumulative Number of Mixed Edges')
    plt.xlabel('Year')
    plt.show()
