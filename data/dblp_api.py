import requests
import pandas as pd
import html

from bs4 import BeautifulSoup


class DblpApi:

    def __init__(self):
        self.session = requests.Session()
        self.author_url = 'http://dblp.org/search/author/api'
        self.pub_url = 'http://dblp.org/search/publ/api'

    def get_pub_list_by_url(self, url):
        req = self.session.get(url)
        soup = BeautifulSoup(req.content, 'html.parser')
        pub_list = [article.get_text() for article in soup.select('span[class="title"]')]
        return pub_list

    def search_pub(self, pub_name):
        params = {
            'q': pub_name,
            'format': 'json',
            'h': 1000,
        }
        req = self.session.get(self.pub_url, params=params)
        data = req.json()
        print(data['result'])

    def search_author(self, author_input):

        # prepare the first query
        params = {
            'q': author_input,
            'format': 'json',
            'h': 1000,
        }
        req = self.session.get(self.author_url, params=params)
        data = req.json()

        if data['result']['status']['@code'] == '200':

            # split the input author name
            author_input_list = author_input.split(' ')
            author_input_length = len(author_input_list)

            # if the first query got no result and the name is ended with a identifier, remove the identifier and retry
            if data['result']['hits']['@total'] == '0' and author_input_list[-1].isdigit():
                author_input_length -= 1
                author_input_list = author_input_list[:author_input_length]
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

                # iterate through all result
                for author in data['result']['hits']['hit']:
                    author_info = author['info']
                    unescaped_name = html.unescape(author_info['author'])
                    author_name_list = unescaped_name.split(' ')

                    found = False
                    # the case that the two names match exactly.
                    if author_input_list == author_name_list:
                        # author_identical.append((author_info['author'], author['@id'], author_info['url']))
                        found = True

                    # it's a duplicate name in the form of the exact name follow by an four digits identifier.
                    elif author_input_length + 1 == len(author_name_list) and author_name_list[-1].isdigit():
                        if author_input_list == author_name_list[:author_input_length]:
                            # author_identical.append((author_info['author'], author['@id'], author_info['url']))
                            found = True

                    # # middle name case, doesn't work for Chinese names.
                    # elif len(author_name_list) == 3 and author_input_length == 2 and not author_name_list[-1].isdigit():
                    #     if author_name_list[0] == author_name_list[0] and author_name_list[2] == author_name_list[2]:
                    #         found = True

                    if found:
                        author_identical.append(
                            (author_info['author'], author['@id'], author_info['url'], author_input))

                    # the case that the author has name aliases
                    elif not found and 'aliases' in author_info:
                        alias = author_info['aliases']['alias']

                        # the author has one alias, and it matches the name exactly
                        if isinstance(alias, str) and html.unescape(alias) == author_input:
                            author_identical.append(
                                (author_info['author'], author['@id'], author_info['url'], author_input))

                        # the author has a list of aliases
                        elif isinstance(alias, list):
                            for a in alias:
                                a_list = html.unescape(a).split(' ')
                                if a_list == author_input_list:
                                    author_identical.append(
                                        (author_info['author'], author['@id'], author_info['url'], author_input))
                                elif author_input_length + 1 == len(a_list) and a_list[-1].isdigit():
                                    if author_input_list == a_list[:author_input_length]:
                                        author_identical.append(
                                            (author_info['author'], author['@id'], author_info['url'], author_input))

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

    dblp = DblpApi()

    df_authors = pd.read_pickle('authors.pkl')
    # df_bad = pd.read_pickle('bad.pkl')
    #
    # df_bad.rename({0: 'author'}, inplace=True, axis=1)
    #
    # counter = 0
    # for row in df_bad.iterrows():
    #     # print(df_authors[df_authors['author'] == row[1]['author']])
    #     x = dblp.search_author(row[1]['author'])
    #     if len(x) == 0:
    #         counter += 1
    #         print(df_authors[df_authors['author'] == row[1]['author']])
    #
    # print(counter)

    # df_article = pd.read_pickle('dblp_article_multi_author.pkl')

    # print(df_article['title'].iloc[0])

    # dblp.search_pub('Object Data Model Facilities for Multimedia Data Types.')

    # print(df_authors['author'][15623])

    # n = 'Frank Manola'
    #
    # x = dblp.search_author(n)
    #
    # print(x)
    #
    # req = dblp.session.get(x[0][2])
    #
    # soup = BeautifulSoup(req.content, 'html.parser')
    #
    # for y in soup.select('span[class="title"]'):
    #     print(y.get_text())
    #
    # pub_author_map = [(article.get_text(), x[0][2]) for article in soup.select('span[class="title"]')]
    #
    # print(pub_author_map)

    # for x in soup.select('#publ-section > div:nth-child(2) > div > ul'):
    #     print(x)

    # for decades in soup.find_all('ul', {'class': 'publ-list'}):
    #     for decade in decades:
    #         for year in decade:
    #             print(year)
    #         print('----------------------------------')
    #     print('111111111')

    upper_bound = 100000

    author_found = []
    author_not_found = []
    author_bad_format = []
    for name in df_authors['author'].tolist()[:upper_bound]:

        try:
            identical_authors = dblp.search_author(name)
            if len(identical_authors) == 0:
                author_not_found.append(name)
            else:
                author_found.extend(identical_authors)
        except Exception:
            print(f'name {name} does not work.')
            author_bad_format.append(name)

    print(f'There are {len(author_not_found)} bad data.')
    print(author_not_found)

    df_not_found = pd.DataFrame(author_not_found)
    df_not_found.to_pickle('author_not_found.pkl')

    df_found = pd.DataFrame(author_found)
    df_found.to_pickle('author_found.pkl')

    df_bad_format = pd.DataFrame(author_bad_format)
    df_bad_format.to_pickle('author_bad_format.pkl')
