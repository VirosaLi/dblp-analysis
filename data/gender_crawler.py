import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

from googlesearch import search


class GenderCrawler:

    def __init__(self):
        self.session = requests.Session()
        self.wiki_url = "https://en.wikipedia.org/w/api.php"
        self.male_word = ['he', 'him', 'his']
        self.female_word = ['she', 'her']
        self.skipping_domain = ['www.linkedin.com']

    @staticmethod
    def html_to_text(wiki_page_html):
        soup = BeautifulSoup(wiki_page_html, features='lxml')
        return soup.body.get_text(separator=' ').lower()

    @staticmethod
    def count(word, input_text):
        return sum(1 for _ in re.finditer(r'\b%s\s\b' % re.escape(word), input_text))

    @staticmethod
    def google_search(search_word):
        return [url for url in search(search_word, stop=5)]

    def request_page(self, url):
        req = self.session.get(url)
        return req.content

    def gender_guesser(self, page_name):

        male_count = 0
        female_count = 0
        for url in self.google_search(page_name):
            url_comp = urlparse(url)
            if url_comp.netloc in self.skipping_domain:
                continue
            text = GenderCrawler.html_to_text(self.request_page(url))
            male_occ = [GenderCrawler.count(word, text) for word in self.male_word]
            female_occ = [GenderCrawler.count(word, text) for word in self.female_word]
            print(url, male_occ, female_occ)
            male_count += sum(male_occ)
            female_count += sum(female_occ)

        return 0 if female_count > male_count else 1


if __name__ == '__main__':
    gc = GenderCrawler()
    author = 'ning zhang'

    print(gc.gender_guesser(author))
