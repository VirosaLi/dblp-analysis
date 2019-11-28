import requests
import pandas as pd
from tqdm import tqdm


class DblpApi:

    def __init__(self):
        self.session = requests.Session()
        self.author_url = 'http://dblp.org/search/author/api'

    def search_author(self, author_input):
        params = {
            'q': author_input,
            'format': 'json',
            'h': 1000,
        }

        req = self.session.get(self.author_url, params=params)

        data = req.json()

        if data['result']['status']['@code'] == '200':

            if data['result']['hits']['@total'] == '0':

                author_input_list = author_input.split(' ')

                if author_input_list[-1].isdigit():
                    author_input_list = author_input_list[:len(author_input_list)-1]
                    params = {
                        'q': ' '.join(author_input_list),
                        'format': 'json',
                        'h': 1000,
                    }
                    req = self.session.get(self.author_url, params=params)
                    data = req.json()

            author_identical = []
            curr_counter = data['result']['hits']['@sent']
            while True:

                author_list = data['result']['hits']['hit']

                # print(author_list)
                author_input_list = author_input.split(' ')
                author_input_length = len(author_input_list)

                # iterate through all result
                for author in author_list:
                    author_info = author['info']
                    author_name_list = author_info['author'].split(' ')

                    # the case that the two names match exactly.
                    if author_input_list == author_name_list:
                        author_identical.append((author_info['author'], author['@id'], author_info['url']))

                    # it's a duplicate name in the form of the exact name follow by an four digits identifier.
                    elif author_input_length + 1 == len(author_name_list) and author_name_list[-1].isdigit():
                        if author_input_list == author_name_list[:author_input_length]:
                            author_identical.append((author_info['author'], author['@id'], author_info['url']))

                    # the case that the author has name aliases
                    elif 'aliases' in author_info:
                        alias = author_info['aliases']['alias']

                        # the author has one alias, and it matches the name exactly
                        if alias == author_input:
                            author_identical.append((author_info['author'], author['@id'], author_info['url']))

                        # the author has a list of aliases
                        elif isinstance(alias, list):
                            for a in alias:
                                a_list = a.split(' ')
                                if a_list == author_input_list:
                                    author_identical.append((author_info['author'], author['@id'], author_info['url']))
                                elif author_input_length + 1 == len(a_list) and a_list[-1].isdigit():
                                    if author_input_list == a_list[:author_input_length]:
                                        author_identical.append(
                                            (author_info['author'], author['@id'], author_info['url']))

                if curr_counter < data['result']['hits']['@total']:
                    params = {
                        'q': author_input,
                        'format': 'json',
                        'h': 1000,
                        'f': curr_counter,
                    }

                    req = self.session.get(self.author_url, params=params)

                    data = req.json()

                    if data['result']['hits']['@sent'] == '0':
                        break

                    curr_counter += data['result']['hits']['@sent']
                else:
                    break

            return author_identical


if __name__ == '__main__':

    df_authors = pd.read_pickle('authors.pkl')
    # print(df_authors)

    dblp = DblpApi()

    # print(df_authors['author'][15623])

    # dblp.search_author(df_authors['author'][15623])

    result = []
    bad_data = []
    for name in tqdm(df_authors['author'].tolist()):

        try:
            identical_authors = dblp.search_author(name)
            if len(identical_authors) == 0:
                bad_data.append(name)
            else:
                result.extend(identical_authors)
        except Exception:
            print(f'name {name} does not work.')

    print(f'There are {len(bad_data)} bad data.')
    print(bad_data)

    df_bad = pd.DataFrame(bad_data)
    df_bad.to_pickle('bad.pkl')

    df_result = pd.DataFrame(result)
    df_result.to_pickle('author_result.pkl')

    # dblp.search_author('Li Chen')

    # str = 'Wei Zhang'
    #
    # text = "Wei Zhang You 0110"
    # text2 = "Wss"
    #
    # m = re.search(f'((?:^|\\W\\.){str}($|))|{str}\\s\\d+', text)
    #
    # if m:
    #     print('wow')
    # else:
    #     print('11')
