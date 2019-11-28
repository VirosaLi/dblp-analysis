import re
import requests
from bs4 import BeautifulSoup


class GenderCrawler:

    def __init__(self):
        self.session = requests.Session()
        self.url = "https://en.wikipedia.org/w/api.php"
        self.male_word = ['he', 'him', 'his']
        self.female_word = ['she', 'her']

    @staticmethod
    def html_to_text(wiki_page_html):
        soup = BeautifulSoup(wiki_page_html, features='lxml')
        return soup.body.get_text(separator=' ').lower()

    @staticmethod
    def count(word, input_text):
        return sum(1 for _ in re.finditer(r'\b%s\b' % re.escape(word), input_text))

    def request_page(self, page_name):
        params = {
            'action': 'parse',
            'page': page_name,
            'format': 'json'
        }
        req = self.session.get(self.url, params=params)

        data = req.json()

        return data

    def gender_guesser(self, page_name):

        res = self.request_page(page_name)

        if 'error' in res:
            return res['error']['info']
        else:
            text = GenderCrawler.html_to_text(res['parse']['text']['*'])

            male_occ = [GenderCrawler.count(word, text) for word in self.male_word]

            female_occ = [GenderCrawler.count(word, text) for word in self.female_word]

            return 0 if sum(female_occ) > sum(male_occ) else 1


if __name__ == '__main__':
    gc = GenderCrawler()
    author = 'Fei-Fe Li'

    gender = gc.gender_guesser(author)

    print(gender)
