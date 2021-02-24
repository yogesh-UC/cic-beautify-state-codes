from bs4 import BeautifulSoup, Doctype, element
import re
from datetime import datetime
from parser_base import ParserBase


class KYParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.class_regex = {'ul': '^CHAPTER', 'head2': '^CHAPTER', 'title': '^(TITLE)', 'sec_head': r'^([^\s]+[^\D]+)',
                            'junk': '^(Text)', 'ol': r'^(\d+)|^([(]\d+[)]|^[(]\D[)])', 'head4': '^(NOTES TO DECISIONS)',
                            }
        self.title_id = None
        self.soup = None
        self.start_parse()

    def create_page_soup(self):

        with open(f'../transforms/ky/ocky/r{self.release_number}/raw/{self.html_file_name}') as open_file:
            html_data = open_file.read()
        self.soup = BeautifulSoup(html_data, features="lxml")
        self.soup.contents[0].replace_with(Doctype("html"))
        self.soup.html.attrs['lang'] = 'en'
        print('created soup')

    def get_class_name(self):
        for key, value in self.class_regex.items():
            tag_class = self.soup.find(
                lambda tag: tag.name == 'p' and re.search(self.class_regex.get(key), tag.get_text().strip()) and
                            tag.attrs["class"][0] not in self.class_regex.values())
            if tag_class:
                self.class_regex[key] = tag_class.get('class')[0]
        print('updated class dict')

    def remove_junk(self):
        [span.unwrap() if span["class"] == ['Apple-converted-space'] else span.decompose() for span in
         self.soup.findAll("span")]
        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.class_regex["junk"])]
        for b_tag in self.soup.findAll("b"):
            b_tag.name = "span"
            b_tag["class"] = "boldspan"
        print('junk removed')

    def write_soup_to_file(self):
        soup_str = str(self.soup.prettify(formatter=None))
        with open(f"../transforms/ga/ocga/r{self.release_number}/{self.html_file_name}", "w") as file:
            file.write(soup_str)

    def start_parse(self):
        self.release_label = f'Release-{self.release_number}'
        print(self.html_file_name)
        start_time = datetime.now()
        print(start_time)
        self.create_page_soup()
        self.get_class_name()
        self.remove_junk()
        self.write_soup_to_file()
        print(datetime.now() - start_time)
