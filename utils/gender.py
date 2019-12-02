import re
import time
from urllib.parse import urlparse
from urllib3.exceptions import MaxRetryError, SSLError
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import logging

import pandas as pd

import ssl
import OpenSSL

from tqdm import tqdm


class GenderCrawler:

    def __init__(self):
        self.session = requests.Session()
        self.wiki_url = "https://en.wikipedia.org/w/api.php"
        self.male_word = ['he', 'him', 'his']
        self.female_word = ['she', 'her']
        self.skipping_domain = ['www.linkedin.com']
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/61.0.3163.100 Safari/537.36'}

    @staticmethod
    def html_to_text(wiki_page_html):
        soup = BeautifulSoup(wiki_page_html, features='lxml')
        if soup.body is None:
            return None
        return soup.body.get_text(separator=' ').lower()

    @staticmethod
    def count(word, input_text):
        return sum(1 for _ in re.finditer(r'\b%s\s\b' % re.escape(word), input_text))

    @staticmethod
    def google_search(search_word):
        try:
            search_result = [url for url in search(search_word, stop=5)]
            return search_result
        except SSLError:
            logging.error(f'Error occurred while searching {search_word}.')
            return []

    def request_page(self, url):
        try:
            req = self.session.get(url, verify=True, headers=self.headers)
            return req.content
        except (requests.exceptions.SSLError, MaxRetryError, ssl.SSLError, OpenSSL.SSL.Error):
            logging.error(f'Error occurred while requesting {url}.')
            return None

    def gender_guesser(self, page_name):

        male_count = 0
        female_count = 0

        search_result = self.google_search(page_name)
        if len(search_result) == 0:
            return 3

        for url in search_result:
            url_comp = urlparse(url)
            if url_comp.netloc in self.skipping_domain:
                continue

            content = self.request_page(url)

            if content is None:
                continue

            text = GenderCrawler.html_to_text(content)

            if not isinstance(text, str):
                logging.error(f'Error occurred while parsing {url}')
                continue

            male_occ = [GenderCrawler.count(word, text) for word in self.male_word]
            female_occ = [GenderCrawler.count(word, text) for word in self.female_word]
            # print(url, male_occ, female_occ)
            male_count += sum(male_occ)
            female_count += sum(female_occ)

        if female_count > male_count:
            return 0
        elif male_count > female_count:
            return 1
        else:
            return 3


if __name__ == '__main__':
    # gc = GenderCrawler()
    # author = 'Lajos Hanzo'
    # g = gc.gender_guesser(author)
    # print(author)
    # print(g)

    authors = pd.read_pickle('../data/authors.pkl')
    great_authors = authors[(authors['number_publication'] > 100) & (authors['number_publication'] <= 300)]
    gc = GenderCrawler()
    # genders = [gc.gender_guesser(author) for author in tqdm(great_authors['author'].tolist())]
    # author_gender = pd.DataFrame(genders)
    # author_gender.to_csv('../data/authors_with_gender_100.csv', index=None)

    for author in great_authors.loc[128:140, 'author'].tolist():
        x = gc.gender_guesser(author)
        print(author, x)
