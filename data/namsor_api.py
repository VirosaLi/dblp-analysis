import requests


class NamSorApi:
    def __init__(self):
        self.session = requests.Session()
        self.api_key = '413812fd8476a9e0de01dd260f944ea7'
        self.headers = {'accept': 'application/json', 'X-API-KEY': self.api_key}

    @staticmethod
    def build_gender_url(name):
        return f'https://v2.namsor.com/NamSorAPIv2/api2/json/genderFull/{name}'

    def get_gender(self, name):
        req = self.session.get(NamSorApi.build_gender_url(name), headers=self.headers)

        data = req.json()

        return data


if __name__ == '__main__':
    namesor = NamSorApi()
    gender = namesor.get_gender('Amelia Xu')
    print(gender)
