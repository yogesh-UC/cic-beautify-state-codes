
"""
    - this file accepts the text util generated html and parse it
    - here the html is converted in such a way that it matches the html5 standards
    - the start_parse method is called by parser base
    - this method based on the file type(constitution files or title files) decides which methods to run
"""


from bs4 import BeautifulSoup, Doctype
import re
from datetime import datetime
from parser_base import ParserBase
import roman


class KYParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.class_regex = {'ul': '^CHAPTER', 'head2': '^CHAPTER', 'title': '^(TITLE)|^(CONSTITUTION OF KENTUCKY)',
                            'sec_head': r'^([^\s]+[^\D]+)',
                            'junk': '^(Text)', 'ol': r'^(\(1\))', 'head4': '^(NOTES TO DECISIONS)'}
        self.title_id = None
        self.soup = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.html_file_name = input_file_name

        self.watermark_text = """Release {0} of the Official Code of Kentucky Annotated released {1}.
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 1.4 on {2}.
        This document is not subject to copyright and is in the public domain.
        """

        self.start_parse()

    def create_page_soup(self):

        """
        - Read the input html to parse and convert it to Beautifulsoup object
        - Input Html will be html 4 so replace html tag which is self.soup.contents[0] with <html>
          which is syntax of html tag in html 5
        - add attribute 'lang' to html tag with value 'en'
        :return:
        """

        with open(f'transforms/ky/ocky/r{self.release_number}/raw/{self.html_file_name}') as open_file:
            html_data = open_file.read()
        self.soup = BeautifulSoup(html_data, features="lxml")
        self.soup.contents[0].replace_with(Doctype("html"))
        self.soup.html.attrs['lang'] = 'en'
        print('created soup')

    def get_class_name(self):

        """
                    - Find the textutil generated class names for each type of tag (h1, h2, ....)
                      using re pattern specified in self.tag_type_dict
        """
        for key, value in self.class_regex.items():
            tag_class = self.soup.find(
                lambda tag: tag.name == 'p' and re.search(self.class_regex.get(key), tag.get_text().strip()) and
                            tag.attrs["class"][0] not in self.class_regex.values())
            if tag_class:
                self.class_regex[key] = tag_class.get('class')[0]

        print(self.class_regex)
        print('updated class dict')

    def remove_junk(self):
        for junk_tag in self.soup.find_all():
            if junk_tag.get("class") == ['Apple-converted-space'] or junk_tag.name == "i":
                junk_tag.unwrap()
            elif junk_tag.get("class") == ['Apple-tab-span']:
                junk_tag.decompose()
            elif junk_tag.name == "br":
                if junk_tag.parent.name == "p":
                    junk_tag.name = "span"
                    junk_tag["class"] = "gnrlbreak"
                else:
                    junk_tag.name = "span"
                    junk_tag["class"] = "headbreak"

        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.class_regex["junk"])]
        for b_tag in self.soup.findAll("b"):
            b_tag.name = "span"
            b_tag["class"] = "boldspan"

        for meta in self.soup.findAll('meta'):
            if meta.get('name') and meta.get('name') in ['Author', 'Description']:
                meta.decompose()

        for key, value in {'viewport': "width=device-width, initial-scale=1",
                           'description': self.watermark_text.format(self.release_number, self.release_date,
                                                                     datetime.now().date())}.items():
            new_meta = self.soup.new_tag('meta')
            new_meta.attrs['name'] = key
            new_meta.attrs['content'] = value
            self.soup.head.append(new_meta)

        print('junk removed')

    # wrap list items with ul tag
    def create_ul_tag(self):
        if re.search('constitution', self.html_file_name):
            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
            for list_item in self.soup.find_all("li"):
                if list_item.find_previous().name == "li":
                    ul_tag.append(list_item)
                else:
                    ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    list_item.wrap(ul_tag)

                    if re.match(r'Preamble', ul_tag.find_previous().text.strip()):
                        ul_tag.find_previous("nav").append(ul_tag.find_previous())
                        ul_tag.find_previous("nav").append(ul_tag)

        else:
            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
            for list_item in self.soup.find_all("li"):
                if list_item.find_previous().name == "li":
                    ul_tag.append(list_item)
                else:
                    ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    list_item.wrap(ul_tag)

                    if ul_tag.find_previous().find_previous().name == "h1":
                        ul_tag.find_previous("nav").append(ul_tag)
                    else:
                        ul_tag.wrap(self.soup.new_tag("nav"))

        print("ul tag is created")

    # wrap the main content
    def create_main_tag(self):
        section_nav_tag = self.soup.new_tag("main")
        first_chapter_header = self.soup.find(class_=self.class_regex["head2"])

        if re.search('constitution', self.html_file_name):
            for main_tag in self.soup.find_all("p"):
                if main_tag.text.strip() == "CONSTITUTION OF KENTUCKY":
                    continue
                elif main_tag.text.strip() == "THE CONSTITUTION OF THE UNITED STATES OF AMERICA":
                    continue
                elif re.match(r'Preamble|SCHEDULE|ORDINANCE', main_tag.text.strip()) and main_tag.get("class") == [
                    self.class_regex['ul']]:
                    continue
                elif re.match(r'^§(§)*|^ARTICLE|^AMENDMENTS', main_tag.text.strip()) and main_tag.get("class") == [
                    self.class_regex["ul"]]:
                    continue
                elif main_tag == first_chapter_header:
                    main_tag.wrap(section_nav_tag)
                else:
                    section_nav_tag.append(main_tag)

        else:
            for main_tag in self.soup.find_all("p"):
                if re.match(r'^(TITLE)', main_tag.text.strip()):
                    continue
                elif re.match(r'^CHAPTER|^Chapter', main_tag.text.strip()) and main_tag.get("class") == [
                    self.class_regex["ul"]]:
                    continue
                elif main_tag == first_chapter_header:
                    main_tag.wrap(section_nav_tag)
                else:
                    section_nav_tag.append(main_tag)

        print("main tag is created")

    # # wrapping with ol tag
    # def wrap_with_ordered_tag1(self):
    #     pattern = re.compile(r'^(\d+)|^([(]\d+[)]|^[(]\s*[a-z][a-z]?\s*[)])|^(\D\.)')
    #     Num_bracket_pattern = re.compile(r'^\(\d+\)')
    #     alpha_pattern = re.compile(r'^\([a-z][a-z]?\)')
    #     # alp_pattern = re.compile(r'\(\D+\)')
    #     num_pattern = re.compile(r'^\d+\.')
    #     # num_pattern1 = re.compile(r'^1\.')
    #     numAlpha_pattern = re.compile(r'^\(\d+\)\s\(\D\)')
    #     alphanum_pattern = re.compile(r'^\(\D+\)\s(\d)+')
    #
    #     ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #     ol_tag = self.soup.new_tag("ol")
    #     ol_tag3 = self.soup.new_tag("ol")
    #     ol_tag1 = self.soup.new_tag("ol")
    #     ol_tag4 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #     ol_tag5 = self.soup.new_tag("ol")
    #
    #     ol_num = None
    #     ol_alpha = None
    #     ol_inr_num = None
    #     ol_inr_apha = None
    #
    #     for tag in self.soup.findAll("p", class_=self.class_regex["ol"]):
    #         current_tag = tag.text.strip()
    #         if re.match(pattern, tag.text.strip()):
    #             tag.name = "li"
    #
    #         # (1)
    #         if re.match(Num_bracket_pattern, current_tag):
    #             # pattern1 = re.findall(r'^\(\d+\)', tag.text.strip())
    #             ol_num = tag
    #             if re.search(r'^(\(1\))', current_tag):
    #                 ol_tag = self.soup.new_tag("ol")
    #                 tag.wrap(ol_tag)
    #             else:
    #                 ol_tag.append(tag)
    #
    #             tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
    #             prev_header_id = tag.find_previous("h3").get("id")
    #             tag["id"] = f"{prev_header_id}ol1{tag_id}"
    #
    #         # (a)
    #         if re.match(alpha_pattern, current_tag):
    #             ol_alpha = tag
    #             if re.match(r'^\(a\)', tag.text.strip()):
    #                 ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #                 tag.wrap(ol_tag2)
    #                 ol_num.append(ol_tag2)
    #             else:
    #                 ol_tag2.append(tag)
    #
    #             tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
    #             prev_header_id = ol_num.get("id")
    #             tag["id"] = f"{prev_header_id}{tag_id}"
    #
    #
    #
    #
    #         # # (4)(a)
    #         if re.match(numAlpha_pattern, current_tag):
    #             ol_inr_apha = tag
    #             prev_header = tag.find_previous("h3")
    #             prev_header_id = prev_header.get("id")
    #
    #             tag_id1 = re.search(r'^\((?P<id1>\d+)\)\s*\((\D+)\)', current_tag).group("id1")
    #             tag_id2 = re.search(r'^\((\d+)\)\s*\((?P<id2>\D+)\)', current_tag).group("id2")
    #
    #             ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #             li_tag = self.soup.new_tag("li")
    #
    #             # li_tag.append(current_tag)
    #
    #             tag_text = re.sub(numAlpha_pattern, '', tag.text.strip())
    #             li_tag.append(tag_text)
    #
    #             li_tag["id"] = f"{prev_header_id}ol1{tag_id1}{tag_id2}"
    #
    #             ol_tag2.append(li_tag)
    #             tag.contents = []
    #             tag.append(ol_tag2)
    #
    #             # (4)(a)1.
    #             if re.match(r'\(\d+\)\s*\(\D\)\s*\d\.', current_tag):
    #                 ol_tag4 = self.soup.new_tag("ol")
    #                 inner_li_tag = self.soup.new_tag("li")
    #
    #                 tag_text = re.sub(r'\(\d+\)\s*\(\D\)\s*\d\.', '', current_tag)
    #                 inner_li_tag.append(tag_text)
    #
    #                 # print(tag)
    #
    #                 # inner_li_tag.append(tag.text.strip())
    #
    #                 tag_id1 = re.search(r'^(\(\d+\)\s*\((?P<id1>\D)\)\s*\d\.)', current_tag).group("id1")
    #                 tag_id2 = re.search(r'\(\d+\)\s*\(\D\)\s*(?P<id2>\d)\.', current_tag).group("id2")
    #
    #                 prev_id = ol_inr_apha.get("id")
    #                 inner_li_tag["id"] = f"{prev_id}{tag_id1}{tag_id2}"
    #                 prev_header_id = f"{prev_id}{tag_id1}"
    #                 main_olcount = 2
    #
    #                 ol_tag4.append(inner_li_tag)
    #                 tag.insert(1, ol_tag4)
    #                 ol_tag4.find_previous().string.replace_with(ol_tag4)
    #
    #         # a
    #         if re.match(r'[a-z]\.', current_tag):
    #             if re.match(r'a\.', current_tag):
    #                 ol_tag3 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #                 tag.wrap(ol_tag3)
    #                 ol_tag.append(ol_tag3)
    #                 tag.find_previous("li").append(ol_tag3)
    #
    #                 inr_olcount = 97
    #                 prev_header_id = tag.find_previous("li").get("id")
    #             else:
    #                 tag.find_previous("li").append(tag)
    #
    #             tag_id = re.search(r'^(?P<id>[a-z])\.', current_tag).group('id')
    #             tag["id"] = f"{prev_header_id}{tag_id}"
    #
    #             if tag.span:
    #                 tag.span.string = ""
    #
    #         # (a) 1.
    #         if re.match(alphanum_pattern, current_tag):
    #             ol_tag5 = self.soup.new_tag("ol")
    #             li_tag = self.soup.new_tag("li")
    #
    #             tag_id1 = re.search(r'^\((?P<id1>\D+)\)\s(\d)+', current_tag).group("id1")
    #             tag_id2 = re.search(r'^\(\D+\)\s(?P<id2>\d)+', current_tag).group("id2")
    #
    #             tag_text = re.sub(r'^\(\D+\)\s(\d)\.', '', current_tag)
    #             li_tag.append(tag_text)
    #
    #             # li_tag.append(current_tag.strip())
    #
    #             ol_tag5.append(li_tag)
    #
    #             prev_id = ol_inr_apha.get("id")
    #             li_tag["id"] = f"{prev_id}{tag_id1}{tag_id2}"
    #             prev_header_id = f"{prev_id}{tag_id1}"
    #             main_olcount = 2
    #
    #             tag.contents = []
    #             tag.append(ol_tag5)
    #
    #             # print(tag)
    #             # tag.span.string = ""
    #
    #         # elif re.match(num_pattern, tag.text.strip()):
    #         #     tag.find_previous("li").append(tag)
    #
    #         # 1. and previous (1)(a)
    #         if re.match(num_pattern, current_tag):
    #             if re.match(r'^1\.', current_tag):
    #                 ol_tag6 = self.soup.new_tag("ol")
    #                 tag.wrap(ol_tag6)
    #                 tag.find_previous("li").append(ol_tag6)
    #
    #                 main_olcount = 1
    #                 if tag.find_previous("li"):
    #                     prev_header_id = tag.find_previous("li").get("id")
    #
    #             elif tag.find_previous("li"):
    #                 tag.find_previous("li").append(tag)
    #
    #             # prev_header_id = tag.find_previous("h3").get("id")
    #             tag["id"] = f"{prev_header_id}{main_olcount}"
    #             main_olcount += 1
    #
    #         # 1. previous
    #     print("ol tag is created")

    # create div tags
    def create_and_wrap_with_div_tag(self):
        self.soup = BeautifulSoup(self.soup.prettify(formatter=None), features='lxml')
        for header in self.soup.findAll('h2'):
            new_chap_div = self.soup.new_tag('div')
            sec_header = header.find_next_sibling()
            header.wrap(new_chap_div)
            while True:
                next_sec_tag = sec_header.find_next_sibling()
                if sec_header.name == 'h3':
                    new_sec_div = self.soup.new_tag('div')
                    tag_to_wrap = sec_header.find_next_sibling()
                    sec_header.wrap(new_sec_div)
                    while True:
                        next_tag = tag_to_wrap.find_next_sibling()
                        if tag_to_wrap.name == 'h4':
                            new_sub_sec_div = self.soup.new_tag('div')
                            inner_tag = tag_to_wrap.find_next_sibling()
                            tag_to_wrap.wrap(new_sub_sec_div)

                            while True:
                                inner_next_tag = inner_tag.find_next_sibling()
                                if inner_tag.name == 'h5':
                                    new_h5_div = self.soup.new_tag('div')
                                    inner_h5_tag = inner_tag.find_next_sibling()
                                    inner_tag.wrap(new_h5_div)
                                    while True:
                                        next_h5_child_tag = inner_h5_tag.find_next_sibling()
                                        new_h5_div.append(inner_h5_tag)
                                        inner_next_tag = next_h5_child_tag
                                        if not next_h5_child_tag or next_h5_child_tag.name in ['h3', 'h2', 'h4', 'h5']:
                                            break
                                        inner_h5_tag = next_h5_child_tag
                                    inner_tag = new_h5_div
                                new_sub_sec_div.append(inner_tag)
                                next_tag = inner_next_tag
                                if not inner_next_tag or inner_next_tag.name in ['h3',
                                                                                 'h2'] or inner_next_tag.name == 'h4' \
                                        and inner_next_tag.get('class'):
                                    break
                                inner_tag = inner_next_tag
                            tag_to_wrap = new_sub_sec_div
                        elif tag_to_wrap.name == 'h5':
                            new_sub_sec_div = self.soup.new_tag('div')
                            inner_tag = tag_to_wrap.find_next_sibling()
                            tag_to_wrap.wrap(new_sub_sec_div)
                            while True:
                                inner_next_tag = inner_tag.find_next_sibling()
                                new_sub_sec_div.append(inner_tag)
                                next_tag = inner_next_tag
                                if not inner_next_tag or inner_next_tag.name in ['h3', 'h2', 'h4', 'h5']:
                                    break
                                inner_tag = inner_next_tag
                            tag_to_wrap = new_sub_sec_div
                        if not re.search(r'h\d', tag_to_wrap.name):
                            new_sec_div.append(tag_to_wrap)
                        next_sec_tag = next_tag
                        if not next_tag or next_tag.name in ['h3', 'h2']:
                            break
                        tag_to_wrap = next_tag
                    sec_header = new_sec_div
                new_chap_div.append(sec_header)
                if not next_sec_tag or next_sec_tag.name == 'h2':
                    break
                sec_header = next_sec_tag

        print('wrapped div tags')

    def convert_roman_to_digit(self, roman):
        value = {'M': 1000, 'D': 500, 'C': 100, 'L': 50, 'X': 10, 'V': 5, 'I': 1}
        prev = 0
        ans = 0
        length = len(roman)
        for num in range(length - 1, -1, -1):
            if value[roman[num]] >= prev:
                ans += value[roman[num]]
            else:
                ans -= value[roman[num]]
            prev = value[roman[num]]

        return ans

    # creating numberical ol
    def create_numberical_ol(self):
        pattern = re.compile(r'^(\d+)|^(\(\d+\)|^\(\s*[a-z][a-z]?\s*\))|^([a-z]\.)|^([A-Z]{0,3}\.)|^([a-z]{0,3}\.)')
        Num_bracket_pattern = re.compile(r'^\(\d+\)')
        alpha_pattern = re.compile(r'^\(\s*[a-z][a-z]?\s*\)')
        num_pattern = re.compile(r'^\d+\.')
        rom_pattern = re.compile(r'^([A-Z]{0,3}\.)')
        # numAlpha_pattern = re.compile(r'^\(\d+\)\s\(\D\)')

        for tag in self.soup.findAll("li", class_=self.class_regex["ol"]):
            if re.match(pattern, tag.text.strip()):
                if re.match(Num_bracket_pattern, tag.text.strip()) or re.match(alpha_pattern, tag.text.strip()) or \
                        re.match(num_pattern, tag.text.strip()) or re.match(rom_pattern, tag.text.strip()):
                    if tag.span:
                        tag.span.string = ""
                    else:
                        tag_text = re.sub(r'^\d+\.','',tag.text.strip())
                        tag.string = tag_text







    # add watermark and remove default class names
    def add_watermark_and_remove_class_name(self):

        for tag in self.soup.find_all():
            if tag.name in ['li', 'h4', 'h3', 'p']:
                del tag["class"]

        watermark_tag = self.soup.new_tag('p', Class='transformation')
        watermark_tag.string = self.watermark_text.format(self.release_number, self.release_date,
                                                          datetime.now().date())

        title_tag = self.soup.find("nav")
        if title_tag:
            title_tag.insert(0, watermark_tag)

        for meta in self.soup.findAll('meta'):
            if meta.get('http-equiv') == "Content-Style-Type":
                meta.decompose()

        for all_tag in self.soup.findAll():

            if all_tag.get("class"):
                all_tag_class = str(all_tag.get("class"))
                # print(all_tag_class)
                if re.match(r'^\[\'p\d\'\]',all_tag_class.strip()):
                    del all_tag["class"]




    # citation
    def add_citation1(self):
        title_dict = {"I": ['1', '2', '3'], "II": ['5', '6', '6A', '7', '7A', '7B', '8'],
                      "III": ['11', '11A', '12', '13', '13A', '13B', '14', '14A', '15', '15A', '16', '17', '18', '18A',
                              '19'], "IV": ['21', '21A', '22', '22A', '23', '23A', '24', '24A',
                                            '25', '26', '26A', '27', '27A', '28', '29', '29A', '30', '30A', '31', '31A',
                                            '32', '34'],
                      'V': ['35', '36', '37', '38', '39', '39A', '39B', '39C', '39D', '39E', '39F', '39G', '40'],
                      'VI': ['41', '42', '43', '44', '45', '45A', '46', '47', '48', '49'],
                      'VII': ['56', '57', '58'], 'VIII': ['61', '62', '63', '64', '64'],
                      'IX': ['65', '65A', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77', '78',
                             '79', '80', '81', '81A', '82', '83', '83A', '84', '85', '86', '87', '88', '89', '90', '91',
                             '91A', '92', '93', '93A', '94', '95', '95A', '96', '96A', '97', '98', '99', '99A', '100',
                             '101', '102', '103', '104', '105', '106', '107', '108', '108A', '109'],
                      'X': ['116', '117', '117A', '118', '118A', '118B', '119', '120', '121', '121A', '122', '123',
                            '124',
                            '125', '126', '127', '128'],
                      'XI': ['131', '132', '133', '134', '135', '136', '137', '138', '139', '140', '141', '142', '143',
                             '143A', '144'],
                      'XII': ['146', '147', '147A', '147B', '148', '149', '150', '151', '151B', '152', '152A', '153',
                              '154', '154A', '154B', '155'],
                      'XIII': ['156', '157', '157A', '158', '159', '160', '161', '162', '163', '164A', '165', '165A',
                               '166', '167', '168'], 'XIV': ['171', '172', '173'],
                      'XV': ['174', '175', '175A', '175B', '176', '177', '178', '179', '180', '181', '182', '183',
                             '184'],
                      'XVI': ['186', '186A', '187', '188', '189', '189A', '190', '190A'],
                      'XVII': ['194', '194A', '194B', '195', '196', '197', '198', '198A', '198B', '199', '200', '201',
                               '202', '202A', '202B', '203', '204', '205', '206', '207', '208', '208A', '208B', '208C',
                               '208D', '208E', '208F', '208G', '209', '209A'],
                      'XVIII': ['210', '211', '212', '213', '214', '215', '216', '216A', '216B', '216C', '217', '217A',
                                '217B', '217C', '218', '218A', '219', '220', '221', '222', '223', '224', '224A'],
                      'XIX': ['226', '227', '227A', '228', '229', '230', '231', '232', '233', '234', '235', '236',
                              '237', '238'], 'XX': ['241', '242', '243', '244'],
                      'XXI': ['246', '247', '248', '249', '248', '249', '250', '251', '252', '253', '254', '255', '256',
                              '257', '258', '259', '260', '261', '262', '263'], 'XXII': ['266', '267', '268', '269'],
                      'XXIII': ['271', '271A', '271B', '272', '272A', '273', '274', '274', '275'],
                      'XXIV': ['276', '277', '278', '279', '280', '281', '281A'],
                      'XXV': ['286', '287', '288', '289', '290', '291', '292', '293', '294', '295', '296', '297', '298',
                              '299', '300', '301', '302', '303', '304', '305', '306', '307'],
                      'XXVI': ['309', '310', '311', '311A', '311B', '312', '313', '314', '314A', '315', '316', '317',
                               '317A', '317B', '318', '319', '319A', '319B', '319C', '320', '321', '322', '322A', '323',
                               '323A', '324', '324A', '324B', '325', '326', '327', '328', '329', '329A', '330', '331',
                               '332', '333', '334', '334A', '335', '335B'],
                      'XXVII': ['336', '337', '338', '339', '340', '341', '342', '343', '344', '345', '346', '347'],
                      'XXVIII': ['349', '350', '351', '352', '353', '354'],
                      'XXIX': ['355', '356', '357', '358', '359', '360', '361', '362', '363', '364', '365', '366',
                               '367', '368', '369'],
                      'XXX': ['371', '372'], 'XXXI': ['376', '377', '378', '379', '380'],
                      'XXXII': ['381', '382', '383', '384', '385'],
                      'XXXIII': ['386', '386A', '386B', '387', '388', '389', '389A', '390'],
                      'XXXIV': ['391', '392', '393', '393A', '394', '395', '395A', '396', '397', '397A'],
                      'XXXV': ['401', '402', '403', '404', '405', '406', '407'],
                      'XXXVI': ['411', '412', '413', '414', '415', '416', '417', '418', '419', '420', '421', '422',
                                '423', '424', '425', '426', '427', '428', '429', '430', '431', '432', '433', '434',
                                '435', '436', '437', '438', '439', '440', '441', '442', '443', '444', '445'],
                      'XXXVII': ['416', '417', '418', '419'], 'XXXVIII': ['421', '422', '423', '424'],
                      'XXXIX': ['425', '426', '427'],
                      'XXXX': ['431', '432', '434', '435', '436', '437', '438', '439', '440', '441'],
                      'XXXXI': ['446', '447'], 'XXXXII': ['451', '452', '453', '454', '455', '456', '457'],
                      'XXXXX': ['500', '501', '502', '503', '504', '505', '506', '507', '507A', '508', '509', '510',
                                '511', '512', '513', '514', '515',
                                '516', '517', '518', '519', '520', '521', '522', '523', '524', '525', '526', '527',
                                '528', '529', '530', '531', '532', '533', '534'],
                      'XXXXXI': ['600', '605', '610', '615', '620', '625', '630', '635', '640', '645']

                      }

        tag_id = None
        target = "_blank"

        chapter_list = []
        for chap_tag in self.soup.find_all(class_=self.class_regex["ul"]):
            if re.search('constitution', self.html_file_name):
                if re.match(r'^(§(§)*\s*(?P<chap>\d+[a-zA-Z]*).)', chap_tag.text.strip()):
                    chap_list = re.search(r'^(§(§)*\s*(?P<chap>\d+[a-zA-Z]*).)', chap_tag.text.strip()).group("chap")
                    chapter_list = chapter_list + [chap_list]

            else:
                if re.match(r'^(CHAPTER)', chap_tag.a.text.strip()):
                    # print(chap_tag)
                    chap_list = re.search(r'^(CHAPTER\s*(?P<chap_num>\d+))', chap_tag.a.text.strip()).group("chap_num")
                    chapter_list = chapter_list + [chap_list]

        cite_p_tags = []
        cite_li_tags = []
        titleid = ""

        for tag in self.soup.find_all(["p", "li"]):
            if re.search(r"KRS\s?\d+[a-zA-Z]*\.\d+(\(\d+\))*(-\d+)*|"
                         r"(KRS Chapter \d+[a-zA-Z]*)|"
                         r"(KRS Title \D+, Chapter \D+?,)|"
                         r"KRS\s*\d+[a-zA-Z]*\.\d+\(\d+\)|"
                         r"(KRS\s*\d+[a-zA-Z]*\.\d+\(\d+\)|"
                         r"(U.S.C.\s*secs*\.\s*\d+)|"
                         r"(Ky.\s?(App\.)?\s?LEXIS\s?\d+)|"
                         r"(Ky.\s*(L. Rptr.\s*)*\d+)|"
                         r"(OAG \d+-\d+))", tag.text.strip()):
                # cite_li_tags.append(tag)
                text = str(tag)
                # print(tag)

                for match in [x[0] for x in re.findall(r'((Ky.\s*(L. Rptr.\s*)*\d+)|'
                                                       r'(Ky.\s?(App\.)?\s?LEXIS\s?\d+)|'
                                                       r'(U.S.C.\s*secs*\.\s*\d+(\([a-zA-Z]\))*(\(\d+\))*)|'
                                                       r'(KRS\s?\d+[a-zA-Z]*\.\d+(\(\d+\))*(\(\D\))*)(-\d+)*|'
                                                       r'(Chapter \d+[a-zA-Z]*)|'
                                                       r'(Title\s+?\D+,\s+?Chapter\s+?\D+?,)|'
                                                       r'(\d+?\w?\.\d+\s+?\(\d\)+?)|'
                                                       r'(\d+\.\d{3}[^\d])|'
                                                       r'(\d+\.\d{3}\(\d+\))|'
                                                       r'(KRS\s*\d+[a-zA-Z]*\.\d+\(\d+\))|'
                                                       r'(OAG \d+-\d+))'
                        , tag.get_text())]:

                    if tag.parent.name == "ul":
                        continue

                    else:

                        match = re.sub(r'KRS\s', '', match.strip())
                        tag.clear()

                        inside_text = re.sub(
                            r'<p\sclass="\w\d+">|</p>|<b>|</b>|^<li\sclass="\w\d+"\sid="\w+\.\d+(\.\d+)?ol\d\d+">|'
                            r'<li\sclass="\w\d+"\sid="t[a-zA-Z]+\d+[a-zA-Z]+\d+s\d+[a-zA-Z]+\d+-\d+\w+\W+(\d+)*ol\d+">|'
                            r'<li\sclass="\w\d+"\sid="t[a-zA-Z]+\d+[a-zA-Z]+\d+s\d+[a-zA-Z]+\d+-\d+[a-zA-Z]+ol\d+">|'
                            r'<li\sclass="\w\d+"\sid="t[a-zA-Z]+\d+[a-zA-Z]+\d+s\d+[a-zA-Z]+\d+-\d+[a-zA-Z]+—[a-zA-Z]+ol\d+">|'
                            r'<li\sclass="\w\d+"\sid="t[a-zA-Z]+\d+[a-zA-Z]+\d+s\d+[a-zA-Z]+\d+-\d+[a-zA-Z]+-[a-zA-Z]+(—)*\w+\W+\d+ol\d+">|'
                            r'<li\sclass="\w\d+"\sid="t[a-zA-Z]+\d+[a-zA-Z]+\d+s\d+[a-zA-Z]+\d+-\d+[a-zA-Z]+[—a-zA-Z]+ol\d+">|'
                            r'<li\sclass="\w\d+"\sid="t[a-zA-Z]+\d+[a-zA-Z]+\d+s\d+[a-zA-Z]+\d+-\d+\w+\W+[a-zA-Z]+(\d+)*ol\d+">|'
                            r'<li\sclass="\w\d+"\sid="t[a-zA-Z]+\d+[a-zA-Z]+\d+s\d+[a-zA-Z]+\d+-\d+\w+\W+\w+(-)*(\W+)*\w+(—\w+)*ol\d+">|'
                            r'<li\sclass="\w\d+"\sid="t[a-zA-Z]+\d+[a-zA-Z]+\d+s\d+[a-zA-Z]+\d+-\d+\w+[,\d]+\w+ol\d+">|'
                            r'<li\sclass="\w\d+"\sid="t[a-zA-Z]+\d+[a-zA-Z]*\d+[a-zA-Z]*\.\d+-\d+[a-zA-Z]*\W*ol\d+">|'
                            # r'<li\sclass="\w\d+"\sid="t[a-zA-Z]+\d+s\d+.\d+[\w\W]+ol\d\d\D">|'                               
                            r'</li>$',
                            '', text, re.DOTALL)


                        # 1.2025/1A.2025
                        if re.search(r'(\d+[a-zA-Z]*\.\d+)(-\d+)*', match.strip()):

                            chap_num = re.search(r'(?P<chap>\d+[a-zA-Z]*)\.\d+(-\d+)*', match.strip()).group("chap")

                            sec_num = re.search(r'(\d+[a-zA-Z]*\.\d+)(-\d+)*', match.strip()).group().zfill(2)
                            if chap_num in chapter_list:
                                tag_id = f'#t{self.title_id}c{chap_num.zfill(2)}s{sec_num}'
                                target = "_self"

                            else:

                                for key, value in title_dict.items():

                                    if chap_num in value:
                                        titleid = key
                                        titleid1 = self.convert_roman_to_digit(key)

                                        tag_id = f'gov.ky.krs.title.{titleid1:02}.html#t{titleid}c{chap_num.zfill(2)}s{sec_num}'
                                        target = "_blank"

                        # 1.2025(a)/#1A.2025(a)
                        if re.search(r'\d+[a-zA-Z]*\.\d+(\(\d+\))', match.strip()):
                            # print(match)
                            chap_num = re.search(r'(?P<chap>\d+[a-zA-Z]*)\.\d+(\(\d+\))', match.strip()).group("chap")
                            # print(chap_num)
                            sec_num = re.search(r'\d+[a-zA-Z]*\.\d+', match.strip()).group().zfill(2)
                            ol_num = re.search(r'\d+[a-zA-Z]*\.\d+\((?P<ol>\d+)\)', match.strip()).group("ol")
                            # print(ol_num)

                            if chap_num in chapter_list:
                                tag_id = f'#t{self.title_id}c{chap_num.zfill(2)}s{sec_num}ol1{ol_num}'
                                target = "_self"

                            else:
                                for key, value in title_dict.items():
                                    if chap_num in value:
                                        titleid = key
                                        titleid1 = self.convert_roman_to_digit(key)

                                        tag_id = f'gov.ky.krs.title.{titleid1:02}.html#t{titleid}c{chap_num.zfill(2)}s{sec_num}ol1{ol_num}'
                                        target = "_blank"

                        # 1.2025(a)(1)/1A.2025(a)(1)
                        if re.search(r'(\d+[a-zA-Z]*\.\d+(\(\d+\))(\(\D\)))', match.strip()):
                            # print(match)
                            chap_num = re.search(r'(?P<chap>\d+[a-zA-Z]*)\.\d+(\(\d+\))(\(\D\))', match.strip()).group(
                                "chap")
                            # print(chap_num)
                            sec_num = re.search(r'\d+[a-zA-Z]*\.\d+', match.strip()).group().zfill(2)
                            ol_num = re.search(r'\d+[a-zA-Z]*\.\d+\((?P<ol>\d+)\)', match.strip()).group("ol")
                            inr_ol_num = re.search(r'\d+[a-zA-Z]*\.\d+\(\d+\)\((?P<innr_ol>\D)\)', match.strip()).group(
                                "innr_ol")
                            # print(inr_ol_num)

                            if chap_num in chapter_list:
                                tag_id = f'#t{self.title_id}c{chap_num.zfill(2)}s{sec_num}ol1{ol_num}{inr_ol_num}'
                                target = "_self"

                            else:
                                for key, value in title_dict.items():
                                    if chap_num in value:
                                        titleid = key
                                        titleid1 = self.convert_roman_to_digit(key)

                                    tag_id = f'gov.ky.krs.title.{titleid1:02}.html#t{titleid}c{chap_num.zfill(2)}s{sec_num}ol1{ol_num}{inr_ol_num}'
                                    target = "_blank"

                        # Chapter I
                        if re.search(r'(Chapter \d+[a-zA-Z]*)', match.strip()):
                            chap_num = re.search(r'Chapter (?P<chap>\d+[a-zA-Z]*)', match.strip()).group("chap")
                            if chap_num in chapter_list:
                                tag_id = f'#t{self.title_id}c{chap_num.zfill(2)}'
                                target = "_self"
                            else:
                                for key, value in title_dict.items():
                                    if chap_num in value:
                                        titleid = key
                                        titleid1 = self.convert_roman_to_digit(key)
                                        tag_id = f'gov.ky.krs.title.{titleid1:02}.html#t{titleid}c{chap_num.zfill(2)}'
                                        # print(tag_id)
                                        target = "_blank"

                        # Title I Chapter I
                        if re.search(r'(Title\s+?(\D+|\d+),\s+?Chapter\s+?(\D+|\d+)?,)', match.strip()):
                            tag_id = re.search(r'(Title\s+?(?P<tid>\D+|\d+),\s+?Chapter\s+?(?P<cid>\D+|\d+)?,)',
                                               match.strip())

                            title_id = tag_id.group("tid")
                            chapter = tag_id.group("cid")

                            if chapter.isalpha():
                                chap_num = self.convert_roman_to_digit(chapter)
                            else:
                                chap_num = chapter

                            title = self.convert_roman_to_digit(title_id)

                            if str(chap_num) in chapter_list:
                                tag_id = f'#t{self.title_id}c{chap_num:02}'
                                target = "_self"
                            else:
                                tag_id = f'gov.ky.krs.title.{title}.html#t{titleid}c{chap_num:02}'
                                target = "_blank"

                        class_name = "ocky"
                        format_text = f'<cite class="{class_name}"><a href="{tag_id}" target="{target}">{match}</a></cite>'

                        if re.search(r'(U.S.C.\s*secs*\.\s*\d+(\([a-zA-Z]\))*(\(\d+\))*)', match.strip()):
                            class_name = "US_code"
                            format_text = f'<cite class="{class_name}">{match}</cite>'

                        if re.search(r'(Ky.\s?(App\.)?\s?LEXIS\s?\d+)', match.strip()):
                            class_name = "ky_app_code"
                            format_text = f'<cite class="{class_name}">{match}</cite>'

                        if re.search(r'(Ky.\s*(L. Rptr.\s*)*\d+)|(OAG \d+-\d+)', match.strip()):
                            if re.search(r'(?P<APP>(Ky.\s*(L. Rptr.\s*)*\d+))', match.strip()):
                                if re.match(r'(?P<APP>(Ky.\s*(L. Rptr.\s*)\d+))', match.strip()):
                                    class_name = "ky_rptr_code"
                                    format_text = f'<cite class="{class_name}">{match}</cite>'
                                else:
                                    chap_num = re.search(r'Ky.\s*(?P<chap>\d+)', match.strip()).group("chap")

                                    if chap_num in chapter_list:

                                        tag_id = f'#t{self.title_id}c{chap_num.zfill(2)}'
                                        target = "_self"

                                        class_name = "ocky"
                                        format_text = f'<cite class="{class_name}"><a href="{tag_id}" target="{target}">{match}</a></cite>'

                                    else:

                                        for key, value in title_dict.items():

                                            if chap_num in value:

                                                titleid = key
                                                titleid1 = self.convert_roman_to_digit(key)

                                                tag_id = f'gov.ky.krs.title.{titleid1:02}.html#t{titleid}c{chap_num.zfill(2)}'
                                                target = "_blank"

                                                class_name = "ocky"
                                                format_text = f'<cite class="{class_name}"><a href="{tag_id}" target="{target}">{match}</a></cite>'
                                                break

                                            else:

                                                class_name = "ky_code"
                                                format_text = f'<cite class="{class_name}">{match}</cite>'


                            else:

                                class_name = "OAG"
                                format_text = f'<cite class="{class_name}">{match}</cite>'

                        # print(format_text)

                        text = re.sub(fr'\s{re.escape(match)}', format_text, inside_text, re.I)
                        tag.append(text)

    # replace title tag to "h1" and wrap it with "nav" tag
    def set_appropriate_tag_name_and_id1(self):
        snav = 0
        cnav = 0
        anav = 0
        pnav = 0
        chapter_id_list = []
        header_list = []
        note_list = []
        cur_id_list = []
        repeated_header_list = []
        for header_tag in self.soup.body.find_all():
            if re.search('constitution', self.html_file_name):
                if header_tag.get("class") == [self.class_regex["title"]]:
                    if re.search(r'^(THE CONSTITUTION OF THE UNITED STATES OF AMERICA)', header_tag.text.strip()):
                        self.title_id = "constitution-us"
                    else:
                        self.title_id = "constitution-ky"
                    header_tag.name = "h1"
                    header_tag.attrs = {}
                    header_tag.wrap(self.soup.new_tag("nav"))

                elif header_tag.get("class") == [self.class_regex["head2"]]:
                    # print(header_tag)
                    if re.search(r'^§(§)*|^(ARTICLE)|^(AMENDMENTS)', header_tag.text.strip()):
                        header_tag.name = "h2"

                        if re.search(r'^§(§)*', header_tag.text.strip()):
                            chap_num = re.search(r'^(§(§)*\s*(?P<chap>\d+[a-zA-Z]*).?) ',
                                                 header_tag.text.strip()).group(
                                "chap").zfill(2)
                            header_tag["id"] = f"{self.title_id}p{chap_num}"
                        elif re.search(r'^(ARTICLE)', header_tag.text.strip()):
                            chap_num = re.search(r'^(ARTICLE\s*(?P<ar>[A-Z]+))', header_tag.text.strip()).group(
                                "ar").zfill(2)
                            header_tag["id"] = f"{self.title_id}ar{chap_num}"
                        elif re.search(r'^AMENDMENTS', header_tag.text.strip()):
                            chap_num = re.sub(r'\s', '', header_tag.text.strip())
                            header_tag["id"] = f"{self.title_id}am{chap_num}"
                    elif re.search(r'^(AMENDMENT)', header_tag.text.strip()):
                        header_tag.name = "h3"
                        chap_num = re.sub(r'[\W]', '', header_tag.text.strip())
                        header_tag["id"] = f"{self.title_id}am{chap_num}"

                elif header_tag.get("class") == [self.class_regex["sec_head"]]:
                    if re.search(r'^Section', header_tag.text.strip()):
                        header_tag.name = "h3"

                        if header_tag.find_previous("h3") and re.match(r'AMENDMENT',
                                                                       header_tag.find_previous("h2").text.strip()):
                            prev_id = header_tag.find_previous("h3").get("id")
                            header_tag.name = "h4"
                        else:
                            prev_id = header_tag.find_previous("h2").get("id")
                        cur_id = re.search(r'^^(Section\s?(?P<sec>\d+).)', header_tag.text.strip()).group("sec").zfill(
                            2)
                        header_tag["id"] = f'{prev_id}s{cur_id}'


                elif header_tag.get("class") == [self.class_regex["ul"]]:
                    if re.search(r'^§(§)*|^(ARTICLE)|^(Section)|^(AMENDMENT)', header_tag.text.strip()):
                        header_tag.name = "li"

                elif header_tag.get("class") == [self.class_regex["head4"]]:
                    if re.match(r'^(\d+\.)', header_tag.text.strip()):
                        header_tag.name = "h5"

                        if re.match(r'^(\d+\.\s*“?[a-zA-Z]+)', header_tag.text.strip()):
                            prev_note_id = header_tag.find_previous("h4").get("id")
                            current_id = re.sub(r'[\s.]', '', header_tag.get_text()).lower()
                            header_tag["id"] = f'{prev_note_id}-{current_id}'
                            sub_sec_id = header_tag.get("id")

                            if re.match(r'^1.', header_tag.text.strip()):
                                nav_link_list = []
                                count = 1

                        elif re.match(r'^(\d+\.(\d+\.)?\s*—\s*[a-zA-Z]+)', header_tag.text.strip()):

                            head_tag_text = re.sub(r'[\s.—]', '', header_tag.text.strip()).lower()

                            prev_sub_tag = sub_sec_id
                            innr_sec_text = re.sub(r'[\s.—]', '', header_tag.get_text()).lower()

                            if head_tag_text in header_list:
                                innr_sec_id1 = f"{prev_sub_tag}-{innr_sec_text}.{count}"
                                count += 1
                            else:
                                innr_sec_id1 = f"{prev_sub_tag}-{innr_sec_text}"

                            header_tag["id"] = innr_sec_id1
                            header_text = re.sub(r'[\s.—]', '', header_tag.text.strip()).lower()
                            header_list.append(header_text)



                        elif re.match(r'^(\d+\.\s*—\s*—\s*[a-zA-Z]+)', header_tag.text.strip()):
                            prev_child_tag = innr_sec_id1
                            innr_sec_text2 = re.sub(r'[\s.—]', '', header_tag.get_text()).lower()

                            if innr_sec_text2 in header_list:
                                innr_sec_id2 = f"{prev_child_tag}-{innr_sec_text2}.{count}"
                                count += 1
                            else:
                                innr_sec_id2 = f"{prev_child_tag}-{innr_sec_text2}"

                            # innr_sec_id2 = f"{prev_child_tag}-{innr_sec_text2}"
                            header_tag["id"] = innr_sec_id2

                            header_text = re.sub(r'[\s.—]', '', header_tag.text.strip()).lower()
                            header_list.append(header_text)


                        elif re.match(r'^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)', header_tag.text.strip()):
                            prev_child_id1 = innr_sec_id2
                            innr_subsec_header_id = re.sub(r'[\s.—]', '', header_tag.get_text()).lower()
                            innr_subsec_header_tag_id = f"{prev_child_id1}-{innr_subsec_header_id}"
                            header_tag["id"] = innr_subsec_header_tag_id

                    else:

                        header_tag.name = "h4"

                        if header_tag.find_previous("h2"):

                            prev_head_id = header_tag.find_previous("h2").get("id")
                            current_id = re.sub(r'\s.', '', header_tag.text.strip())
                            curr_tag_id = f'{prev_head_id}-{current_id}'

                            if header_tag.find_previous("h4"):

                                if curr_tag_id in cur_id_list:
                                    # if curr_tag_id == header_tag.find_previous("h4").get("id"):
                                    header_tag["id"] = f'{prev_head_id}-{current_id}-1'

                                else:
                                    header_tag["id"] = f'{prev_head_id}-{current_id}'

                                cur_id_list.append(header_tag["id"])

                        else:

                            current_id = re.sub(r'\s', '', header_tag.text.strip())
                            header_tag["id"] = f'{self.title_id}-{current_id}'

            else:

                if header_tag.get("class") == [self.class_regex["title"]]:
                    header_tag.name = "h1"
                    header_tag.attrs = {}
                    header_tag.wrap(self.soup.new_tag("nav"))

                    self.title_id = re.search(r'^(TITLE)\s(?P<title_id>\w+)', header_tag.text.strip()).group('title_id')

                elif header_tag.get("class") == [self.class_regex["head2"]]:

                    if re.search("^(CHAPTER)|^(Chapter)", header_tag.text):

                        chap_nums = re.search(r'^(CHAPTER|Chapter)\s(?P<chapter_id>\w+)',
                                              header_tag.text.strip()).group(
                            'chapter_id').zfill(2)

                        header_tag.name = "h2"
                        header_tag.attrs = {}
                        header_tag['id'] = f"t{self.title_id}c{chap_nums}"
                        header_tag["class"] = "chapterh2"


                    elif re.search("^(Article|SUBCHAPTER)", header_tag.text):
                        artical_nums = re.search(r'^(Article|SUBCHAPTER(S)*)\s(?P<chapter_id>\w+)',
                                                 header_tag.text.strip()).group(
                            'chapter_id').zfill(2)
                        header_tag.name = "h2"
                        header_tag.attrs = {}
                        prev_id = header_tag.find_previous("h2", class_="chapterh2").get("id")

                        if re.search(r'SUBCHAPTER', header_tag.text.strip()):
                            header_tag['id'] = f"{prev_id}s{artical_nums}"
                            header_tag["class"] = "Subsectionh2"
                        else:
                            header_tag['id'] = f"{prev_id}a{artical_nums}"
                            header_tag["class"] = "Articleh2"

                    elif re.search("^(Part)", header_tag.text):
                        header_tag.name = "h2"
                        part_nums = re.search(r'^(Part)\s(?P<chapter_id>\w+)',
                                              header_tag.text.strip()).group(
                            'chapter_id').zfill(2)
                        prev_id = header_tag.find_previous("h2", class_="Articleh2").get("id")
                        header_tag["id"] = f"{prev_id}p{part_nums.zfill(2)}"
                        header_tag["class"] = "parth2"

                        # print(header_tag)

                    elif re.search("^([A-Z]\.)|^(Subpart)", header_tag.text):
                        header_tag.name = "h3"
                        prev_id = header_tag.find_previous("h2", class_="parth2").get("id")
                        chap_nums = header_tag.find_previous("h2").get("id")
                        if re.match("^([A-Z]\.)", header_tag.text):
                            subpart_nums = re.search(r'^((?P<chapter_id>[A-Z])\.)', header_tag.text.strip()).group(
                                "chapter_id").zfill(2)
                            header_tag["id"] = f"{prev_id}sub{subpart_nums}"

                        if re.match(r'^(Subpart)\s(?P<chapter_id>\w+)', header_tag.text):
                            subpart_nums = re.search(r'^(Subpart)\s(?P<chapter_id>\w+)', header_tag.text.strip()).group(
                                "chapter_id").zfill(2)
                            header_tag["id"] = f"{prev_id}sub{subpart_nums}"

                    else:

                        header_tag.name = "h3"
                        prev_id = header_tag.find_previous("h2", class_="chapterh2").get("id")
                        header_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                        header_tag["id"] = f"{prev_id}{header_id}"

                elif header_tag.get("class") == [self.class_regex["sec_head"]]:
                    header_tag.name = "h3"

                    # print(header_tag)

                    # sec_pattern = re.compile(r'^(\d+\.\d+\.)')
                    if re.match(r'^(\d+\.\d+\.*)', header_tag.text.strip()):
                        chap_num = re.search(r'^(\d+)', header_tag.text.strip()).group().zfill(2)
                        sec_num = re.search(r'^(\d+\.\d+)', header_tag.text.strip()).group().zfill(2)
                        header_pattern = re.search(r'^(\d+\.\d+)', header_tag.text.strip()).group()
                        if header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"]):
                            prev_tag = header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"])
                            if header_pattern not in prev_tag.text.split()[0]:
                                header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"
                            else:
                                count = 0
                                header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}.{count + 1}"

                        else:
                            header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"

                    if re.match(r'^(\d+[a-z]?\.\d+[a-zA-Z]?-\d+\.)', header_tag.text.strip()):
                        chap_num = re.search(r'^([^.]+)', header_tag.text.strip()).group().zfill(2)
                        sec_num = re.search(r'^(\d+[a-z]?\.\d+[a-zA-Z]?-\d+)', header_tag.text.strip()).group().zfill(2)
                        header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"


                    elif re.match(r'^(\d+\D\.\d+)', header_tag.text.strip()):

                        if re.match(r'(\d+[a-zA-Z]*\.\d+-\d+\.)', header_tag.text.strip()):
                            chap_num = re.search(r'^([^.]+)', header_tag.text.strip()).group().zfill(2)
                            sub_num = re.search(r'(\d+[a-zA-Z]*\.(?P<sub>\d+)-\d+\.)', header_tag.text.strip()).group(
                                "sub").zfill(2)
                            # sec_num = re.search(r'(\d+[a-zA-Z]*\.\d+-\d+)', header_tag.text.strip()).group().zfill(2)
                            sec_num = re.sub(r'[\s\.\[\]]', '', header_tag.text.strip())
                            header_tag["id"] = f"t{self.title_id}c{chap_num}sub{sub_num}s{sec_num}"

                        else:

                            chap_num = re.search(r'^([^.]+)', header_tag.text.strip()).group().zfill(2)
                            sec_num = re.search(r'^(\d+\D\.\d+)', header_tag.text.strip()).group().zfill(2)
                            header_pattern = re.search(r'^(\d+\D\.\d+)', header_tag.text.strip()).group()
                            if header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"]):
                                prev_tag = header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"])
                                if header_pattern in prev_tag.text.split()[0]:
                                    count = 0
                                    header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}.{count + 1}"
                                else:
                                    header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"

                            # print(header_tag)

                    elif re.match(r'^(\d+\D\.\d+-\d+)|^(\d+\.\d+-\d+)', header_tag.text):
                        # print(header_tag)
                        chap_num = re.search(r'^([^.]+)', header_tag.text).group().zfill(2)
                        sec_num = re.search(r'^(\d+\D\.\d+-\d+)|^(\d+\.\d+-\d+)', header_tag.text).group().zfill(2)
                        header_pattern = re.search(r'^(\d+\D\.\d+-\d+)|^(\d+\.\d+-\d+)',
                                                   header_tag.text.strip()).group()
                        if header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"]):
                            prev_tag = header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"])
                            if header_pattern in prev_tag.text.split()[0]:
                                count = 0

                                header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}.{count + 1}"
                            else:
                                header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"

                elif header_tag.get("class") == [self.class_regex["ul"]]:
                    header_tag.name = "li"

                    if re.search("^(CHAPTER)|^(Chapter)", header_tag.text):
                        chap_nums = re.search(r'^(CHAPTER|Chapter)\s(?P<chapter_id>\w+)',
                                              header_tag.text.strip()).group(
                            'chapter_id')
                        cnav = cnav + 1
                        header_tag['id'] = f"t{self.title_id}c{chap_nums.zfill(2)}-cnav{cnav:02}"

                    elif re.search("^(Article)|^(SUBCHAPTER)", header_tag.text):
                        # print(header_tag)
                        art_nums = re.search(r'^(Article|SUBCHAPTER(S)*)\s(?P<chapter_id>\w+)',
                                             header_tag.text.strip()).group(
                            'chapter_id')
                        if header_tag.find_previous_sibling().name != "li":
                            anav = 0
                        anav = anav + 1
                        header_tag['id'] = f"t{self.title_id}c{chap_nums.zfill(2)}a{art_nums.zfill(2)}-cnav{anav:02}"

                    elif re.search("^(Part)", header_tag.text):
                        chap_nums = header_tag.find_previous("h2").get("id")
                        part_nums = re.search(r'^(Part)\s(?P<chapter_id>\w+)', header_tag.text.strip()).group(
                            'chapter_id')
                        if header_tag.find_previous_sibling().name != "li":
                            pnav = 0
                        pnav = pnav + 1
                        header_tag['id'] = f"{chap_nums.zfill(2)}p{part_nums.zfill(2)}-cnav{pnav:02}"

                    elif re.search("^([A-Z]\.)|^(Subpart)", header_tag.text):

                        if re.match("^([A-Z]\.)", header_tag.text):
                            subpart_nums = re.search(r'^(?P<chapter_id1>[A-Z])\.', header_tag.text.strip()).group(
                                "chapter_id1")
                        if re.match(r'^(Subpart)', header_tag.text):
                            subpart_nums = re.search(r'^Subpart\s(?P<chapter_id2>\w+)', header_tag.text.strip()).group(
                                "chapter_id2")

                        chap_nums = header_tag.find_previous("h2").get("id")
                        if header_tag.find_previous_sibling().name != "li":
                            spnav = 0
                        spnav = spnav + 1
                        header_tag["id"] = f"{chap_nums}sub{subpart_nums.zfill(2)}-cnav{spnav:02}"


                    else:
                        prev_chapter_id = header_tag.find_previous("h2").get("id")
                        if re.match(r'^(\d+\D*\.\d+(-\d+)*)', header_tag.text.strip()):
                            sec_id = re.search(r'^(?P<id>\d+\D*\.\d+\D?-?\d*)', header_tag.text.strip()).group("id")
                            # chapter_id = re.search(r'^([^.]+)', header_tag.text).group().zfill(2)
                            if header_tag.find_previous_sibling().name != "li":
                                snav = 0
                            snav = snav + 1

                            header_tag["id"] = f"{prev_chapter_id}s{sec_id}-snav{snav:02}"

                        else:
                            previous_tag = header_tag.find_previous().get("id")
                            if re.match(r'^(\d+\D*\.\d+)', header_tag.find_previous().text.strip()):
                                sec_id = re.search("(snav)(?P<id>\d+)", previous_tag.strip()).group("id").zfill(2)
                                sec_id = int(sec_id) + 1

                                section_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                                header_tag["id"] = f"{prev_chapter_id}s{section_id}-snav{sec_id:02}"

                            elif header_tag.find_previous().get("id"):
                                previous_tag_id = header_tag.find_previous().get("id")
                                sec_id = re.search("(snav)(?P<id>\d+)", previous_tag_id.strip()).group("id").zfill(2)
                                sec_id = int(sec_id) + 1

                                section_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                                header_tag["id"] = f"{prev_chapter_id}s{section_id}-snav{sec_id:02}"

                            else:

                                chap_nums = re.search(r'^(CHAPTER|Chapter)\s(?P<chapter_id>\w+)',
                                                      header_tag.find_previous("h2",
                                                                               class_="chapterh2").text.strip()).group(
                                    'chapter_id').zfill(2)
                                section_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                                if re.match(r'^CHAPTER', header_tag.find_previous().text):
                                    snav = 0
                                snav = snav + 1

                                header_tag["id"] = f"t{self.title_id}c{chap_nums}s{section_id}-snav{snav:02}"



                elif header_tag.get('class') == [self.class_regex["head4"]]:
                    if re.match(r'^(\d+\.)', header_tag.text.strip()):
                        header_tag.name = "h5"




                    else:
                        header_tag.name = "h4"

                    if header_tag.name == "h4":
                        if header_tag.find_previous("h3"):
                            prev_tag = header_tag.find_previous("h3").get("id")
                            tag_text = re.sub(r'\s+', '', header_tag.get_text()).lower()
                            header_tag["id"] = f"{prev_tag}{tag_text}"

                            # chapter_id_list.append(header_tag["id"])

                            if header_tag.find_previous("h4"):
                                prev_head_tag_id = header_tag.find_previous("h4").get("id")
                                chapter_id_list.append(prev_head_tag_id)

                                # if header_tag["id"] == prev_head_tag_id:
                                #     header_tag["id"] = f"{prev_tag}{tag_text}-{tag_text}"

                            if header_tag["id"] in chapter_id_list:
                                # print(header_tag)
                                header_tag["id"] = f"{prev_tag}{tag_text}-1"


                    else:
                        if not re.match(r'^(\d+\.\s*—)', header_tag.text.strip()):
                            prev_head_tag = header_tag.find_previous("h4").get("id")
                            sub_sec_text = re.sub(r'[\W]', '', header_tag.get_text()).lower()
                            if header_tag.text.strip() in repeated_header_list:
                                sub_sec_id = f"{prev_head_tag}-{sub_sec_text}.1"
                            else:
                                sub_sec_id = f"{prev_head_tag}-{sub_sec_text}"
                            header_tag["id"] = sub_sec_id
                            repeated_header_list.append(header_tag.text.strip())
                            if re.match(r'^1.\s*[a-zA-Z]+',header_tag.text.strip()):
                                repeated_header_list = []

                        elif re.match(r'^(\d+\.\s*—\s*[a-zA-Z]+)', header_tag.text.strip()):
                            prev_sub_tag = sub_sec_id
                            innr_sec_text = re.sub(r'[\W]', '', header_tag.get_text()).lower()
                            innr_sec_id1 = f"{prev_sub_tag}-{innr_sec_text}"
                            header_tag["id"] = innr_sec_id1

                        elif re.match(r'^(\d+\.\s*—\s*—\s*[a-zA-Z]+)', header_tag.text.strip()):
                            prev_child_tag = innr_sec_id1
                            innr_sec_text1 = re.sub(r'[\W]', '', header_tag.get_text()).lower()
                            innr_sec_id2 = f"{prev_child_tag}-{innr_sec_text1}"
                            header_tag["id"] = innr_sec_id2

                        elif re.match(r'^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)', header_tag.text.strip()):
                            prev_child_id1 = innr_sec_id2
                            innr_subsec_header_id = re.sub(r'[\W]', '', header_tag.get_text()).lower()
                            innr_subsec_header_tag_id = f"{prev_child_id1}-{innr_subsec_header_id}"
                            header_tag["id"] = innr_subsec_header_tag_id

        print("tags are replaced")

    # create a reference
    def create_chap_sec_nav1(self):

        count = 0
        for list_item in self.soup.find_all("li"):
            if re.search('constitution', self.html_file_name):
                if re.match(r'^(§(§)*)', list_item.text.strip()):
                    chap_num = re.search(r'^(§(§)*\s*(?P<chap>\d+[a-zA-Z]*).?) ', list_item.text.strip()).group(
                        "chap").zfill(2)
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(list_item.text)
                    nav_link["href"] = f"#{self.title_id}p{chap_num}"
                    nav_list.append(nav_link)
                    list_item.contents = nav_list

                elif re.match(r'^ARTICLE', list_item.text.strip()):
                    chap_num = re.search(r'^(ARTICLE\s*(?P<ar>[A-Z]+))|^(AMENDMENTS)', list_item.text.strip()).group(
                        "ar").zfill(2)
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(list_item.text)
                    nav_link["href"] = f"#{self.title_id}ar{chap_num}"
                    nav_list.append(nav_link)
                    list_item.contents = nav_list

                elif re.match(r'^Section', list_item.text.strip()):
                    if list_item.find_previous("h3"):
                        prev_id = list_item.find_previous("h3").get("id")
                    else:
                        prev_id = list_item.find_previous("h2").get("id")

                    cur_id = re.search(r'^^(Section\s?(?P<sec>\d+).)', list_item.text.strip()).group("sec").zfill(2)
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(list_item.text)
                    nav_link["href"] = f"#{prev_id}s{cur_id}"
                    nav_list.append(nav_link)
                    list_item.contents = nav_list
                elif re.match(r'^AMENDMENT|^AMENDMENTS', list_item.text.strip()):
                    chap_num = re.sub(r'[\W]', '', list_item.text.strip())
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(list_item.text)
                    nav_link["href"] = f"#{self.title_id}am{chap_num}"
                    nav_list.append(nav_link)
                    list_item.contents = nav_list

            else:

                if re.match(r'^(CHAPTER)|^(Chapter)', list_item.text.strip()):
                    chap_nav_nums = re.search(r'(\s+[^\s]+)', list_item.text.strip())
                    chap_nums = re.search(r'(\s+[^\s]+)', list_item.text).group(0)
                    chap_num = re.sub(r'\s+', '', chap_nums).zfill(2)
                    if chap_nav_nums:
                        nav_list = []
                        nav_link = self.soup.new_tag('a')
                        nav_link.append(list_item.text)
                        nav_link["href"] = f"#t{self.title_id}c{chap_num}"
                        nav_list.append(nav_link)
                        list_item.contents = nav_list
                else:
                    if re.match(r'^(\d+\.\d+\.)', list_item.text.strip()):
                        chap_num = re.search(r'^([^.]+)', list_item.text.strip()).group().zfill(2)
                        sec_num = re.search(r'^(\d+\.\d+)', list_item.text.strip()).group(1).zfill(2)
                        sec_pattern = re.search(r'^(\d+\.\d+\.)', list_item.text.strip()).group()
                        sec_next_tag = list_item.find_next('li')
                        sec_prev_tag = list_item.find_previous("li")
                        sec_prev_tag_text = sec_prev_tag.a
                        if sec_next_tag:
                            if sec_pattern in sec_next_tag.text:
                                list_link = self.soup.new_tag('a')
                                list_link.string = list_item.text

                                list_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
                                list_item.contents = [list_link]

                            elif sec_prev_tag_text:
                                sub = re.search(r'^[^\s]+', sec_prev_tag.a.text.strip()).group()
                                # print(sub)

                                if sec_pattern in sub:
                                    # if sec_pattern in sec_prev_tag.a.text:

                                    list_link = self.soup.new_tag('a')
                                    list_link.string = list_item.text

                                    list_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}.{count + 1}"
                                    list_item.contents = [list_link]

                                else:
                                    nav_link = self.soup.new_tag('a')
                                    nav_link.string = list_item.text
                                    nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
                                    list_item.contents = [nav_link]
                        else:
                            nav_link = self.soup.new_tag('a')
                            nav_link.string = list_item.text
                            nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
                            list_item.contents = [nav_link]

                    elif re.match(r'^(\d+\D\.\d+)', list_item.text.strip()):
                        if re.match(r'(\d+[a-zA-Z]*\.\d+-\d+\.)', list_item.text.strip()):
                            chap_num = re.search(r'^([^.]+)', list_item.text.strip()).group().zfill(2)
                            sub_num = re.search(r'(\d+[a-zA-Z]*\.(?P<sub>\d+)-\d+\.)', list_item.text.strip()).group(
                                "sub").zfill(2)
                            # sec_num = re.search(r'(\d+[a-zA-Z]*\.\d+-\d+)', list_item.text.strip()).group().zfill(2)
                            sec_num = re.sub(r'[\s\.\[\]]', '', list_item.text.strip())
                            nav_link = self.soup.new_tag('a')
                            nav_link.string = list_item.text
                            nav_link["href"] = f"#t{self.title_id}c{chap_num}sub{sub_num}s{sec_num}"
                            list_item.contents = [nav_link]

                        else:
                            chap_num = re.search(r'^([^.]+)', list_item.text.strip()).group().zfill(2)
                            sec_num = re.search(r'^(\d+\D\.\d+)', list_item.text.strip()).group().zfill(2)
                            nav_link = self.soup.new_tag('a')
                            nav_link.string = list_item.text
                            nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
                            list_item.contents = [nav_link]



                    elif re.match(r'Article|SUBCHAPTER', list_item.text.strip()):
                        chap_num = list_item.find_previous("h2", class_="chapterh2").get("id")
                        art_nums = re.search(r'^(Article|SUBCHAPTER(S)*)\s(?P<chapter_id>\w+)',
                                             list_item.text.strip()).group(
                            'chapter_id')
                        new_link = self.soup.new_tag('a')
                        new_link.string = list_item.text
                        new_link["href"] = f"#{chap_num}a{art_nums.zfill(2)}"
                        list_item.contents = [new_link]

                    elif re.match(r'Part\s\d\.', list_item.text.strip()):

                        chap_num = list_item.find_previous("h2", class_="Articleh2").get("id")
                        part_nums = re.search(r'^(Part)\s(?P<chapter_id>\w+)', list_item.text.strip()).group(
                            'chapter_id')
                        new_link = self.soup.new_tag('a')
                        new_link.string = list_item.text
                        new_link["href"] = f"#{chap_num}p{part_nums.zfill(2)}"
                        list_item.contents = [new_link]

                    elif re.search("^([A-Z]\.)|^(Subpart)", list_item.text.strip()):
                        if list_item.find_previous("h2", class_="parth2"):
                            chap_num = list_item.find_previous("h2", class_="parth2").get("id")

                            new_link = self.soup.new_tag('a')
                            new_link.string = list_item.text

                        if re.match("^([A-Z]\.)", list_item.text.strip()):
                            subpart_nums = re.search(r'^(?P<chapter_id1>[A-Z])\.', list_item.text.strip()).group(
                                "chapter_id1")

                            new_link["href"] = f"#{chap_num}p{subpart_nums.zfill(2)}"
                            list_item.contents = [new_link]

                        # if re.match(r'^(Subpart)', list_item.text.strip()):
                        else:
                            # print(list_item)
                            subpart_nums = re.search(r'^Subpart\s(?P<chapter_id2>\w+)', list_item.text.strip()).group(
                                "chapter_id2")

                            new_link["href"] = f"#{chap_num}sub{subpart_nums.zfill(2)}"
                            list_item.contents = [new_link]


                    elif re.match(r'^(\d+\.\d+\D?-\d+\.)', list_item.text.strip()):

                        # print(list_item)
                        chap_num = re.search(r'^([^.]+)', list_item.text.strip()).group().zfill(2)
                        sec_num = re.search(r'^(\d+\.\d+\D?-\d+)', list_item.text.strip()).group().zfill(2)
                        nav_link = self.soup.new_tag('a')
                        nav_link.string = list_item.text
                        nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
                        list_item.contents = [nav_link]

                    else:
                        # print(list_item)
                        chapter_header = list_item.find_previous("h2")
                        chap_nums = re.search(r'(\s+[^\s]+)', chapter_header.text.strip()).group(0)
                        chap_num = re.sub(r'\s+', '', chap_nums).zfill(2)
                        sec_id = re.sub(r'[\s+.]', '', list_item.get_text()).lower()
                        new_link = self.soup.new_tag('a')
                        new_link.string = list_item.text
                        new_link["href"] = f"#t{self.title_id}c{chap_num}{sec_id}"
                        list_item.contents = [new_link]

    # # # create ol tag for note to decision nav
    def create_ul_tag_to_notes_to_decision2(self):
        new_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        # new_nav_tag = self.soup.new_tag("nav")
        innr_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        innr_ul_tag1 = self.soup.new_tag("ul", **{"class": "leaders"})
        innr_ul_tag2 = self.soup.new_tag("ul", **{"class": "leaders"})
        note_nav_pattern = re.compile(r'^(\d+\.\s*“?[a-zA-Z]+)|^(\d+\.\s*“?\d*)|^(\d+\.\s*—\s*[a-zA-Z]+)|^(\d+\.\d+)|^(\d+\.\s*—\s*—\s*[a-zA-Z]+)|^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)')

        if re.search('constitution', self.html_file_name):
            tag_class = self.class_regex["sec_head"]
        else:

            for head_tag in self.soup.find_all("h4"):
                if head_tag.text.strip() == "NOTES TO DECISIONS":
                    if re.match(r'^(\d+\.\s*\w+)', head_tag.findNext("p").text.strip()):
                        notetodecison_nav_class = head_tag.findNext("p").get("class")

            if notetodecison_nav_class:

                for note_tag in self.soup.find_all(class_=notetodecison_nav_class):
                    if re.match(note_nav_pattern, note_tag.text.strip()):

                        note_tag.name = "li"
                        # print(note_tag)
                    # if note_tag.find_next():
                    #
                    #     if note_tag.find_next().name == "a":
                    #
                    #         note_tag.name = "li"

                            # # parent
                    if re.match(r'^(\d+\.\s*“?[a-zA-Z]+)|^(\d+\.\s*“?\d*)',
                                        note_tag.text.strip()) and note_tag.name == "li":

                                # note_tag.name = "li"
                                if re.match(r'^(1\.)', note_tag.text.strip()) and note_tag.name == "li" :
                                    if note_tag.find_previous("h4").text.strip() == "NOTES TO DECISIONS":

                                        new_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                                        note_tag.wrap(new_ul_tag)
                                        new_ul_tag.wrap(self.soup.new_tag("nav"))
                                else:
                                    new_ul_tag.append(note_tag)

                            # -
                    if re.match(r'^(\d+\.\s*—\s*[a-zA-Z]+)|^(\d+\.\d+)',
                                        note_tag.text.strip()) and note_tag.name == "li":

                                # note_tag.name = "li"
                                if re.match(r'^(\d+\.\s*[a-zA-Z]+)|^(\d+\.\d+)',
                                            note_tag.find_previous().text.strip()) and note_tag.name == "li":
                                    innr_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                                    note_tag.wrap(innr_ul_tag)
                                    new_ul_tag.append(innr_ul_tag)
                                    note_tag.find_previous("li").append(innr_ul_tag)
                                else:
                                    innr_ul_tag.append(note_tag)

                            # # ---
                    if re.match(r'^(\d+\.\s*—\s*—\s*[a-zA-Z]+)', note_tag.text.strip()) and note_tag.name == "li":
                                # note_tag.name = "li"
                                if re.match(r'^(\d+\.\s*—\s*—\s*[a-zA-Z]+)',
                                            note_tag.find_previous().text.strip()) and note_tag.name == "li":
                                    innr_ul_tag1.append(note_tag)
                                else:
                                    innr_ul_tag1 = self.soup.new_tag("ul", **{"class": "leaders"})
                                    note_tag.wrap(innr_ul_tag1)
                                    note_tag.find_previous("li").append(innr_ul_tag1)

                            # # ----
                    if re.match(r'^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)', note_tag.text.strip()) and note_tag.name == "li":
                                # note_tag.name = "li"
                                if re.match(r'^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)',
                                            note_tag.find_previous().text.strip()) and note_tag.name == "li":
                                    innr_ul_tag2.append(note_tag)

                                else:
                                    innr_ul_tag2 = self.soup.new_tag("ul", **{"class": "leaders"})
                                    note_tag.wrap(innr_ul_tag2)
                                    note_tag.find_previous("li").append(innr_ul_tag2)
                                    # innr_ul_tag1.append(innr_ul_tag2)

                    if re.match(r'^(\d+\.\s*“?[a-zA-Z]+)', note_tag.text.strip()) and note_tag.find_previous(
                                    "p") is not None and note_tag.find_previous("p").text.strip() == 'Analysis':
                                note_tag.name = "li"

                                if note_tag.find_previous().text.strip() == 'Analysis':
                                    new_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                                    note_tag.wrap(new_ul_tag)
                                    new_ul_tag.wrap(self.soup.new_tag("nav"))
                                else:
                                    new_ul_tag.append(note_tag)

    # # create ol tag for note to decision nav
    def create_ul_tag_to_notes_to_decision3(self):
        new_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        # new_nav_tag = self.soup.new_tag("nav")
        innr_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        innr_ul_tag1 = self.soup.new_tag("ul", **{"class": "leaders"})
        innr_ul_tag2 = self.soup.new_tag("ul", **{"class": "leaders"})
        note_nav_pattern = re.compile(
            r'^(\d+\.\s*“?[a-zA-Z]+)|^(\d+\.\s*“?\d*)|^(\d+\.\s*—\s*[a-zA-Z]+)|^(\d+\.\d+)|^(\d+\.\s*—\s*—\s*[a-zA-Z]+)|^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)')

        if re.search('constitution', self.html_file_name):
            tag_class = self.class_regex["sec_head"]
        else:
            tag_class = self.class_regex["ol"]

        for note_tag in self.soup.find_all(class_=tag_class):
            if note_tag.find_next():

                if note_tag.find_next().name == "a":
                    note_tag.name = "li"


            # # parent
            if re.match(r'^(\d+\.\s*“?[a-zA-Z]+)|^(0.5\.)',
                        note_tag.text.strip()) and note_tag.name == "li":

                if re.match(r'^(0.5\.)', note_tag.text.strip()) and note_tag.name == "li":
                    if re.match(r'^(0.5\.)',note_tag.find_previous("li").text.strip()):
                        new_ul_tag.append(note_tag)
                    else:
                        new_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                        note_tag.wrap(new_ul_tag)
                        new_ul_tag.wrap(self.soup.new_tag("nav"))
                elif re.match(r'^(1\.)', note_tag.text.strip()) and note_tag.name == "li":

                    if re.match(r'^(0.5\.)',note_tag.find_previous("li").text.strip()):
                        new_ul_tag.append(note_tag)
                    else:

                        new_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                        note_tag.wrap(new_ul_tag)
                        new_ul_tag.wrap(self.soup.new_tag("nav"))
                else:
                    new_ul_tag.append(note_tag)


            # -
            elif re.match(r'^(\d+\.\s*—\s*[a-zA-Z]+)|^(\d+\.\d+)|^(\d+\.(\d+\.)\s*“*[a-zA-Z]+)',
                        note_tag.text.strip()) and note_tag.name == "li":
                if re.match(r'^(\d+\.\s*[a-zA-Z]+)|^(\d+\.\d+)|^(\d+\.(\d+\.)\s*“*[a-zA-Z]+)',
                            note_tag.find_previous().text.strip()) and note_tag.name == "li":
                    if re.match(r'^(\d+\.(\d+\.)\s*“*[a-zA-Z]+)', note_tag.find_previous().text.strip()):
                        innr_ul_tag.append(note_tag)
                    else:
                        innr_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                        note_tag.wrap(innr_ul_tag)
                        new_ul_tag.append(innr_ul_tag)
                        note_tag.find_previous("li").append(innr_ul_tag)
                else:
                    innr_ul_tag.append(note_tag)


            # # ---
            if re.match(r'^(\d+\.\s*—\s*—\s*[a-zA-Z]+)', note_tag.text.strip()) and note_tag.name == "li":
                # note_tag.name = "li"
                if re.match(r'^(\d+\.\s*—\s*—\s*[a-zA-Z]+)',
                            note_tag.find_previous().text.strip()) and note_tag.name == "li":
                    innr_ul_tag1.append(note_tag)
                else:
                    innr_ul_tag1 = self.soup.new_tag("ul", **{"class": "leaders"})
                    note_tag.wrap(innr_ul_tag1)
                    note_tag.find_previous("li").append(innr_ul_tag1)

            # # ----
            if re.match(r'^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)', note_tag.text.strip()) and note_tag.name == "li":
                # note_tag.name = "li"
                if re.match(r'^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)',
                            note_tag.find_previous().text.strip()) and note_tag.name == "li":
                    innr_ul_tag2.append(note_tag)

                else:
                    innr_ul_tag2 = self.soup.new_tag("ul", **{"class": "leaders"})
                    note_tag.wrap(innr_ul_tag2)
                    note_tag.find_previous("li").append(innr_ul_tag2)
                    # innr_ul_tag1.append(innr_ul_tag2)

            if re.match(r'^(\d+\.\s*“?[a-zA-Z]+)', note_tag.text.strip()) and note_tag.find_previous(
                    "p") is not None and note_tag.find_previous("p").text.strip() == 'Analysis':
                note_tag.name = "li"

                if note_tag.find_previous().text.strip() == 'Analysis':
                    new_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    note_tag.wrap(new_ul_tag)
                    new_ul_tag.wrap(self.soup.new_tag("nav"))
                else:
                    new_ul_tag.append(note_tag)

    def create_link_to_notetodecision_nav1(self):
        nav_link = self.soup.new_tag('a')
        innr_nav_link1 = self.soup.new_tag('a')
        innr_nav_link2 = self.soup.new_tag('a')
        nav_link_list = []
        notetodecison_nav_class = 0
        nav_list = []

        for head_tag in self.soup.find_all("h4"):
            if head_tag.text.strip() == "NOTES TO DECISIONS":
                if re.match(r'^(\d+\.\s*\w+)', head_tag.findNext("p").text.strip()):
                    notetodecison_nav_class = head_tag.findNext("p").get("class")

        if notetodecison_nav_class:
            for p_tag in self.soup.find_all(class_=notetodecison_nav_class):
                if re.match(r'^(\d+\.)', p_tag.text.strip()):
                    if p_tag.find_next().name != "span":


                        if re.search(r'^(\d+\.(\d+\.)?\s*“*[a-zA-Z]+)', p_tag.get_text().strip()):
                            prev_head_tag = p_tag.find_previous("h4").get("id")
                            sub_sec_id = re.sub(r'[\W]', '', p_tag.get_text()).lower()

                            nav_link = self.soup.new_tag('a')
                            nav_link.string = p_tag.text
                            # nav_link_href = f"#{prev_head_tag}-{sub_sec_id}"

                            if p_tag.text.strip() in nav_list:
                                nav_link["href"] = f"#{prev_head_tag}-{sub_sec_id}.1"
                            else:
                                nav_link["href"] = f"#{prev_head_tag}-{sub_sec_id}"

                            p_tag.string = ''
                            p_tag.insert(0, nav_link)

                            nav_list.append(p_tag.text.strip())

                            if re.match(r'^1.\s*[a-zA-Z]+', p_tag.text.strip()):
                                nav_list = []
                                nav_link_list = []
                                count = 1



                        elif re.match(r'^(\d+\.(\d+\.)?\s*—\s*[a-zA-Z]+)', p_tag.text.strip()):
                            # print(p_tag)

                            p_tag_text = re.sub(r'[\s.—]', '', p_tag.text.strip()).lower()

                            prev_id = nav_link["href"]
                            sub_sec_id = re.sub(r'[\W]', '', p_tag.get_text()).lower()
                            innr_nav_link1 = self.soup.new_tag('a')
                            innr_nav_link1.string = p_tag.text

                            if p_tag_text in nav_link_list:

                                innr_nav_link1["href"] = f"{prev_id}-{sub_sec_id}.{count}"
                                count += 1
                            else:
                                innr_nav_link1["href"] = f"{prev_id}-{sub_sec_id}"

                            p_tag.string = ''
                            p_tag.insert(0, innr_nav_link1)

                            p_text = re.sub(r'[\s.—]', '', p_tag.text.strip()).lower()
                            nav_link_list.append(p_text)

                            count1 = 1



                        elif re.match(r'^(\d+\.\s*—\s*—\s*[a-zA-Z]+)', p_tag.text.strip()):

                            # print(p_tag)

                            p_tag_text = re.sub(r'[\s.—]', '', p_tag.text.strip())

                            innr_id1 = innr_nav_link1["href"]
                            sub_sec_id = re.sub(r'[\W]', '', p_tag.get_text()).lower()
                            innr_nav_link2 = self.soup.new_tag('a')
                            innr_nav_link2.string = p_tag.text

                            if p_tag_text in nav_link_list:
                                innr_nav_link2["href"] = f"{innr_id1}-{sub_sec_id}.{count1}"
                                count1 += 1
                            else:
                                innr_nav_link2["href"] = f"{innr_id1}-{sub_sec_id}"

                            # innr_nav_link2["href"] = f"{innr_id1}-{sub_sec_id}"
                            p_tag.string = ''
                            p_tag.insert(0, innr_nav_link2)

                            p_text = re.sub(r'[\s.—]', '', p_tag.text.strip())
                            nav_link_list.append(p_text)

                        elif re.match(r'^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)', p_tag.text.strip()):

                            p_tag_text = re.sub(r'[\s.—]', '', p_tag.text.strip())

                            innr_id2 = innr_nav_link2["href"]
                            sub_sec_id = re.sub(r'[\W]', '', p_tag.get_text()).lower()
                            innr_nav_link3 = self.soup.new_tag('a')
                            innr_nav_link3.string = p_tag.text

                            if p_tag_text in nav_link_list:
                                innr_nav_link3["href"] = f"{innr_id2}-{sub_sec_id}.{count1}"

                                count1 += 1
                            else:
                                innr_nav_link3["href"] = f"{innr_id2}-{sub_sec_id}"

                            # innr_nav_link3["href"] = f"{innr_id2}-{sub_sec_id}"
                            p_tag.string = ''
                            p_tag.insert(0, innr_nav_link3)

                            p_text = re.sub(r'[\s.—]', '', p_tag.text.strip())
                            nav_link_list.append(p_text)
                        # print(nav_link_list)


                    elif re.match(r'^(\d+\.\s*—\s*[a-zA-Z]+)', p_tag.text.strip()):

                        p_tag_text = re.sub(r'[\s.—]', '', p_tag.text.strip())

                        sub_sec = re.sub(r'[\W]', '', p_tag.get_text()).lower()
                        sub_sec_id = p_tag.find_previous("h5").get("id")
                        innr_nav_link1 = self.soup.new_tag('a')
                        innr_nav_link1.string = p_tag.text

                        if p_tag_text in nav_link_list:

                            innr_nav_link1["href"] = f"#{sub_sec_id}-{sub_sec}.{count1}"

                            count1 += 1
                        else:
                            innr_nav_link1["href"] = f"#{sub_sec_id}-{sub_sec}"

                        # innr_nav_link1["href"] = f"#{sub_sec_id}-{sub_sec}"
                        p_tag.string = ''
                        p_tag.insert(0, innr_nav_link1)

                        p_text = re.sub(r'[\s.—]', '', p_tag.text.strip())
                        nav_link_list.append(p_text)


    def wrap_with_ordered_tag_2(self):

        # pattern = re.compile(r'^(\d+)|^(\(\d+\)|^\(\s*[a-z][a-z]?\s*\))|^([a-z]\.)|^([A-Z]{0,3}\.)|^([a-z]{0,3}\.)')

        pattern = re.compile(
            r'^(\d+\.(\s*[a-z]\.)*)|^(\(\d+\)|^\(\s*[a-z][a-z]?\s*\))|^([a-z]\.)|^([A-Z]{0,3}\.\s*[a-zA-Z]+)|^([a-z]{0,3}\.)|^[A-Z]\.')
        Num_bracket_pattern = re.compile(r'^\(\d+\)')
        alpha_pattern = re.compile(r'^\(\s*[a-z][a-z]?\s*\)')
        # alp_pattern = re.compile(r'\(\D+\)')
        num_pattern = re.compile(r'^\d+\.')
        # num_pattern1 = re.compile(r'^1\.')
        numAlpha_pattern = re.compile(r'^\(\d+\)\s\(\D\)')
        alphanum_pattern = re.compile(r'^\(\D+\)\s(\d)+')

        ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
        # ol_tag = self.soup.new_tag("ol")
        ol_tag3 = self.soup.new_tag("ol")
        ol_tag1 = self.soup.new_tag("ol")
        ol_tag4 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
        ol_tag5 = self.soup.new_tag("ol")
        ol_tag6 = self.soup.new_tag("ol")
        rom_ol_tag = self.soup.new_tag("ol", type="i", **{"class": "roman"})
        ol_cap_tag = self.soup.new_tag("ol", type="A")

        ol_num = None
        ol_alpha = None
        ol_inr_num = None
        ol_inr_apha = None
        ol_inr_alpha = None
        ol_rom = None
        prev_id = 0
        current_id = 0
        pre_id = 0
        sec_id_list = []
        ol_count = 1
        ol_num_id = 0

        for tag in self.soup.findAll("p", class_=self.class_regex["ol"]):
            current_tag = tag.text.strip()



            if re.match(pattern, tag.text.strip()):
                tag.name = "li"

            elif re.match(r'^(Article)\s*[I,V,X]*\.', tag.text.strip()):
                tag.name = "h4"
                prev_id = tag.find_previous("h3").get("id")
                article_id = re.search(r'^(Article)\s*(?P<ar_id>[I,V,X]*)', tag.text.strip()).group("ar_id")
                tag["id"] = f'{prev_id}a{article_id}'
                tag["class"] = "article"

            elif re.match(r'^(ARTICLE)\s*[I,V,X]*', tag.text.strip()):
                tag.name = "h4"
                prev_id = tag.find_previous("h3").get("id")
                article_id = re.search(r'^(ARTICLE)\s*(?P<ar_id>[I,V,X]*)', tag.text.strip()).group("ar_id")
                tag["id"] = f'{prev_id}a{article_id}'
                tag["class"] = "article"




            elif re.match(r'Section\s*[A-Z]+\.', tag.text.strip()):
                tag.name = "h4"
                prev_id = tag.find_previous("h4", class_="article").get("id")
                article_id = re.search(r'^(Section)\s*(?P<ar_id>[A-Z]+)\.', tag.text.strip()).group("ar_id")
                tag["id"] = f'{prev_id}s{article_id}'
                tag["class"] = "section"

            # A
            if re.match(r'^[A-Z]\.', current_tag):

                if re.match(r'^A\.', current_tag):

                    ol_cap_tag = self.soup.new_tag("ol", type="A")
                    tag.wrap(ol_cap_tag)

                    art_id = tag.find_previous("h4").get("id")
                    tag["id"] = f'{art_id}A'

                else:
                    if re.match(r'^[B-Z]\.', tag.find_previous().text.strip()) and tag.name == "li":
                        cur_alpha = re.search(r'^(?P<cap_id>[A-Z])\.', current_tag).group("cap_id")
                        ol_cap_tag.append(tag)

                        if tag.find_previous("h4"):
                            art_id = tag.find_previous("h4").get("id")
                            tag["id"] = f'{art_id}{cur_alpha}'

                    elif not re.match(r'^[I,V,X]', current_tag):

                        tag.name = "p"

            # I.
            if re.match(r'^([A-Z]{0,3}\.\s*[a-zA-Z]+)', current_tag):

                if re.match(r'^([I,V,X]{0,3}\.)', current_tag):

                    ol_rom = tag
                    if re.search(r'^(I\.)', current_tag):
                        ol_tag1 = self.soup.new_tag("ol", type="I")
                        tag.wrap(ol_tag1)

                    else:

                        ol_tag1.append(tag)

                    tag_id = re.search(r'^(?P<id>[A-Z]{0,3})', current_tag).group('id')
                    prev_header_id = tag.find_previous("h3").get("id")
                    tag["id"] = f"{prev_header_id}ol1{tag_id}"

                else:
                    if re.search(r'^(A\.)', current_tag):
                        ol_tag1 = self.soup.new_tag("ol", type="A")
                        tag.wrap(ol_tag1)
                        tag_id = re.search(r'^(?P<id>[A-Z]{0,3})', current_tag).group('id')
                        if tag.find_previous("h4"):
                            prev_header_id = tag.find_previous("h4").get("id")
                            tag["id"] = f"{prev_header_id}ol1{tag_id}"

                    else:
                        if re.match(r'^[B-Z]\.', tag.find_previous().text.strip()):

                            ol_tag1.append(tag)

                            tag_id = re.search(r'^(?P<id>[A-Z]{0,3})', current_tag).group('id')
                            if tag.find_previous("h4"):
                                prev_header_id = tag.find_previous("h4").get("id")
                                tag["id"] = f"{prev_header_id}ol1{tag_id}"

            # # (1)
            if re.match(Num_bracket_pattern, current_tag):

                ol_num = tag
                if re.search(r'^(\(1\))', current_tag):
                    if re.match(r'^([A-Z]{0,3}\.)', tag.find_previous().text.strip()):

                        tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
                        ol_tag = self.soup.new_tag("ol")
                        tag.wrap(ol_tag)
                        tag.find_previous("li").append(ol_tag)
                        if ol_rom:
                            prev_id = ol_rom.get("id")
                        else:
                            prev_id = tag.find_previous("li").get("id")

                        tag["id"] = f'{prev_id}{tag_id}'

                    else:

                        if tag.find_previous("h3") in sec_id_list:
                            ol_count += 1

                        ol_tag = self.soup.new_tag("ol")
                        tag.wrap(ol_tag)

                        tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')

                        if tag.find_previous("h4"):
                            if re.match(r'Section\s*[A-Z]+\.', tag.find_previous("h4").text.strip()):
                                prev_header_id = tag.find_previous("h4").get("id")
                            elif re.match(r'^(Article|ARTICLE)\s*[I,V,X]*', tag.find_previous("h4").text.strip()):
                                prev_header_id = tag.find_previous("h4").get("id")
                            else:
                                prev_header_id = tag.find_previous("h3").get("id")
                        else:
                            prev_header_id = tag.find_previous("h3").get("id")

                        tag_id1 = f"{prev_header_id}ol{ol_count}{tag_id}"
                        tag["id"] = f"{prev_header_id}ol{ol_count}{tag_id}"

                        sec_id_list.append(tag.find_previous("h3"))


                else:

                    if re.search(r'History|HISTORY:', tag.find_next("p").text.strip()):
                        # print(tag)
                        ol_rom = None

                    ol_tag.append(tag)

                    tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
                    if ol_rom:
                        prev_header_id = ol_rom.get("id")
                        tag["id"] = f"{prev_header_id}{tag_id}"

                    else:
                        if tag.find_previous("h4"):
                            if re.match(r'Section\s*[A-Z]+\.', tag.find_previous("h4").text.strip()):
                                prev_header_id = tag.find_previous("h4").get("id")
                            elif re.match(r'^(Article|ARTICLE)\s*[I,V,X]*', tag.find_previous("h4").text.strip()):
                                prev_header_id = tag.find_previous("h4").get("id")
                            else:
                                prev_header_id = tag.find_previous("h3").get("id")
                        else:
                            prev_header_id = tag.find_previous("h3").get("id")

                        # prev_header_id = tag.find_previous("h3").get("id")
                        tag["id"] = f"{prev_header_id}ol{ol_count}{tag_id}"

            # (a)
            if re.match(alpha_pattern, current_tag):

                ol_alpha = tag
                prev_header_id = ol_num.get("id")
                if re.match(r'^\(a\)', tag.text.strip()):

                    ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                    tag.wrap(ol_tag2)
                    if re.match(alpha_pattern, tag.find_previous("li").text.strip()):

                        tag.find_previous("li").append(ol_tag2)
                        prev_header_id = tag.find_previous("li").get("id")
                        tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
                        tag["id"] = f"{prev_header_id}{tag_id}"



                    else:

                        ol_num.append(ol_tag2)
                        tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')

                        prev_header_id = ol_num.get("id")
                        alpha_id = f"{prev_header_id}{tag_id}"

                        tag["id"] = f"{prev_header_id}{tag_id}"
                else:

                    ol_tag2.append(tag)
                    tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
                    # prev_header_id = ol_num.get("id")
                    alpha_id = f"{prev_header_id}{tag_id}"
                    tag["id"] = f"{prev_header_id}{tag_id}"

            # # (4)(a)
            if re.match(numAlpha_pattern, current_tag):
                ol_inr_apha = tag
                prev_header = tag.find_previous("h3")
                prev_header_id = prev_header.get("id")

                tag_id1 = re.search(r'^\((?P<id1>\d+)\)\s*\((\D+)\)', current_tag).group("id1")
                tag_id2 = re.search(r'^\((\d+)\)\s*\((?P<id2>[a-z]+)\)', current_tag).group("id2")

                ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                li_tag = self.soup.new_tag("li")

                # li_tag.append(current_tag)

                tag_text = re.sub(numAlpha_pattern, '', tag.text.strip())
                li_tag.append(tag_text)

                li_tag["id"] = f"{prev_header_id}ol1{tag_id1}{tag_id2}"

                ol_tag2.append(li_tag)
                tag.contents = []
                tag.append(ol_tag2)

                # (4)(a)1.
                if re.match(r'\(\d+\)\s*\(\D\)\s*\d\.', current_tag):
                    ol_tag4 = self.soup.new_tag("ol")
                    inner_li_tag = self.soup.new_tag("li")

                    tag_text = re.sub(r'\(\d+\)\s*\(\D\)\s*\d\.', '', current_tag)
                    inner_li_tag.append(tag_text)

                    # print(tag)

                    # inner_li_tag.append(tag.text.strip())

                    tag_id1 = re.search(r'^(\(\d+\)\s*\((?P<id1>\D)\)\s*\d\.)', current_tag).group("id1")
                    tag_id2 = re.search(r'\(\d+\)\s*\(\D\)\s*(?P<id2>\d)\.', current_tag).group("id2")

                    prev_id = ol_inr_apha.get("id")
                    inner_li_tag["id"] = f"{prev_id}{tag_id1}{tag_id2}"
                    prev_header_id = f"{prev_id}{tag_id1}"
                    main_olcount = 2

                    ol_tag4.append(inner_li_tag)
                    tag.insert(1, ol_tag4)
                    ol_tag4.find_previous().string.replace_with(ol_tag4)

            # a
            if re.match(r'[a-z]([a-z])*\.', current_tag):

                ol_inr_apha = tag

                tag_id = re.search(r'^(?P<id>[a-z]([a-z])*)\.', current_tag).group('id')

                if re.match(r'a\.', current_tag):

                    ol_tag3 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                    tag.wrap(ol_tag3)
                    if re.match(num_pattern, tag.find_previous("li").text.strip()):
                        ol_tag5.append(ol_tag3)
                    else:
                        ol_tag.append(ol_tag3)

                    tag.find_previous("li").append(ol_tag3)

                    tag["id"] = f"{current_id}{tag_id}"

                    prev_id = tag.find_previous("li").get("id")

                    tag["id"] = f"{prev_id}{tag_id}"


                else:
                    if re.match(r'i\.', current_tag) and re.match(r'ii\.', tag.find_next_sibling().text.strip()):


                        rom_ol_tag = self.soup.new_tag("ol", type="i", **{"class": "roman"})
                        tag.wrap(rom_ol_tag)

                        ol_tag.append(rom_ol_tag)
                        # tag.find_previous("li").append(rom_ol_tag)

                    elif re.match(r'[a-z]\.', current_tag):
                        # print(current_tag)
                        ol_tag3.append(tag)

                        # print (tag)
                        pre_id = ol_num_id.get("id")
                        # prev_alpha_id = tag.find_previous("li").get("id")
                        tag["id"] = f"{pre_id}{tag_id}"


                    else:
                        rom_ol_tag.append(tag)

                if tag.span:
                    tag.span.string = ""

            # (a) 1.
            if re.match(alphanum_pattern, current_tag):
                ol_tag5 = self.soup.new_tag("ol")
                li_tag = self.soup.new_tag("li")

                tag_id1 = re.search(r'^\((?P<id1>\D+)\)\s(\d)+', current_tag).group("id1")
                tag_id2 = re.search(r'^\(\D+\)\s(?P<id2>\d)+', current_tag).group("id2")

                tag_text = re.sub(r'^\(\D+\)\s(\d)\.', '', current_tag)
                li_tag.append(tag_text)

                # li_tag.append(current_tag.strip())

                ol_tag5.append(li_tag)

                # prev_id = ol_inr_apha.get("id")
                prev_id = ol_alpha.get("id")
                # prev_id = li_tag.find_previous("li").get("id")
                li_tag["id"] = f"{prev_id}{tag_id2}"
                prev_header_id = f"{prev_id}{tag_id1}"
                main_olcount = 2

                tag.contents = []
                tag.append(ol_tag5)

                # 2.a.
            if re.match(r'(\d+\.(\s*[a-z]\.))', current_tag):
                ol_tag3 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                inner_a_tag = self.soup.new_tag("li")

                tag_text = re.sub(r'(\d+\.(\s*(?P<prev>[a-z])\.))', '', current_tag)
                inner_a_tag.append(tag_text)

                prev = tag.find_previous("li").get("id")
                curr = re.search(r'(\d+\.(\s*(?P<prev>[a-z])\.))', current_tag).group("prev")
                inner_a_tag["id"] = f'{prev}{curr}'

                prev_id = ol_alpha.get("id")
                cur_id = re.search(r'(\d+\.(\s*[a-z]\.))', current_tag).group()
                cur_id = re.sub(r'[\s\.]', '', cur_id)

                # inner_a_tag["id"] = f'{prev_id}{cur_id}'
                # print(inner_a_tag)
                tag.clear()

                ol_tag3.append(inner_a_tag)
                tag.insert(1, ol_tag3)

            # 1. and previous (1)(a)
            if re.match(num_pattern, current_tag):
                ol_num_id = tag
                if re.match(r'^1\.', current_tag):

                    ol_tag5 = self.soup.new_tag("ol")
                    tag.wrap(ol_tag5)

                    if tag.find_previous("h4"):

                        if not re.match(r'^(ARTICLE)\s*[I,V,X]*',
                                        tag.find_previous("h4").text.strip()) and not re.match(r'Section\s*[A-Z]+\.',
                                                                                               tag.find_previous(
                                                                                                       "h4").text.strip()):
                            tag.find_previous("li").append(ol_tag5)

                            main_olcount = 1
                            prev_id = tag.find_previous("li").get("id")
                            tag["id"] = f"{prev_id}{main_olcount}"

                            main_olcount += 1

                            if tag.find_previous("li"):
                                prev_header_id = tag.find_previous("li").get("id")
                        else:

                            ar_id = tag.find_previous("h4").get("id")
                            main_olcount = 1
                            tag["id"] = f"{ar_id}{main_olcount}"
                            main_olcount += 1
                    else:
                        pre_id = tag.find_previous("li").get("id")
                        tag.find_previous("li").append(ol_tag5)
                        main_olcount = 1
                        tag["id"] = f"{pre_id}{main_olcount}"
                        main_olcount += 1

                elif tag.find_previous("li"):

                    ol_tag5.append(tag)

                    if tag.find_previous("h4"):

                        if not re.match(r'^(ARTICLE)\s*[I,V,X]*',
                                        tag.find_previous("h4").text.strip()) and not re.match(
                                r'Section\s*[A-Z]+\.', tag.find_previous("h4").text.strip()):
                            if prev_id:
                                current_id = f"{prev_id}{main_olcount}"

                                tag["id"] = f"{prev_id}{main_olcount}"
                                main_olcount += 1
                        else:

                            current_id = f"{ar_id}{main_olcount}"

                            tag["id"] = f"{ar_id}{main_olcount}"
                            main_olcount += 1

                    else:
                        cur_id = re.sub(r'\d+$', '', tag.find_previous().get("id"))
                        tag["id"] = f"{cur_id}{main_olcount}"
                        main_olcount += 1

        print("ol tag is created")

    # def wrap_with_ordered_tag_3(self):
    #
    #     # pattern = re.compile(r'^(\d+)|^(\(\d+\)|^\(\s*[a-z][a-z]?\s*\))|^([a-z]\.)|^([A-Z]{0,3}\.)|^([a-z]{0,3}\.)')
    #
    #     pattern = re.compile(
    #         r'^(\d+\.(\s*[a-z]\.)*)|^(\(\d+\)|^\(\s*[a-z][a-z]?\s*\))|^([a-z]\.)|^([A-Z]{0,3}\.\s*[a-zA-Z]+)|^([a-z]{0,3}\.)|^[A-Z]\.')
    #     Num_bracket_pattern = re.compile(r'^\(\d+\)')
    #     alpha_pattern = re.compile(r'^\(\s*[a-z][a-z]?\s*\)')
    #     # alp_pattern = re.compile(r'\(\D+\)')
    #     num_pattern = re.compile(r'^\d+\.')
    #     # num_pattern1 = re.compile(r'^1\.')
    #     numAlpha_pattern = re.compile(r'^\(\d+\)\s\(\D\)')
    #     alphanum_pattern = re.compile(r'^\(\D+\)\s(\d)+')
    #
    #     ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #     # ol_tag = self.soup.new_tag("ol")
    #     ol_tag3 = self.soup.new_tag("ol")
    #     ol_tag1 = self.soup.new_tag("ol")
    #     ol_tag4 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #     ol_tag5 = self.soup.new_tag("ol")
    #     ol_tag6 = self.soup.new_tag("ol")
    #     rom_ol_tag = self.soup.new_tag("ol", type="i", **{"class": "roman"})
    #     ol_cap_tag = self.soup.new_tag("ol", type="A")
    #
    #     ol_num = None
    #     ol_alpha = None
    #     ol_inr_num = None
    #     ol_inr_apha = None
    #     ol_inr_alpha = None
    #     ol_rom = None
    #     prev_id = 0
    #     current_id = 0
    #     pre_id = 0
    #
    #     for tag in self.soup.findAll("p", class_=self.class_regex["ol"]):
    #         current_tag = tag.text.strip()
    #
    #         if re.match(pattern, tag.text.strip()):
    #             tag.name = "li"
    #
    #         elif re.match(r'^(Article)\s*[I,V,X]*\.', tag.text.strip()):
    #             tag.name = "h4"
    #             prev_id = tag.find_previous("h3").get("id")
    #             article_id = re.search(r'^(Article)\s*(?P<ar_id>[I,V,X]*)', tag.text.strip()).group("ar_id")
    #             tag["id"] = f'{prev_id}a{article_id}'
    #             tag["class"] = "article"
    #
    #         elif re.match(r'^(ARTICLE)\s*[I,V,X]*', tag.text.strip()):
    #             tag.name = "h4"
    #             prev_id = tag.find_previous("h3").get("id")
    #             article_id = re.search(r'^(ARTICLE)\s*(?P<ar_id>[I,V,X]*)', tag.text.strip()).group("ar_id")
    #             tag["id"] = f'{prev_id}a{article_id}'
    #             tag["class"] = "article"
    #
    #
    #
    #
    #         elif re.match(r'Section\s*[A-Z]+\.', tag.text.strip()):
    #             tag.name = "h4"
    #             prev_id = tag.find_previous("h4",class_="article").get("id")
    #             article_id = re.search(r'^(Section)\s*(?P<ar_id>[A-Z]+)\.', tag.text.strip()).group("ar_id")
    #             tag["id"] = f'{prev_id}s{article_id}'
    #             tag["class"] = "section"
    #
    #         #A
    #         if re.match(r'^[A-Z]\.', current_tag):
    #             if re.match(r'^A\.', current_tag):
    #
    #                 ol_cap_tag = self.soup.new_tag("ol", type="A")
    #                 tag.wrap(ol_cap_tag)
    #
    #                 art_id = tag.find_previous("h4").get("id")
    #                 tag["id"] = f'{art_id}A'
    #
    #
    #             else:
    #                 if re.match(r'^[B-Z]\.', tag.find_previous().text.strip()):
    #
    #                     cur_alpha =  re.search(r'^(?P<cap_id>[A-Z])\.',current_tag).group("cap_id")
    #                     ol_cap_tag.append(tag)
    #
    #                     art_id = tag.find_previous("h4").get("id")
    #                     tag["id"] = f'{art_id}{cur_alpha}'
    #                 else:
    #                     tag.name = "p"
    #
    #
    #
    #         # I.
    #         if re.match(r'^([A-Z]{0,3}\.\s*[a-zA-Z]+)', current_tag):
    #
    #             if re.match(r'^([I,V,X]{0,3}\.)', current_tag):
    #
    #                 ol_rom = tag
    #                 if re.search(r'^(I\.)', current_tag):
    #                     ol_tag1 = self.soup.new_tag("ol", type="I")
    #                     tag.wrap(ol_tag1)
    #
    #                 else:
    #                     ol_tag1.append(tag)
    #
    #                 tag_id = re.search(r'^(?P<id>[A-Z]{0,3})', current_tag).group('id')
    #                 prev_header_id = tag.find_previous("h3").get("id")
    #                 tag["id"] = f"{prev_header_id}ol1{tag_id}"
    #
    #             else:
    #                 if re.search(r'^(A\.)', current_tag):
    #                     ol_tag1 = self.soup.new_tag("ol", type="A")
    #                     tag.wrap(ol_tag1)
    #
    #                 else:
    #                     ol_tag1.append(tag)
    #
    #                 tag_id = re.search(r'^(?P<id>[A-Z]{0,3})', current_tag).group('id')
    #                 if tag.find_previous("h4"):
    #                     prev_header_id = tag.find_previous("h4").get("id")
    #                     tag["id"] = f"{prev_header_id}ol1{tag_id}"
    #
    #         # # (1)
    #         if re.match(Num_bracket_pattern, current_tag):
    #             ol_num = tag
    #             if re.search(r'^(\(1\))', current_tag):
    #                 if re.match(r'^([A-Z]{0,3}\.)', tag.find_previous().text.strip()):
    #
    #                     tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
    #                     ol_tag = self.soup.new_tag("ol")
    #                     tag.wrap(ol_tag)
    #                     tag.find_previous("li").append(ol_tag)
    #                     if ol_rom:
    #                         prev_id = ol_rom.get("id")
    #                     else:
    #                         prev_id = tag.find_previous("li").get("id")
    #
    #                     tag["id"] = f'{prev_id}{tag_id}'
    #
    #                 else:
    #                     ol_tag = self.soup.new_tag("ol")
    #                     tag.wrap(ol_tag)
    #
    #                     tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
    #
    #                     if tag.find_previous("h4"):
    #                         if re.match(r'Section\s*[A-Z]+\.', tag.find_previous("h4").text.strip()):
    #                             prev_header_id = tag.find_previous("h4").get("id")
    #                         elif re.match(r'^(Article|ARTICLE)\s*[I,V,X]*', tag.find_previous("h4").text.strip()):
    #                             prev_header_id = tag.find_previous("h4").get("id")
    #                         else:
    #                             prev_header_id = tag.find_previous("h3").get("id")
    #                     else:
    #                         prev_header_id = tag.find_previous("h3").get("id")
    #
    #                     tag_id1 = f"{prev_header_id}ol1{tag_id}"
    #                     tag["id"] = f"{prev_header_id}ol1{tag_id}"
    #
    #             else:
    #
    #
    #                 if re.search(r'History|HISTORY:', tag.find_next("p").text.strip()):
    #                     # print(tag)
    #                     ol_rom = None
    #
    #                 ol_tag.append(tag)
    #
    #                 tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
    #                 if ol_rom:
    #                     prev_header_id = ol_rom.get("id")
    #                     tag["id"] = f"{prev_header_id}{tag_id}"
    #
    #                 else:
    #                     if tag.find_previous("h4"):
    #                         if re.match(r'Section\s*[A-Z]+\.', tag.find_previous("h4").text.strip()):
    #                             prev_header_id = tag.find_previous("h4").get("id")
    #                         elif re.match(r'^(Article|ARTICLE)\s*[I,V,X]*', tag.find_previous("h4").text.strip()):
    #                             prev_header_id = tag.find_previous("h4").get("id")
    #                         else:
    #                             prev_header_id = tag.find_previous("h3").get("id")
    #                     else:
    #                         prev_header_id = tag.find_previous("h3").get("id")
    #
    #
    #
    #                     # prev_header_id = tag.find_previous("h3").get("id")
    #                     tag["id"] = f"{prev_header_id}ol1{tag_id}"
    #
    #         # (a)
    #         if re.match(alpha_pattern, current_tag):
    #
    #             ol_alpha = tag
    #             if re.match(r'^\(a\)', tag.text.strip()):
    #
    #
    #                 ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #                 tag.wrap(ol_tag2)
    #                 if re.match(alpha_pattern, tag.find_previous("li").text.strip()):
    #
    #                     tag.find_previous("li").append(ol_tag2)
    #                     tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
    #                     tag["id"] = f"{alpha_id}{tag_id}"
    #
    #
    #
    #                 else:
    #
    #                     ol_num.append(ol_tag2)
    #                     tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
    #
    #                     prev_header_id = ol_num.get("id")
    #                     alpha_id = f"{prev_header_id}{tag_id}"
    #
    #                     tag["id"] = f"{prev_header_id}{tag_id}"
    #             else:
    #
    #                 ol_tag2.append(tag)
    #                 tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
    #                 prev_header_id = ol_num.get("id")
    #                 alpha_id = f"{prev_header_id}{tag_id}"
    #                 tag["id"] = f"{prev_header_id}{tag_id}"
    #
    #         # # (4)(a)
    #         if re.match(numAlpha_pattern, current_tag):
    #             ol_inr_apha = tag
    #             prev_header = tag.find_previous("h3")
    #             prev_header_id = prev_header.get("id")
    #
    #             tag_id1 = re.search(r'^\((?P<id1>\d+)\)\s*\((\D+)\)', current_tag).group("id1")
    #             tag_id2 = re.search(r'^\((\d+)\)\s*\((?P<id2>[a-z]+)\)', current_tag).group("id2")
    #
    #             ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #             li_tag = self.soup.new_tag("li")
    #
    #             # li_tag.append(current_tag)
    #
    #             tag_text = re.sub(numAlpha_pattern, '', tag.text.strip())
    #             li_tag.append(tag_text)
    #
    #             li_tag["id"] = f"{prev_header_id}ol1{tag_id1}{tag_id2}"
    #
    #             ol_tag2.append(li_tag)
    #             tag.contents = []
    #             tag.append(ol_tag2)
    #
    #             # (4)(a)1.
    #             if re.match(r'\(\d+\)\s*\(\D\)\s*\d\.', current_tag):
    #                 ol_tag4 = self.soup.new_tag("ol")
    #                 inner_li_tag = self.soup.new_tag("li")
    #
    #                 tag_text = re.sub(r'\(\d+\)\s*\(\D\)\s*\d\.', '', current_tag)
    #                 inner_li_tag.append(tag_text)
    #
    #                 # print(tag)
    #
    #                 # inner_li_tag.append(tag.text.strip())
    #
    #                 tag_id1 = re.search(r'^(\(\d+\)\s*\((?P<id1>\D)\)\s*\d\.)', current_tag).group("id1")
    #                 tag_id2 = re.search(r'\(\d+\)\s*\(\D\)\s*(?P<id2>\d)\.', current_tag).group("id2")
    #
    #                 prev_id = ol_inr_apha.get("id")
    #                 inner_li_tag["id"] = f"{prev_id}{tag_id1}{tag_id2}"
    #                 prev_header_id = f"{prev_id}{tag_id1}"
    #                 main_olcount = 2
    #
    #                 ol_tag4.append(inner_li_tag)
    #                 tag.insert(1, ol_tag4)
    #                 ol_tag4.find_previous().string.replace_with(ol_tag4)
    #
    #         # a
    #         if re.match(r'[a-z]([a-z])*\.', current_tag):
    #
    #             ol_inr_apha = tag
    #
    #             tag_id = re.search(r'^(?P<id>[a-z]([a-z])*)\.', current_tag).group('id')
    #
    #             if re.match(r'a\.', current_tag):
    #
    #                 ol_tag3 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #                 tag.wrap(ol_tag3)
    #                 if re.match(num_pattern, tag.find_previous("li").text.strip()):
    #                     ol_tag5.append(ol_tag3)
    #                 else:
    #                     ol_tag.append(ol_tag3)
    #
    #                 tag.find_previous("li").append(ol_tag3)
    #
    #                 # print(tag)
    #
    #                 tag["id"] = f"{current_id}{tag_id}"
    #
    #                 prev_id = tag.find_previous("li").get("id")
    #
    #                 tag["id"] = f"{prev_id}{tag_id}"
    #
    #
    #             else:
    #                 if re.match(r'i\.', current_tag) and re.match(r'ii\.', tag.find_next_sibling().text.strip()):
    #                     rom_ol_tag = self.soup.new_tag("ol", type="i", **{"class": "roman"})
    #                     tag.wrap(rom_ol_tag)
    #                     ol_tag.append(rom_ol_tag)
    #                     tag.find_previous("li").append(rom_ol_tag)
    #
    #                 elif re.match(r'[a-z]\.', current_tag):
    #                     # print(current_tag)
    #                     ol_tag3.append(tag)
    #                     pre_id = ol_num_id.get("id")
    #                     # prev_alpha_id = tag.find_previous("li").get("id")
    #                     tag["id"] = f"{pre_id}{tag_id}"
    #
    #
    #                 else:
    #                     rom_ol_tag.append(tag)
    #
    #             if tag.span:
    #                 tag.span.string = ""
    #
    #         # (a) 1.
    #         if re.match(alphanum_pattern, current_tag):
    #             ol_tag5 = self.soup.new_tag("ol")
    #             li_tag = self.soup.new_tag("li")
    #
    #             tag_id1 = re.search(r'^\((?P<id1>\D+)\)\s(\d)+', current_tag).group("id1")
    #             tag_id2 = re.search(r'^\(\D+\)\s(?P<id2>\d)+', current_tag).group("id2")
    #
    #             tag_text = re.sub(r'^\(\D+\)\s(\d)\.', '', current_tag)
    #             li_tag.append(tag_text)
    #
    #             # li_tag.append(current_tag.strip())
    #
    #             ol_tag5.append(li_tag)
    #
    #             # prev_id = ol_inr_apha.get("id")
    #             prev_id = ol_alpha.get("id")
    #             # prev_id = li_tag.find_previous("li").get("id")
    #             li_tag["id"] = f"{prev_id}{tag_id2}"
    #             prev_header_id = f"{prev_id}{tag_id1}"
    #             main_olcount = 2
    #
    #             tag.contents = []
    #             tag.append(ol_tag5)
    #
    #             # 2.a.
    #         if re.match(r'(\d+\.(\s*[a-z]\.))', current_tag):
    #             ol_tag3 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #             inner_a_tag = self.soup.new_tag("li")
    #
    #             tag_text = re.sub(r'(\d+\.(\s*(?P<prev>[a-z])\.))', '', current_tag)
    #             inner_a_tag.append(tag_text)
    #
    #             prev = tag.find_previous("li").get("id")
    #             curr = re.search(r'(\d+\.(\s*(?P<prev>[a-z])\.))', current_tag).group("prev")
    #             inner_a_tag["id"] = f'{prev}{curr}'
    #
    #             prev_id = ol_alpha.get("id")
    #             cur_id = re.search(r'(\d+\.(\s*[a-z]\.))', current_tag).group()
    #             cur_id = re.sub(r'[\s\.]', '', cur_id)
    #
    #             # inner_a_tag["id"] = f'{prev_id}{cur_id}'
    #             # print(inner_a_tag)
    #             tag.clear()
    #
    #             ol_tag3.append(inner_a_tag)
    #             tag.insert(1, ol_tag3)
    #
    #
    #
    #         # 1. and previous (1)(a)
    #         if re.match(num_pattern, current_tag):
    #             ol_num_id = tag
    #             if re.match(r'^1\.', current_tag):
    #
    #                 ol_tag5 = self.soup.new_tag("ol")
    #                 tag.wrap(ol_tag5)
    #
    #                 if tag.find_previous("h4"):
    #
    #                     if not re.match(r'^(ARTICLE)\s*[I,V,X]*',tag.find_previous("h4").text.strip()) and not re.match(r'Section\s*[A-Z]+\.',tag.find_previous("h4").text.strip()) :
    #                             tag.find_previous("li").append(ol_tag5)
    #
    #                             main_olcount = 1
    #                             prev_id = tag.find_previous("li").get("id")
    #                             tag["id"] = f"{prev_id}{main_olcount}"
    #
    #                             main_olcount += 1
    #
    #                             if tag.find_previous("li"):
    #                                 prev_header_id = tag.find_previous("li").get("id")
    #                     else:
    #
    #                             ar_id = tag.find_previous("h4").get("id")
    #                             main_olcount = 1
    #                             tag["id"] = f"{ar_id}{main_olcount}"
    #                             main_olcount += 1
    #                 else:
    #                     pre_id = tag.find_previous("li").get("id")
    #                     tag.find_previous("li").append(ol_tag5)
    #                     main_olcount = 1
    #                     tag["id"] = f"{pre_id}{main_olcount}"
    #                     main_olcount += 1
    #
    #             elif tag.find_previous("li"):
    #
    #                 ol_tag5.append(tag)
    #
    #                 if tag.find_previous("h4"):
    #
    #                     if not re.match(r'^(ARTICLE)\s*[I,V,X]*', tag.find_previous("h4").text.strip()) and not re.match(
    #                                 r'Section\s*[A-Z]+\.', tag.find_previous("h4").text.strip()):
    #                         if prev_id:
    #                             current_id = f"{prev_id}{main_olcount}"
    #
    #                             tag["id"] = f"{prev_id}{main_olcount}"
    #                             main_olcount += 1
    #                     else:
    #                         current_id = f"{ar_id}{main_olcount}"
    #
    #                         tag["id"] = f"{ar_id}{main_olcount}"
    #                         main_olcount += 1
    #
    #                 else:
    #                     tag["id"] = f"{pre_id}{main_olcount}"
    #                     main_olcount += 1
    #
    #
    #     print("ol tag is created")
    #

    # def wrap_with_ordered_tag_2(self):
    #
    #     # pattern = re.compile(r'^(\d+)|^(\(\d+\)|^\(\s*[a-z][a-z]?\s*\))|^([a-z]\.)|^([A-Z]{0,3}\.)|^([a-z]{0,3}\.)')
    #
    #     pattern = re.compile(
    #         r'^(\d+\.(\s*[a-z]\.)*)|^(\(\d+\)|^\(\s*[a-z][a-z]?\s*\))|^([a-z]\.)|^([A-Z]{0,3}\.)|^([a-z]{0,3}\.)')
    #     Num_bracket_pattern = re.compile(r'^\(\d+\)')
    #     alpha_pattern = re.compile(r'^\(\s*[a-z][a-z]?\s*\)')
    #     # alp_pattern = re.compile(r'\(\D+\)')
    #     num_pattern = re.compile(r'^\d+\.')
    #     # num_pattern1 = re.compile(r'^1\.')
    #     numAlpha_pattern = re.compile(r'^\(\d+\)\s\(\D\)')
    #     alphanum_pattern = re.compile(r'^\(\D+\)\s(\d)+')
    #
    #     ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #     # ol_tag = self.soup.new_tag("ol")
    #     ol_tag3 = self.soup.new_tag("ol")
    #     ol_tag1 = self.soup.new_tag("ol")
    #     ol_tag4 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #     ol_tag5 = self.soup.new_tag("ol")
    #     ol_tag6 = self.soup.new_tag("ol")
    #     rom_ol_tag = self.soup.new_tag("ol", type="i", **{"class": "roman"})
    #
    #     ol_num = None
    #     ol_alpha = None
    #     ol_inr_num = None
    #     ol_inr_apha = None
    #     ol_inr_alpha = None
    #     ol_rom = None
    #
    #     for tag in self.soup.findAll("p", class_=self.class_regex["ol"]):
    #         current_tag = tag.text.strip()
    #
    #         if re.match(pattern, tag.text.strip()):
    #             tag.name = "li"
    #
    #         elif re.match(r'^(Article\s*[I,V,X]*\.)', tag.text.strip()):
    #             tag.name = "h4"
    #             prev_id = tag.find_previous("h3").get("id")
    #             article_id = re.search(r'^(Article\s*(?P<ar_id>[I,V,X]*))', tag.text.strip()).group("ar_id")
    #             tag["id"] = f'{prev_id}a{article_id}'
    #
    #         # I.
    #         if re.match(r'^([A-Z]{0,3}\.\s*[a-zA-Z]+)', current_tag):
    #
    #             if re.match(r'^([I,V,X]{0,3}\.)', current_tag):
    #
    #                 ol_rom = tag
    #                 if re.search(r'^(I\.)', current_tag):
    #                     ol_tag1 = self.soup.new_tag("ol", type="I")
    #                     tag.wrap(ol_tag1)
    #
    #                 else:
    #                     ol_tag1.append(tag)
    #
    #                 tag_id = re.search(r'^(?P<id>[A-Z]{0,3})', current_tag).group('id')
    #                 prev_header_id = tag.find_previous("h3").get("id")
    #                 tag["id"] = f"{prev_header_id}ol1{tag_id}"
    #
    #             else:
    #                 if re.search(r'^(A\.)', current_tag):
    #                     ol_tag1 = self.soup.new_tag("ol", type="A")
    #                     tag.wrap(ol_tag1)
    #
    #                 else:
    #                     ol_tag1.append(tag)
    #
    #                 tag_id = re.search(r'^(?P<id>[A-Z]{0,3})', current_tag).group('id')
    #                 prev_header_id = tag.find_previous("h4").get("id")
    #                 tag["id"] = f"{prev_header_id}ol1{tag_id}"
    #
    #         # # (1)
    #         if re.match(Num_bracket_pattern, current_tag):
    #             ol_num = tag
    #             if re.search(r'^(\(1\))', current_tag):
    #                 if re.match(r'^([A-Z]{0,3}\.)', tag.find_previous().text.strip()):
    #
    #                     tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
    #                     ol_tag = self.soup.new_tag("ol")
    #                     tag.wrap(ol_tag)
    #                     tag.find_previous("li").append(ol_tag)
    #                     if ol_rom:
    #                         prev_id = ol_rom.get("id")
    #                     else:
    #                         prev_id = tag.find_previous("li").get("id")
    #
    #                     tag["id"] = f'{prev_id}{tag_id}'
    #
    #                 else:
    #                     ol_tag = self.soup.new_tag("ol")
    #                     tag.wrap(ol_tag)
    #
    #                     tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
    #
    #                     prev_header_id = tag.find_previous("h3").get("id")
    #                     tag_id1 = f"{prev_header_id}ol1{tag_id}"
    #                     tag["id"] = f"{prev_header_id}ol1{tag_id}"
    #
    #             else:
    #                 # if re.search('Kentucky Communications Network Authority.', tag.text.strip()):
    #                 #     print(tag.find_next("p").text)
    #
    #                 if re.search(r'History|HISTORY:', tag.find_next("p").text.strip()):
    #                     # print(tag)
    #                     ol_rom = None
    #
    #                 ol_tag.append(tag)
    #
    #                 tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
    #                 if ol_rom:
    #                     prev_header_id = ol_rom.get("id")
    #                     tag["id"] = f"{prev_header_id}{tag_id}"
    #
    #                 else:
    #                     prev_header_id = tag.find_previous("h3").get("id")
    #                     tag["id"] = f"{prev_header_id}ol1{tag_id}"
    #
    #         # (a)
    #         if re.match(alpha_pattern, current_tag):
    #
    #             ol_alpha = tag
    #             if re.match(r'^\(a\)', tag.text.strip()):
    #                 # print(current_tag)
    #                 ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #                 tag.wrap(ol_tag2)
    #                 # tag.find_previous("li").append(ol_tag2)
    #                 ol_num.append(ol_tag2)
    #             else:
    #
    #                 # print(current_tag)
    #                 ol_tag2.append(tag)
    #
    #                 # print(current_tag)
    #
    #             tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
    #
    #             prev_header_id = ol_num.get("id")
    #             alpha_id = f"{prev_header_id}{tag_id}"
    #
    #             tag["id"] = f"{prev_header_id}{tag_id}"
    #
    #         # # (4)(a)
    #         if re.match(numAlpha_pattern, current_tag):
    #             ol_inr_apha = tag
    #             prev_header = tag.find_previous("h3")
    #             prev_header_id = prev_header.get("id")
    #
    #             tag_id1 = re.search(r'^\((?P<id1>\d+)\)\s*\((\D+)\)', current_tag).group("id1")
    #             tag_id2 = re.search(r'^\((\d+)\)\s*\((?P<id2>[a-z]+)\)', current_tag).group("id2")
    #
    #             ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #             li_tag = self.soup.new_tag("li")
    #
    #             # li_tag.append(current_tag)
    #
    #             tag_text = re.sub(numAlpha_pattern, '', tag.text.strip())
    #             li_tag.append(tag_text)
    #
    #             li_tag["id"] = f"{prev_header_id}ol1{tag_id1}{tag_id2}"
    #
    #             ol_tag2.append(li_tag)
    #             tag.contents = []
    #             tag.append(ol_tag2)
    #
    #             # (4)(a)1.
    #             if re.match(r'\(\d+\)\s*\(\D\)\s*\d\.', current_tag):
    #                 ol_tag4 = self.soup.new_tag("ol")
    #                 inner_li_tag = self.soup.new_tag("li")
    #
    #                 tag_text = re.sub(r'\(\d+\)\s*\(\D\)\s*\d\.', '', current_tag)
    #                 inner_li_tag.append(tag_text)
    #
    #                 # print(tag)
    #
    #                 # inner_li_tag.append(tag.text.strip())
    #
    #                 tag_id1 = re.search(r'^(\(\d+\)\s*\((?P<id1>\D)\)\s*\d\.)', current_tag).group("id1")
    #                 tag_id2 = re.search(r'\(\d+\)\s*\(\D\)\s*(?P<id2>\d)\.', current_tag).group("id2")
    #
    #                 prev_id = ol_inr_apha.get("id")
    #                 inner_li_tag["id"] = f"{prev_id}{tag_id1}{tag_id2}"
    #                 prev_header_id = f"{prev_id}{tag_id1}"
    #                 main_olcount = 2
    #
    #                 ol_tag4.append(inner_li_tag)
    #                 tag.insert(1, ol_tag4)
    #                 ol_tag4.find_previous().string.replace_with(ol_tag4)
    #
    #         # 2.a.
    #         if re.match(r'(\d+\.(\s*[a-z]\.))', current_tag):
    #             ol_tag3 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #             inner_a_tag = self.soup.new_tag("li")
    #
    #             tag_text = re.sub(r'(\d+\.(\s*[a-z]\.))', '', current_tag)
    #             inner_a_tag.append(tag_text)
    #
    #             prev_id = ol_alpha.get("id")
    #             cur_id = re.search(r'(\d+\.(\s*[a-z]\.))', current_tag).group()
    #             cur_id = re.sub(r'[\s\.]', '', cur_id)
    #
    #             inner_a_tag["id"] = f'{prev_id}{cur_id}'
    #             # print(inner_a_tag)
    #             tag.clear()
    #
    #             ol_tag3.append(inner_a_tag)
    #             tag.insert(1, ol_tag3)
    #
    #         # a
    #         if re.match(r'[a-z]([a-z])*\.', current_tag):
    #
    #             ol_inr_apha = tag
    #
    #             tag_id = re.search(r'^(?P<id>[a-z]([a-z])*)\.', current_tag).group('id')
    #
    #             if re.match(r'a\.', current_tag):
    #                 ol_tag3 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
    #                 tag.wrap(ol_tag3)
    #                 ol_tag.append(ol_tag3)
    #                 tag.find_previous("li").append(ol_tag3)
    #
    #                 # tag["id"] = f"{current_id}{tag_id}"
    #
    #                 prev_id = tag.find_previous("li").get("id")
    #
    #                 tag["id"] = f"{prev_id}{tag_id}"
    #                 # print(tag)
    #
    #             else:
    #                 if re.match(r'i\.', current_tag) and re.match(r'ii\.', tag.find_next_sibling().text.strip()):
    #                     rom_ol_tag = self.soup.new_tag("ol", type="i", **{"class": "roman"})
    #                     tag.wrap(rom_ol_tag)
    #                     ol_tag.append(rom_ol_tag)
    #                     tag.find_previous("li").append(rom_ol_tag)
    #
    #                 elif re.match(r'[a-z]\.', current_tag):
    #                     # print(current_tag)
    #                     ol_tag3.append(tag)
    #                     pre_id = ol_num_id.get("id")
    #                     # prev_alpha_id = tag.find_previous("li").get("id")
    #                     tag["id"] = f"{pre_id}{tag_id}"
    #
    #
    #                 else:
    #                     rom_ol_tag.append(tag)
    #
    #             if tag.span:
    #                 tag.span.string = ""
    #
    #         # (a) 1.
    #         if re.match(alphanum_pattern, current_tag):
    #             ol_tag5 = self.soup.new_tag("ol")
    #             li_tag = self.soup.new_tag("li")
    #
    #             tag_id1 = re.search(r'^\((?P<id1>\D+)\)\s(\d)+', current_tag).group("id1")
    #             tag_id2 = re.search(r'^\(\D+\)\s(?P<id2>\d)+', current_tag).group("id2")
    #
    #             tag_text = re.sub(r'^\(\D+\)\s(\d)\.', '', current_tag)
    #             li_tag.append(tag_text)
    #
    #             # li_tag.append(current_tag.strip())
    #
    #             ol_tag5.append(li_tag)
    #
    #             # prev_id = ol_inr_apha.get("id")
    #             prev_id = ol_alpha.get("id")
    #             # prev_id = li_tag.find_previous("li").get("id")
    #             li_tag["id"] = f"{prev_id}{tag_id2}"
    #             prev_header_id = f"{prev_id}{tag_id1}"
    #             main_olcount = 2
    #
    #             tag.contents = []
    #             tag.append(ol_tag5)
    #
    #         # 1. and previous (1)(a)
    #         if re.match(num_pattern, current_tag):
    #             ol_num_id = tag
    #             if re.match(r'^1\.', current_tag):
    #
    #                 ol_tag5 = self.soup.new_tag("ol")
    #                 tag.wrap(ol_tag5)
    #                 # ol_tag2.append(ol_tag5)
    #                 tag.find_previous("li").append(ol_tag5)
    #
    #                 main_olcount = 1
    #                 prev_id = tag.find_previous("li").get("id")
    #                 tag["id"] = f"{prev_id}{main_olcount}"
    #
    #                 main_olcount += 1
    #
    #                 # print(tag.find_previous("li").get("id"))
    #                 # main_olcount = 1
    #                 if tag.find_previous("li"):
    #                     prev_header_id = tag.find_previous("li").get("id")
    #
    #             elif tag.find_previous("li"):
    #
    #                 # print()
    #
    #                 ol_tag5.append(tag)
    #
    #                 # prev_header_id = ol_alpha.get("id")
    #                 current_id = f"{prev_header_id}{main_olcount}"
    #                 tag["id"] = f"{prev_header_id}{main_olcount}"
    #                 main_olcount += 1
    #
    #
    #
    #     print("ol tag is created")

    def wrap_with_ordered_tag_3(self):

        # pattern = re.compile(r'^(\d+)|^(\(\d+\)|^\(\s*[a-z][a-z]?\s*\))|^([a-z]\.)|^([A-Z]{0,3}\.)|^([a-z]{0,3}\.)')

        pattern = re.compile(
            r'^(\d+\.(\s*[a-z]\.)*)|^(\(\d+\)|^\(\s*[a-z][a-z]?\s*\))|^([a-z]\.)|^([A-Z]{0,3}\.\s*“?[a-zA-Z]+)|^([a-z]{0,3}\.)|^[A-Z]\.\s*[a-zA-Z]+')
        Num_bracket_pattern = re.compile(r'^\(\d+\)')
        alpha_pattern = re.compile(r'^\(\s*[a-z][a-z]?\s*\)')
        # alp_pattern = re.compile(r'\(\D+\)')
        num_pattern = re.compile(r'^\d+\.')
        # num_pattern1 = re.compile(r'^1\.')
        numAlpha_pattern = re.compile(r'^\(\d+\)\s\(\D\)')
        alphanum_pattern = re.compile(r'^\(\D+\)\s(\d)+')

        ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
        # ol_tag = self.soup.new_tag("ol")
        ol_tag3 = self.soup.new_tag("ol")
        ol_tag1 = self.soup.new_tag("ol")
        ol_tag4 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
        ol_tag5 = self.soup.new_tag("ol")
        ol_tag6 = self.soup.new_tag("ol")
        rom_ol_tag = self.soup.new_tag("ol", type="i", **{"class": "roman"})
        ol_cap_tag = self.soup.new_tag("ol", type="A")

        ol_num = None
        ol_alpha = None
        ol_inr_num = None
        ol_inr_apha = None
        ol_inr_alpha = None
        ol_rom = None
        prev_id = 0
        current_id = 0
        pre_id = 0
        sec_id_list = []
        ol_count = 1
        ol_num_id = 0
        curr_id = 0

        for tag in self.soup.findAll("p", class_=self.class_regex["ol"]):
            current_tag = tag.text.strip()

            if re.match(pattern, tag.text.strip()):
                tag.name = "li"

            elif re.match(r'^(Article)\s*[I,V,X]*\.', tag.text.strip()):
                tag.name = "h4"
                prev_id = tag.find_previous("h3").get("id")
                article_id = re.search(r'^(Article)\s*(?P<ar_id>[I,V,X]*)', tag.text.strip()).group("ar_id")
                tag["id"] = f'{prev_id}a{article_id}'
                tag["class"] = "article"

            elif re.match(r'^(ARTICLE)\s*[I,V,X]*', tag.text.strip()):
                tag.name = "h4"
                prev_id = tag.find_previous("h3").get("id")
                article_id = re.search(r'^(ARTICLE)\s*(?P<ar_id>[I,V,X]*)', tag.text.strip()).group("ar_id")
                tag["id"] = f'{prev_id}a{article_id}'
                tag["class"] = "article"

            elif re.match(r'Section\s*[A-Z]+\.', tag.text.strip()):
                tag.name = "h4"
                prev_id = tag.find_previous("h4", class_="article").get("id")
                article_id = re.search(r'^(Section)\s*(?P<ar_id>[A-Z]+)\.', tag.text.strip()).group("ar_id")
                tag["id"] = f'{prev_id}s{article_id}'
                tag["class"] = "section"

            # A
            # if re.match(r'^[A-Z]\.', current_tag):
            #
            #     if re.match(r'^A\.', current_tag):
            #
            #         ol_cap_tag = self.soup.new_tag("ol", type="A")
            #         tag.wrap(ol_cap_tag)
            #
            #         art_id = tag.find_previous("h4").get("id")
            #         tag["id"] = f'{art_id}A'
            #
            #     else:
            #         if re.match(r'^[B-Z]\.', tag.find_previous().text.strip()) and tag.name == "li":
            #             cur_alpha =  re.search(r'^(?P<cap_id>[A-Z])\.',current_tag).group("cap_id")
            #             ol_cap_tag.append(tag)
            #
            #             if tag.find_previous("h4"):
            #
            #                 art_id = tag.find_previous("h4").get("id")
            #                 tag["id"] = f'{art_id}{cur_alpha}'
            #
            #         elif not re.match(r'^[I,V,X]', current_tag):
            #
            #             tag.name = "p"

            # I.
            if re.match(r'^([A-Z]{0,3}\.\s*“?[a-zA-Z]+)', current_tag):
                if re.match(r'^([I,V,X]{0,3}\.)', current_tag) and not re.match(r'^H.', tag.find_previous("li").text.strip()):

                    ol_rom = tag
                    if re.search(r'^(I\.)', current_tag):
                        ol_tag1 = self.soup.new_tag("ol", type="I")
                        tag.wrap(ol_tag1)
                    else:
                        ol_tag1.append(tag)

                    tag_id = re.search(r'^(?P<id>[A-Z]{0,3})', current_tag).group('id')
                    prev_header_id = tag.find_previous("h3").get("id")
                    tag["id"] = f"{prev_header_id}ol1{tag_id}"

                else:
                    if re.search(r'^(A\.)', current_tag):
                        ol_tag1 = self.soup.new_tag("ol", type="A")
                        tag.wrap(ol_tag1)
                        tag_id = re.search(r'^(?P<id>[A-Z]{0,3})', current_tag).group('id')
                        if tag.find_previous("h4"):
                            prev_header_id = tag.find_previous("h4").get("id")
                            tag["id"] = f"{prev_header_id}ol1{tag_id}"

                    else:
                        if re.match(r'^[B-Z]\.', tag.text.strip()) and tag.find_previous().name == "span":
                            ol_tag1.append(tag)

                            tag_id = re.search(r'^(?P<id>[A-Z]{0,3})', current_tag).group('id')
                            if tag.find_previous("h4"):
                                prev_header_id = tag.find_previous("h4").get("id")
                                tag["id"] = f"{prev_header_id}ol1{tag_id}"
                        else:
                            tag.name = "p"

            # # (1)
            if re.match(Num_bracket_pattern, current_tag):
                ol_num = tag

                if re.search(r'^(\(1\))', current_tag):

                    if re.match(r'^([A-Z]{0,3}\.)', tag.find_previous().text.strip()):
                        tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
                        ol_tag = self.soup.new_tag("ol")
                        tag.wrap(ol_tag)
                        tag.find_previous("li").append(ol_tag)
                        if ol_rom:
                            prev_id = ol_rom.get("id")
                        else:
                            prev_id = tag.find_previous("li").get("id")
                        tag["id"] = f'{prev_id}{tag_id}'


                    elif re.match(r'^\([a-z]\)', tag.find_previous().text.strip()):

                        pre_id = tag.find_previous("li").get("id")
                        ol_tag = self.soup.new_tag("ol")
                        tag.wrap(ol_tag)
                        tag.find_previous("li").append(ol_tag)
                        tag["id"] = f'{pre_id}1'

                    else:

                        if tag.find_previous("h3") in sec_id_list:
                            ol_count = 1

                        ol_tag = self.soup.new_tag("ol")
                        tag.wrap(ol_tag)

                        tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')

                        if tag.find_previous("h4"):
                            if re.match(r'Section\s*[A-Z]+\.', tag.find_previous("h4").text.strip()):
                                prev_header_id = tag.find_previous("h4").get("id")
                            elif re.match(r'^(Article|ARTICLE)\s*[I,V,X]*', tag.find_previous("h4").text.strip()):
                                if tag.find_previous("h3") == tag.find_previous("h4").find_previous("h3"):
                                    prev_header_id = tag.find_previous("h4").get("id")
                                else:
                                    prev_header_id = tag.find_previous("h3").get("id")
                            else:
                                prev_header_id = tag.find_previous("h3").get("id")

                        else:
                            # print(tag)
                            prev_header_id = tag.find_previous("h3").get("id")

                        tag_id1 = f"{prev_header_id}ol{ol_count}{tag_id}"

                        tag["id"] = f"{prev_header_id}ol{ol_count}{tag_id}"

                        sec_id_list.append(tag.find_previous("h3"))


                else:

                    if re.search(r'History|HISTORY:', tag.find_next("p").text.strip()):
                        # print(tag)
                        ol_rom = None

                    ol_tag.append(tag)

                    tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
                    if ol_rom:
                        prev_header_id = ol_rom.get("id")
                        tag["id"] = f"{prev_header_id}{tag_id}"

                    else:
                        if tag.find_previous("h4"):
                            if re.match(r'Section\s*[A-Z]+\.', tag.find_previous("h4").text.strip()):
                                prev_header_id = tag.find_previous("h4").get("id")
                            elif re.match(r'^(Article|ARTICLE)\s*[I,V,X]*', tag.find_previous("h4").text.strip()):

                                # prev_header_id = tag.find_previous("h4").get("id")

                                if tag.find_previous("h3") == tag.find_previous("h4").find_previous("h3"):
                                    # print(tag)
                                    prev_header_id = tag.find_previous("h4").get("id")
                                else:
                                    prev_header_id = tag.find_previous("h3").get("id")

                            else:

                                prev_header_id = tag.find_previous("h3").get("id")
                        else:

                            prev_header_id = tag.find_previous("h3").get("id")

                        # prev_header_id = tag.find_previous("h3").get("id")
                        tag["id"] = f"{prev_header_id}ol{ol_count}{tag_id}"


            # (a)
            if re.match(alpha_pattern, current_tag):
                ol_alpha = tag
                if tag.find_previous("h4"):
                    if re.search(r'ARTICLE',tag.find_previous("h4").text.strip()):
                        prev_header_id = tag.find_previous("h4").get("id")
                    else:
                        prev_header_id = ol_num.get("id")

                if re.match(r'^\(a\)', tag.text.strip()) :
                    curr_id = None
                    ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                    tag.wrap(ol_tag2)

                    if re.match(alpha_pattern, tag.find_previous("li").text.strip()) and tag.find_previous().name == "span":
                        tag.find_previous("li").append(ol_tag2)
                        prev_header_id = tag.find_previous("li").get("id")
                        tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
                        curr_id = f"{prev_header_id}{tag_id}"
                        tag["id"] = f"{prev_header_id}{tag_id}"

                    elif tag.find_previous("ol").find_previous().name == "span" and not re.match(r'ARTICLE',tag.find_previous("ol").find_previous().text.strip()):
                        ol_num.append(ol_tag2)
                        tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
                        prev_header_id = ol_num.get("id")
                        alpha_id = f"{prev_header_id}{tag_id}"
                        tag["id"] = f"{prev_header_id}{tag_id}"

                    else:
                        if not re.match(r'ARTICLE',tag.find_previous().find_previous().text.strip()):
                            tag.find_previous("li").append(ol_tag2)
                            tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
                            prev_header_id = tag.find_previous("li").get("id")
                            tag["id"] = f"{prev_header_id}{tag_id}"


                else:
                    ol_tag2.append(tag)
                    tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
                    if tag.find_previous("li").get("id"):
                        prev_header_id = re.sub(r'\D$', '', tag.find_previous("li").get("id"))
                        tag["id"] = f"{prev_header_id}{tag_id}"
                    else:
                        prev_header_id = tag.find_previous("h3").get("id")
                        tag["id"] = f"{prev_header_id}{tag_id}"

                    # if curr_id:
                    #     prev_header_id = re.sub(r'\D$', '', curr_id)
                    #     tag["id"] = f"{prev_header_id}{tag_id}"
                    #
                    # else:
                    #     tag["id"] = f"{prev_header_id}{tag_id}"
                    #
                    # # prev_header_id = ol_num.get("id")
                    # alpha_id = f"{prev_header_id}{tag_id}"

            # # (4)(a)
            if re.match(numAlpha_pattern, current_tag):
                ol_inr_apha = tag
                prev_header = tag.find_previous("h3")
                prev_header_id = prev_header.get("id")

                tag_id1 = re.search(r'^\((?P<id1>\d+)\)\s*\((\D+)\)', current_tag).group("id1")
                tag_id2 = re.search(r'^\((\d+)\)\s*\((?P<id2>[a-z]+)\)', current_tag).group("id2")

                ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                li_tag = self.soup.new_tag("li")

                # li_tag.append(current_tag)

                tag_text = re.sub(numAlpha_pattern, '', tag.text.strip())
                li_tag.append(tag_text)

                li_tag["id"] = f"{prev_header_id}ol1{tag_id1}{tag_id2}"

                ol_tag2.append(li_tag)
                tag.contents = []
                tag.append(ol_tag2)

                # (4)(a)1.
                if re.match(r'\(\d+\)\s*\(\D\)\s*\d\.', current_tag):
                    ol_tag4 = self.soup.new_tag("ol")
                    inner_li_tag = self.soup.new_tag("li")

                    tag_text = re.sub(r'\(\d+\)\s*\(\D\)\s*\d\.', '', current_tag)
                    inner_li_tag.append(tag_text)

                    # print(tag)

                    # inner_li_tag.append(tag.text.strip())

                    tag_id1 = re.search(r'^(\(\d+\)\s*\((?P<id1>\D)\)\s*\d\.)', current_tag).group("id1")
                    tag_id2 = re.search(r'\(\d+\)\s*\(\D\)\s*(?P<id2>\d)\.', current_tag).group("id2")

                    prev_id = ol_inr_apha.get("id")
                    inner_li_tag["id"] = f"{prev_id}{tag_id1}{tag_id2}"
                    prev_header_id = f"{prev_id}{tag_id1}"
                    main_olcount = 2

                    ol_tag4.append(inner_li_tag)
                    tag.insert(1, ol_tag4)
                    ol_tag4.find_previous().string.replace_with(ol_tag4)

            # a
            if re.match(r'[a-z]([a-z])*\.', current_tag):

                ol_inr_apha = tag

                tag_id = re.search(r'^(?P<id>[a-z]([a-z])*)\.', current_tag).group('id')

                if re.match(r'a\.', current_tag):

                    ol_tag3 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})

                    if re.search(r'ARTICLE',tag.find_previous().find_previous().text.strip()):
                        tag.wrap(ol_tag3)
                        prev_id = tag.find_previous("h4").get("id")
                        tag["id"] = f"{prev_id}{tag_id}"

                    elif re.match(num_pattern, tag.find_previous("li").text.strip()):
                        tag.wrap(ol_tag3)
                        ol_tag5.append(ol_tag3)
                        prev_id = tag.find_previous("li").get("id")
                        tag["id"] = f"{prev_id}{tag_id}"
                    else:
                        tag.wrap(ol_tag3)
                        ol_tag.append(ol_tag3)
                        prev_id = tag.find_previous("li").get("id")
                        tag["id"] = f"{prev_id}{tag_id}"

                    # if tag.find_previous("li"):
                    #     # tag.find_previous("li").append(ol_tag3)
                    #     prev_id = tag.find_previous("li").get("id")
                    #     innr_alpha_id = f"{prev_id}{tag_id}"
                    #     tag["id"] = f"{prev_id}{tag_id}"


                else:
                    if re.match(r'i\.', current_tag) and re.match(r'ii\.', tag.find_next_sibling().text.strip()):
                        # print(tag)
                        rom_ol_tag = self.soup.new_tag("ol", type="i", **{"class": "roman"})
                        tag.wrap(rom_ol_tag)
                        # ol_tag.append(rom_ol_tag)
                        tag.find_previous("li").append(rom_ol_tag)


                        pre_rom_id = tag.find_previous("li").get("id")
                        tag["id"] = f'{pre_rom_id}i'


                    elif re.match(r'[a-z]\.', current_tag):

                        ol_tag3.append(tag)
                        # pre_id = ol_num_id.get("id")
                        #print(tag.find_previous("li"))

                        # print(tag.find_previous("li").get("id"))
                        pre_id = re.sub(r'\D+$','',tag.find_previous("li").get("id"))
                        tag["id"] = f"{pre_id}{tag_id}"


                    else:
                        rom_ol_tag.append(tag)
                        if tag.find_previous("li"):
                            if tag.find_previous("li").get("id"):
                                pre_rom_id = re.sub(r'\D$','',tag.find_previous("li").get("id"))
                                cur_rom_id = re.search(r'^[^\s\.]+',current_tag).group()
                                tag["id"] = f'{pre_rom_id}{cur_rom_id}'

                if tag.span:
                    tag.span.string = ""

            # (a) 1.
            if re.match(alphanum_pattern, current_tag):
                ol_tag5 = self.soup.new_tag("ol")
                li_tag = self.soup.new_tag("li")

                tag_id1 = re.search(r'^\((?P<id1>\D+)\)\s(\d)+', current_tag).group("id1")
                tag_id2 = re.search(r'^\(\D+\)\s(?P<id2>\d)+', current_tag).group("id2")

                tag_text = re.sub(r'^\(\D+\)\s(\d)\.', '', current_tag)
                li_tag.append(tag_text)

                # li_tag.append(current_tag.strip())

                ol_tag5.append(li_tag)

                # prev_id = ol_inr_apha.get("id")
                prev_id = ol_alpha.get("id")
                # prev_id = li_tag.find_previous("li").get("id")
                li_tag["id"] = f"{prev_id}{tag_id2}"
                prev_header_id = f"{prev_id}{tag_id1}"
                main_olcount = 2

                tag.contents = []
                tag.append(ol_tag5)

                # 2.a.
            if re.match(r'(\d+\.(\s*[a-z]\.))', current_tag):

                if re.match(r'(\d+\.(\s*i\.))',current_tag):
                    ol_tag3 = self.soup.new_tag("ol", type="i", **{"class": "roman"})
                    inner_a_tag = self.soup.new_tag("li")
                    tag_text = re.sub(r'(\d+\.(\s*(?P<prev>[a-z])\.))', '', current_tag)
                    inner_a_tag.append(tag_text)
                    prev = tag.find_previous("li").get("id")

                    if prev:
                        prev = re.sub(r'\d$','',prev)
                        curr = re.search(r'(?P<prev>\d+\.\s*[a-z]\.)', current_tag).group("prev")
                        curr = re.sub(r'[\.\s]','',curr)
                        inner_a_tag["id"] = f'{prev}{curr}'

                    tag.clear()
                    ol_tag3.append(inner_a_tag)
                    tag.insert(1, ol_tag3)


                else:
                    ol_tag3 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                    inner_a_tag = self.soup.new_tag("li")
                    tag_text = re.sub(r'(\d+\.(\s*(?P<prev>[a-z])\.))', '', current_tag)
                    inner_a_tag.append(tag_text)
                    prev = tag.find_previous("li").get("id")

                    if prev:
                        prev = re.sub(r'\d$','',prev)
                        curr = re.search(r'(?P<prev>\d+\.\s*[a-z]\.)', current_tag).group("prev")
                        curr = re.sub(r'[\.\s]','',curr)
                        inner_a_tag["id"] = f'{prev}{curr}'

                    tag.clear()
                    ol_tag3.append(inner_a_tag)
                    tag.insert(1, ol_tag3)

            # 1. and previous (1)(a)
            if re.match(num_pattern, current_tag):

                ol_num_id = tag
                if re.match(r'^1\.', current_tag):

                    ol_tag5 = self.soup.new_tag("ol")
                    tag.wrap(ol_tag5)

                    if tag.find_previous("h4"):
                        if not re.match(r'^(ARTICLE)\s*[I,V,X]*',
                                        tag.find_previous("h4").text.strip()) and not re.match(r'Section\s*[A-Z]+\.',
                                                                                               tag.find_previous(
                                                                                                       "h4").text.strip()):
                            tag.find_previous("li").append(ol_tag5)
                            main_olcount = 1
                            prev_id = tag.find_previous("li").get("id")
                            tag["id"] = f"{prev_id}{main_olcount}"
                            main_olcount += 1

                            if tag.find_previous("li"):
                                prev_header_id = tag.find_previous("li").get("id")
                        else:
                            tag.find_previous("li").append(ol_tag5)
                            ar_id = tag.find_previous("h4").get("id")
                            main_olcount = 1
                            tag["id"] = f"{ar_id}{main_olcount}"
                            main_olcount += 1
                    else:
                        pre_id = tag.find_previous("li").get("id")
                        tag.find_previous("li").append(ol_tag5)
                        main_olcount = 1
                        tag["id"] = f"{pre_id}{main_olcount}"
                        main_olcount += 1

                elif tag.find_previous("li"):

                    ol_tag5.append(tag)

                    if tag.find_previous("h4"):

                        if not re.match(r'^(ARTICLE)\s*[I,V,X]*',
                                        tag.find_previous("h4").text.strip()) and not re.match(
                                r'Section\s*[A-Z]+\.', tag.find_previous("h4").text.strip()):
                            if prev_id:
                                current_id = f"{prev_id}{main_olcount}"

                                tag["id"] = f"{prev_id}{main_olcount}"
                                main_olcount += 1
                        else:

                            current_id = f"{ar_id}{main_olcount}"

                            tag["id"] = f"{ar_id}{main_olcount}"
                            main_olcount += 1

                    else:
                        if tag.find_previous("li"):
                            if tag.find_previous("li").get("id"):
                                cur_id = re.sub(r'\d+$', '', tag.find_previous("li").get("id"))
                                tag["id"] = f"{cur_id}{main_olcount}"
                                main_olcount += 1

        print("ol tag is created")


    def wrap_with_ordered_tag_4(self):

        # pattern = re.compile(r'^(\d+)|^(\(\d+\)|^\(\s*[a-z][a-z]?\s*\))|^([a-z]\.)|^([A-Z]{0,3}\.)|^([a-z]{0,3}\.)')

        pattern = re.compile(
            r'^(\d+\.(\s*[a-z]\.)*)|^(\(\d+\)|^\(\s*[a-z][a-z]?\s*\))|^([a-z]\.)|^([A-Z]{0,3}\.\s*“?[a-zA-Z]+)|^([a-z]{0,3}\.)|^[A-Z]\.\s*[a-zA-Z]+')
        Num_bracket_pattern = re.compile(r'^\(\d+\)')
        alpha_pattern = re.compile(r'^\(\s*[a-z][a-z]?\s*\)')
        # alp_pattern = re.compile(r'\(\D+\)')
        num_pattern = re.compile(r'^\d+\.')
        # num_pattern1 = re.compile(r'^1\.')
        numAlpha_pattern = re.compile(r'^\(\d+\)\s\(\D\)')
        alphanum_pattern = re.compile(r'^\(\D+\)\s(\d)+')

        ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
        # ol_tag = self.soup.new_tag("ol")
        ol_tag3 = self.soup.new_tag("ol")
        ol_tag1 = self.soup.new_tag("ol")
        ol_tag4 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
        ol_tag5 = self.soup.new_tag("ol")
        ol_tag6 = self.soup.new_tag("ol")
        rom_ol_tag = self.soup.new_tag("ol", type="i", **{"class": "roman"})
        ol_cap_tag = self.soup.new_tag("ol", type="A")

        ol_num = None
        ol_alpha = None
        ol_inr_num = None
        ol_inr_apha = None
        ol_inr_alpha = None
        ol_rom = None
        prev_id = 0
        current_id = 0
        pre_id = 0
        sec_id_list = []
        ol_count = 1
        ol_num_id = 0
        curr_id = 0

        for tag in self.soup.findAll("p", class_=self.class_regex["ol"]):
            current_tag = tag.text.strip()

            if re.match(pattern, tag.text.strip()):
                tag.name = "li"


            # if re.search(r'The health and safety of the public are affected by the degree ', current_tag):
            #     print(tag)



            elif re.match(r'^(Article)\s*[I,V,X]*\.', tag.text.strip()):
                tag.name = "h4"
                prev_id = tag.find_previous("h3").get("id")
                article_id = re.search(r'^(Article)\s*(?P<ar_id>[I,V,X]*)', tag.text.strip()).group("ar_id")
                tag["id"] = f'{prev_id}a{article_id}'
                tag["class"] = "article"

            elif re.match(r'^(ARTICLE)\s*[I,V,X]*', tag.text.strip()):
                tag.name = "h4"
                prev_id = tag.find_previous("h3").get("id")
                article_id = re.search(r'^(ARTICLE)\s*(?P<ar_id>[I,V,X]*)', tag.text.strip()).group("ar_id")
                tag["id"] = f'{prev_id}a{article_id}'
                tag["class"] = "article"

            elif re.match(r'Section\s*[A-Z]+\.|SECTION\s*[0-9]+\.*', tag.text.strip()):
                tag.name = "h4"
                if tag.find_previous("h4", class_="article"):
                    prev_id = tag.find_previous("h4", class_="article").get("id")
                else:
                    prev_id = tag.find_previous("h3").get("id")


                article_id = re.search(r'^(Section|SECTION)\s*(?P<ar_id>[A-Z]+|[0-9]+)\.*', tag.text.strip()).group("ar_id")
                tag["id"] = f'{prev_id}s{article_id}'
                tag["class"] = "section"


            # I.
            if re.match(r'^([A-Z]{0,3}\.\s*“?[a-zA-Z]+)', current_tag):
                if re.match(r'^([I,V,X]{0,3}\.)', current_tag) and not re.match(r'^H.', tag.find_previous("li").text.strip()):

                    ol_rom = tag
                    if re.search(r'^(I\.)', current_tag):
                        ol_tag1 = self.soup.new_tag("ol", type="I")
                        tag.wrap(ol_tag1)
                    else:
                        ol_tag1.append(tag)

                    tag_id = re.search(r'^(?P<id>[A-Z]{0,3})', current_tag).group('id')
                    prev_header_id = tag.find_previous("h3").get("id")
                    tag["id"] = f"{prev_header_id}ol1{tag_id}"

                else:
                    if re.search(r'^(A\.)', current_tag):
                        ol_tag1 = self.soup.new_tag("ol", type="A")
                        tag.wrap(ol_tag1)
                        tag_id = re.search(r'^(?P<id>[A-Z]{0,3})', current_tag).group('id')
                        if tag.find_previous("h4"):
                            prev_header_id = tag.find_previous("h4").get("id")
                            tag["id"] = f"{prev_header_id}ol1{tag_id}"

                    else:
                        if re.match(r'^[B-Z]\.', tag.text.strip()) and tag.find_previous().name == "span":
                            ol_tag1.append(tag)

                            tag_id = re.search(r'^(?P<id>[A-Z]{0,3})', current_tag).group('id')
                            if tag.find_previous("h4"):
                                prev_header_id = tag.find_previous("h4").get("id")
                                tag["id"] = f"{prev_header_id}ol1{tag_id}"
                        else:
                            tag.name = "p"

            # # (1)
            if re.match(Num_bracket_pattern, current_tag):
                ol_num = tag
                if re.search(r'^(\(1\))', current_tag):

                    if re.match(r'^([A-Z]{0,3}\.)', tag.find_previous().text.strip()):
                        tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
                        ol_tag = self.soup.new_tag("ol")
                        tag.wrap(ol_tag)
                        tag.find_previous("li").append(ol_tag)
                        if ol_rom:
                            prev_id = ol_rom.get("id")
                        else:
                            prev_id = tag.find_previous("li").get("id")
                        tag["id"] = f'{prev_id}{tag_id}'


                    elif re.match(r'^\([a-z]\)', tag.find_previous().text.strip()):

                        pre_id = tag.find_previous("li").get("id")
                        ol_tag = self.soup.new_tag("ol")
                        tag.wrap(ol_tag)
                        tag.find_previous("li").append(ol_tag)
                        tag["id"] = f'{pre_id}1'

                    else:

                        if tag.find_previous("h3") in sec_id_list:
                            ol_count = 1

                        ol_tag = self.soup.new_tag("ol")
                        tag.wrap(ol_tag)

                        tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')

                        if tag.find_previous("h4"):
                            if re.match(r'Section\s*[A-Z]+\.', tag.find_previous("h4").text.strip()):
                                prev_header_id = tag.find_previous("h4").get("id")
                            elif re.match(r'^(Article|ARTICLE)\s*[I,V,X]*', tag.find_previous("h4").text.strip()):
                                if tag.find_previous("h3") == tag.find_previous("h4").find_previous("h3"):
                                    prev_header_id = tag.find_previous("h4").get("id")
                                else:
                                    prev_header_id = tag.find_previous("h3").get("id")
                            else:
                                prev_header_id = tag.find_previous("h3").get("id")

                        else:
                            # print(tag)
                            prev_header_id = tag.find_previous("h3").get("id")

                        tag_id1 = f"{prev_header_id}ol{ol_count}{tag_id}"

                        tag["id"] = f"{prev_header_id}ol{ol_count}{tag_id}"

                        sec_id_list.append(tag.find_previous("h3"))

                else:

                    if re.search(r'History|HISTORY:', tag.find_next("p").text.strip()):
                        # print(tag)
                        ol_rom = None

                    ol_tag.append(tag)

                    tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
                    if ol_rom:
                        prev_header_id = ol_rom.get("id")
                        tag["id"] = f"{prev_header_id}{tag_id}"

                    else:
                        if tag.find_previous("h4"):
                            if re.match(r'Section\s*[A-Z]+\.', tag.find_previous("h4").text.strip()):
                                prev_header_id = tag.find_previous("h4").get("id")
                            elif re.match(r'^(Article|ARTICLE)\s*[I,V,X]*', tag.find_previous("h4").text.strip()):

                                # prev_header_id = tag.find_previous("h4").get("id")

                                if tag.find_previous("h3") == tag.find_previous("h4").find_previous("h3"):
                                    # print(tag)
                                    prev_header_id = tag.find_previous("h4").get("id")
                                else:
                                    prev_header_id = tag.find_previous("h3").get("id")

                            else:

                                prev_header_id = tag.find_previous("h3").get("id")
                        else:

                            prev_header_id = tag.find_previous("h3").get("id")

                        # prev_header_id = tag.find_previous("h3").get("id")
                        tag["id"] = f"{prev_header_id}ol{ol_count}{tag_id}"


            # (a)
            if re.match(alpha_pattern, current_tag):
                ol_alpha = tag
                if tag.find_previous("h4"):
                    if re.search(r'ARTICLE',tag.find_previous("h4").text.strip()):
                        prev_header_id = tag.find_previous("h4").get("id")
                    else:
                        prev_header_id = ol_num.get("id")

                if re.match(r'^\(a\)', tag.text.strip()) :
                    curr_id = None
                    ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                    tag.wrap(ol_tag2)

                    if re.match(alpha_pattern, tag.find_previous("li").text.strip()) and tag.find_previous().name == "span":
                        tag.find_previous("li").append(ol_tag2)
                        prev_header_id = tag.find_previous("li").get("id")
                        tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
                        curr_id = f"{prev_header_id}{tag_id}"
                        tag["id"] = f"{prev_header_id}{tag_id}"

                    elif tag.find_previous("ol").find_previous().name == "span" and not re.match(r'ARTICLE',tag.find_previous("ol").find_previous().text.strip()):
                        ol_num.append(ol_tag2)
                        tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
                        prev_header_id = ol_num.get("id")
                        alpha_id = f"{prev_header_id}{tag_id}"
                        tag["id"] = f"{prev_header_id}{tag_id}"

                    else:
                        if not re.match(r'ARTICLE',tag.find_previous().find_previous().text.strip()):
                            if not re.search(r'^[a-zA-Z]+', tag.find_previous().find_previous().text.strip()):
                                tag.find_previous("li").append(ol_tag2)
                                tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
                                prev_header_id = tag.find_previous("li").get("id")
                                tag["id"] = f"{prev_header_id}{tag_id}"
                            else:
                                if tag.find_previous().find_previous("li").parent.name == "ul":
                                    prev_header_id = tag.find_previous("h3").get("id")
                                    tag["id"] = f"{prev_header_id}ol1a"
                                else:
                                    tag.find_previous("li").append(ol_tag2)
                                    tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
                                    prev_header_id = tag.find_previous("li").get("id")
                                    tag["id"] = f"{prev_header_id}{tag_id}"

                else:
                    ol_tag2.append(tag)
                    tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
                    if tag.find_previous("li").get("id"):
                        prev_header_id = re.search(r'^.+ol\d\d*', tag.find_previous("li").get("id")).group()
                        tag["id"] = f"{prev_header_id}{tag_id}"

                    else:
                        prev_header_id = tag.find_previous("h3").get("id")
                        tag["id"] = f"{prev_header_id}{tag_id}"


                    # if curr_id:
                    #     prev_header_id = re.sub(r'\D$', '', curr_id)
                    #     tag["id"] = f"{prev_header_id}{tag_id}"
                    #
                    # else:
                    #     tag["id"] = f"{prev_header_id}{tag_id}"
                    #
                    # # prev_header_id = ol_num.get("id")
                    # alpha_id = f"{prev_header_id}{tag_id}"


            # # (4)(a)
            if re.match(numAlpha_pattern, current_tag):
                ol_inr_apha = tag
                prev_header = tag.find_previous("h3")
                prev_header_id = prev_header.get("id")

                tag_id1 = re.search(r'^\((?P<id1>\d+)\)\s*\((\D+)\)', current_tag).group("id1")
                tag_id2 = re.search(r'^\((\d+)\)\s*\((?P<id2>[a-z]+)\)', current_tag).group("id2")

                ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                li_tag = self.soup.new_tag("li")

                # li_tag.append(current_tag)

                tag_text = re.sub(numAlpha_pattern, '', tag.text.strip())
                li_tag.append(tag_text)

                li_tag["id"] = f"{prev_header_id}ol1{tag_id1}{tag_id2}"

                ol_tag2.append(li_tag)
                tag.contents = []
                tag.append(ol_tag2)

                # (4)(a)1.
                if re.match(r'\(\d+\)\s*\(\D\)\s*\d\.', current_tag):
                    ol_tag4 = self.soup.new_tag("ol")
                    inner_li_tag = self.soup.new_tag("li")

                    tag_text = re.sub(r'\(\d+\)\s*\(\D\)\s*\d\.', '', current_tag)
                    inner_li_tag.append(tag_text)

                    # print(tag)

                    # inner_li_tag.append(tag.text.strip())

                    tag_id1 = re.search(r'^(\(\d+\)\s*\((?P<id1>\D)\)\s*\d\.)', current_tag).group("id1")
                    tag_id2 = re.search(r'\(\d+\)\s*\(\D\)\s*(?P<id2>\d)\.', current_tag).group("id2")

                    prev_id = ol_inr_apha.get("id")
                    inner_li_tag["id"] = f"{prev_id}{tag_id1}{tag_id2}"
                    prev_header_id = f"{prev_id}{tag_id1}"
                    main_olcount = 2

                    ol_tag4.append(inner_li_tag)
                    tag.insert(1, ol_tag4)
                    ol_tag4.find_previous().string.replace_with(ol_tag4)

            # a
            if re.match(r'[a-z]([a-z])*\.', current_tag):

                ol_inr_apha = tag

                tag_id = re.search(r'^(?P<id>[a-z]([a-z])*)\.', current_tag).group('id')

                if re.match(r'a\.', current_tag):

                    ol_tag3 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})

                    if re.search(r'ARTICLE',tag.find_previous().find_previous().text.strip()):
                        tag.wrap(ol_tag3)
                        prev_id = tag.find_previous("h4").get("id")
                        tag["id"] = f"{prev_id}ol1{tag_id}"

                    elif re.match(num_pattern, tag.find_previous("li").text.strip()):

                        tag.wrap(ol_tag3)
                        # ol_tag5.append(ol_tag3)
                        tag.find_previous("li").append(ol_tag3)
                        prev_id = tag.find_previous("li").get("id")
                        tag["id"] = f"{prev_id}{tag_id}"
                    else:
                        tag.wrap(ol_tag3)
                        ol_tag.append(ol_tag3)
                        tag.find_previous("li").append(ol_tag3)
                        prev_id = tag.find_previous("li").get("id")
                        tag["id"] = f"{prev_id}{tag_id}"

                    # if tag.find_previous("li"):
                    #     # tag.find_previous("li").append(ol_tag3)
                    #     prev_id = tag.find_previous("li").get("id")
                    #     innr_alpha_id = f"{prev_id}{tag_id}"
                    #     tag["id"] = f"{prev_id}{tag_id}"


                else:

                    if re.match(r'i\.', current_tag) and re.match(r'ii\.', tag.find_next_sibling().text.strip()):
                        rom_ol_tag = self.soup.new_tag("ol", type="i", **{"class": "roman"})
                        tag.wrap(rom_ol_tag)
                        # ol_tag.append(rom_ol_tag)
                        tag.find_previous("li").append(rom_ol_tag)

                        pre_rom_id = tag.find_previous("li").get("id")
                        tag["id"] = f'{pre_rom_id}i'

                    elif re.match(r'[a-z]\.', current_tag):

                        ol_tag3.append(tag)

                        pre_id = re.sub(r'\D+$|\D\d+$','',tag.find_previous("li").get("id"))
                        tag["id"] = f"{pre_id}{tag_id}"

                    else:
                        rom_ol_tag.append(tag)
                        if tag.find_previous("li"):
                            if tag.find_previous("li").get("id"):
                                pre_rom_id = re.sub(r'\D+$','',tag.find_previous("li").get("id"))
                                cur_rom_id = re.search(r'^[^\s\.]+',current_tag).group()
                                tag["id"] = f'{pre_rom_id}{cur_rom_id}'

                if tag.span:
                    tag.span.string = ""

            # (a) 1.
            if re.match(alphanum_pattern, current_tag):
                ol_tag5 = self.soup.new_tag("ol")
                li_tag = self.soup.new_tag("li")

                tag_id1 = re.search(r'^\((?P<id1>\D+)\)\s(\d)+', current_tag).group("id1")
                tag_id2 = re.search(r'^\(\D+\)\s(?P<id2>\d)+', current_tag).group("id2")

                tag_text = re.sub(r'^\(\D+\)\s(\d)\.', '', current_tag)
                li_tag.append(tag_text)

                # li_tag.append(current_tag.strip())

                ol_tag5.append(li_tag)

                # prev_id = ol_inr_apha.get("id")
                prev_id = ol_alpha.get("id")
                # prev_id = li_tag.find_previous("li").get("id")
                li_tag["id"] = f"{prev_id}{tag_id2}"
                prev_header_id = f"{prev_id}{tag_id1}"
                main_olcount = 2

                tag.contents = []
                tag.append(ol_tag5)


                # 2.a.
            if re.match(r'(\d+\.(\s*[a-z]\.))', current_tag):

                if re.match(r'(\d+\.(\s*i\.))',current_tag):

                    rom_ol_tag = self.soup.new_tag("ol", type="i", **{"class": "roman"})
                    inner_a_tag = self.soup.new_tag("li")
                    tag_text = re.sub(r'(\d+\.(\s*(?P<prev>i\.)))', '', current_tag)
                    inner_a_tag.append(tag_text)
                    prev = tag.find_previous("li").get("id")

                    if prev:
                        prev = re.sub(r'\d$','',prev)
                        curr = re.search(r'(?P<prev>\d+\.\s*[a-z]\.)', current_tag).group("prev")
                        curr = re.sub(r'[\.\s]','',curr)
                        inner_a_tag["id"] = f'{prev}{curr}'

                    tag.clear()
                    rom_ol_tag.append(inner_a_tag)
                    tag.insert(1, rom_ol_tag)

                else:
                    ol_tag3 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                    inner_a_tag = self.soup.new_tag("li")
                    tag_text = re.sub(r'(\d+\.(\s*(?P<prev>[a-z])\.))', '', current_tag)
                    inner_a_tag.append(tag_text)
                    prev = tag.find_previous("li").get("id")

                    if prev:
                        prev = re.sub(r'\d$','',prev)
                        curr = re.search(r'(?P<prev>\d+\.\s*[a-z]\.)', current_tag).group("prev")
                        curr = re.sub(r'[\.\s]','',curr)
                        inner_a_tag["id"] = f'{prev}{curr}'

                    tag.clear()
                    ol_tag3.append(inner_a_tag)
                    tag.insert(1, ol_tag3)


            # 1.
            if re.match(num_pattern, current_tag):
                ol_num_id = tag
                if re.match(r'^1\.', current_tag):
                    ol_tag5 = self.soup.new_tag("ol")
                    tag.wrap(ol_tag5)

                    # if re.search(r'This section definitely rejects', current_tag):
                    #     print()


                    if re.search(alpha_pattern, tag.find_previous().find_previous().text.strip()) or re.search(r'^[a-zA-Z]+',tag.find_previous().find_previous().text.strip())\
                        or tag.find_previous().find_previous().text == "":

                        ol_tag2.append(ol_tag5)
                        tag.find_previous("li").append(ol_tag5)
                        prev_id = tag.find_previous("li").get("id")
                        main_olcount = 1
                        tag["id"] = f"{prev_id}{main_olcount}"
                        main_olcount += 1


                    elif tag.find_previous("h4"):
                        if not re.match(r'^(ARTICLE)\s*[I,V,X]*',
                                        tag.find_previous("h4").text.strip()) and not re.match(r'Section\s*[A-Z]+\.',
                                                                                               tag.find_previous(
                                                                                              "h4").text.strip()):

                            if tag.find_previous().find_previous().name == "li":
                                tag.find_previous("li").append(ol_tag5)
                                prev_id = tag.find_previous("li").get("id")
                                main_olcount = 1
                                tag["id"] = f"{prev_id}{main_olcount}"
                                main_olcount += 1

                            else:
                                prev_id = tag.find_previous("h4").get("id")
                                main_olcount = 1
                                tag["id"] = f"{prev_id}ol1{main_olcount}"
                                main_olcount += 1

                        else:
                            tag.find_previous("li").append(ol_tag5)
                            ar_id = tag.find_previous("li").get("id")
                            main_olcount = 1
                            tag["id"] = f"{ar_id}{main_olcount}"
                            main_olcount += 1

                    else:
                        pre_id = tag.find_previous("li").get("id")
                        tag.find_previous("li").append(ol_tag5)
                        main_olcount = 1
                        tag["id"] = f"{pre_id}{main_olcount}"
                        main_olcount += 1

                elif tag.find_previous("li"):
                    ol_tag5.append(tag)



                    if tag.find_previous("h4"):

                        if not re.match(r'^(ARTICLE)\s*[I,V,X]*',
                                        tag.find_previous("h4").text.strip()) and not re.match(
                                r'Section\s*[A-Z]+\.', tag.find_previous("h4").text.strip()):

                            prev_id = tag.find_previous("li").get("id")
                            if prev_id:
                                pre_id = re.sub(r'\D+$|\d\D$|\d+$', '', tag.find_previous("li").get("id"))

                                tag["id"] = f"{pre_id}1{main_olcount}"
                                main_olcount += 1

                        else:
                            current_id = f"{ar_id}{main_olcount}"

                            tag["id"] = f"{ar_id}{main_olcount}"
                            main_olcount += 1
                    else:
                        if tag.find_previous("li"):
                            if tag.find_previous("li").get("id"):
                                cur_id = re.sub(r'\d+$', '', tag.find_previous("li").get("id"))
                                tag["id"] = f"{cur_id}{main_olcount}"
                                main_olcount += 1

        print("ol tag is created")



    # writting soup to the file
    def write_soup_to_file(self):

        """
            - add the space before self closing meta tags
            - convert html to str
            - write html str to an output file
        """

        soup_str = str(self.soup.prettify(formatter=None))
        with open(f"../cic-code-ky/transforms/ky/ocky/r{self.release_number}/{self.html_file_name}", "w") as file:
            file.write(soup_str)

    # add css file
    def css_file(self):
        head = self.soup.find("head")
        style = self.soup.head.find("style")
        style.decompose()
        css_link = self.soup.new_tag("link")
        css_link.attrs[
            "href"] = "https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css"
        css_link.attrs["rel"] = "stylesheet"
        css_link.attrs["type"] = "text/css"
        head.append(css_link)

    def start_parse(self):

        """
                     - set the values to instance variables
                     - check if the file is constitution file or title file
                     - based on file passed call the methods to parse the passed htmls
        """

        self.release_label = f'Release-{self.release_number}'
        print(self.html_file_name)
        start_time = datetime.now()
        print(start_time)
        self.create_page_soup()
        self.css_file()
        if re.search('constitution', self.html_file_name):
            self.class_regex = {'ul': '^(§ )|^(ARTICLE)', 'head2': '^(§ )|^(ARTICLE)',
                                'title': '^(CONSTITUTION OF KENTUCKY)|^(THE CONSTITUTION OF THE UNITED STATES OF AMERICA)',
                                'sec_head': r'^([^\s]+[^\D]+)|^(Section)',
                                'junk': '^(Text)', 'ol': r'^(\(1\))',
                                'head4': '^(NOTES TO DECISIONS)|^(Compiler’s Notes.)'}

            self.get_class_name()
            self.create_main_tag()
            self.remove_junk()
            self.set_appropriate_tag_name_and_id1()
            self.create_ul_tag()
            self.create_chap_sec_nav1()
            self.create_link_to_notetodecision_nav1()
            self.create_ul_tag_to_notes_to_decision2()
            self.create_and_wrap_with_div_tag()
            self.add_citation1()
            self.add_watermark_and_remove_class_name()

        else:
            self.get_class_name()
            self.create_main_tag()
            self.remove_junk()
            self.set_appropriate_tag_name_and_id1()
            self.create_ul_tag()
            self.create_chap_sec_nav1()
            self.create_link_to_notetodecision_nav1()
            self.create_ul_tag_to_notes_to_decision2()
            self.create_and_wrap_with_div_tag()

            # self.wrap_with_ordered_tag_3()

            self.wrap_with_ordered_tag_4()
            self.create_numberical_ol()
            self.add_citation1()
            self.add_watermark_and_remove_class_name()

        self.write_soup_to_file()
        print(datetime.now() - start_time)



