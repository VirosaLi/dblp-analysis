import json
import pandas as pd
import numpy as np
import networkx as nx


edge_list = pd.read_csv('dblp_article_duplicate_edge_list.csv')

gender_list = pd.read_csv('gender_list.csv')

gender_list_filtered = gender_list[(gender_list['probability'] > 0.8) & (gender_list['count'] > 1)]

first_name_gender_map = dict(zip(gender_list_filtered['name'].tolist(), gender_list_filtered['gender'].tolist()))

edge_list['first_name_source'] = edge_list['source'].map(lambda x: x.split(' ')[0])
edge_list['first_name_target'] = edge_list['target'].map(lambda x: x.split(' ')[0])

edge_list['gender_source'] = edge_list['first_name_source'].map(lambda x: first_name_gender_map.get(x))
edge_list['gender_target'] = edge_list['first_name_target'].map(lambda x: first_name_gender_map.get(x))

edge_list_filtered = edge_list.dropna()

edge_list_filtered.drop(['first_name_source', 'first_name_target'], inplace=True, axis=1)

edge_list_filtered.to_csv('edge_list_filtered.csv')

names = np.concatenate((edge_list_filtered['source'].tolist(), edge_list_filtered['target'].tolist()), axis=None)
genders = np.concatenate((edge_list_filtered['gender_source'].tolist(), edge_list_filtered['gender_target'].tolist()),
                         axis=None)

name_gender_map = dict(zip(names, genders))

with open('name_gender_map.json', 'w') as file:
    json.dump(name_gender_map, file)


