from bs4 import BeautifulSoup, Doctype
import re
from datetime import datetime
from parser_base import ParserBase


class KYParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.class_regex = {'ul': '^CHAPTER', 'head2': '^CHAPTER', 'title': '^(TITLE)', 'sec_head': r'^([^\s]+[^\D]+)',
                            'junk': '^(Text)', 'ol': r'^(\(1\))', 'head4': '^(NOTES TO DECISIONS)',
                            'notetodecison-nav':r'NOTES TO DECISIONS'}
        self.title_id = None
        self.soup = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.html_file_name = input_file_name

        self.watermark_text = """Release {0} of the Official Code of Georgia Annotated released {1}.
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 1.4 on {2}.
        This document is not subject to copyright and is in the public domain.
        """


        self.start_parse()



    def create_page_soup(self):

        with open(f'transforms/ky/ocky/r{self.release_number}/raw/{self.html_file_name}') as open_file:
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

    # # replace title tag to "h1" and wrap it with "nav" tag
    def set_appropriate_tag_name_and_id(self):
        snav = 0
        chapter_id_list = []
        for header_tag in self.soup.body.find_all():
            if header_tag.get("class") == [self.class_regex["title"]]:
                header_tag.name = "h1"
                header_tag.attrs = {}
                header_tag.wrap(self.soup.new_tag("nav"))
                self.title_id = re.search(r'^(TITLE)\s(?P<title_id>\w+)', header_tag.text.strip()).group('title_id')

            elif header_tag.get("class") == [self.class_regex["head2"]]:
                if re.search("^(CHAPTER)|^(Chapter)", header_tag.text):
                    chap_nums = re.search(r'^(CHAPTER|Chapter)\s(?P<chapter_id>\w+)', header_tag.text.strip()).group(
                        'chapter_id').zfill(2)
                    header_tag.name = "h2"
                    header_tag.attrs = {}
                    header_tag['id'] = f"t{self.title_id}c{chap_nums}"

                elif re.search("^(Article)",header_tag.text):
                    chap_nums = re.search(r'^(Article)\s(?P<chapter_id>\w+)',
                                          header_tag.text.strip()).group(
                        'chapter_id').zfill(2)
                    header_tag.name = "h2"
                    header_tag.attrs = {}
                    header_tag['id'] = f"t{self.title_id}c{chap_nums}"
                    header_tag["class"] = "Articleh2"


                else:
                    header_tag.name = "h3"
                    header_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                    chap_nums = re.search(r'^(CHAPTER|Chapter)\s(?P<chapter_id>\w+)',
                                          header_tag.find_previous("h2").text.strip()).group('chapter_id').zfill(2)

                    header_tag["id"] = f"t{self.title_id}c{chap_nums}{header_id}"


            elif header_tag.get("class") == [self.class_regex["sec_head"]]:
                header_tag.name = "h3"

                # sec_pattern = re.compile(r'^(\d+\.\d+\.)')
                if re.match(r'^(\d+\.\d+\.)', header_tag.text.strip()):
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

                elif re.match(r'^(\d+\D\.\d+)', header_tag.text):

                    chap_num = re.search(r'^([^.]+)', header_tag.text).group().zfill(2)
                    sec_num = re.search(r'^(\d+\D\.\d+)', header_tag.text).group().zfill(2)
                    header_pattern = re.search(r'^(\d+\D\.\d+)', header_tag.text.strip()).group()
                    if header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"]):
                        prev_tag = header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"])
                        if header_pattern in prev_tag.text.split()[0]:
                            count = 0
                            header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}.{count + 1}"
                        else:
                            header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"

                elif re.match(r'^(\d+\D\.\d+-\d+)|^(\d+\.\d+-\d+)', header_tag.text):
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
                    chap_nums = re.search(r'^(CHAPTER|Chapter)\s(?P<chapter_id>\w+)', header_tag.text.strip()).group(
                        'chapter_id')
                    header_tag['id'] = f"t{self.title_id}c{chap_nums.zfill(2)}-cnav{chap_nums.zfill(2)}"

                else:
                    prev_chapter_id = header_tag.find_previous("h2").get("id")
                    if re.match(r'^(\d+\D*\.\d+)', header_tag.text.strip()):
                        sec_id = re.search(r'^(\d+\D*\.\d+)', header_tag.text.strip()).group()
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
                                                  header_tag.find_previous("h2").text.strip()).group(
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
                        sub_sec_text = re.sub(r'[\d\W]', '', header_tag.get_text()).lower()
                        sub_sec_id = f"{prev_head_tag}-{sub_sec_text}"
                        header_tag["id"] = sub_sec_id

                    elif re.match(r'^(\d+\.\s*—\s*[a-zA-Z]+)', header_tag.text.strip()):
                        prev_sub_tag = sub_sec_id
                        innr_sec_text = re.sub(r'[\d\W]', '', header_tag.get_text()).lower()
                        innr_sec_id1 = f"{prev_sub_tag}-{innr_sec_text}"
                        header_tag["id"] = innr_sec_id1

                    elif re.match(r'^(\d+\.\s*—\s*—\s*[a-zA-Z]+)', header_tag.text.strip()):
                        prev_child_tag = innr_sec_id1
                        innr_sec_text1 = re.sub(r'[\d\W]', '', header_tag.get_text()).lower()
                        innr_sec_id2 = f"{prev_child_tag}-{innr_sec_text1}"
                        header_tag["id"] = innr_sec_id2

                    elif re.match(r'^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)', header_tag.text.strip()):
                        prev_child_id1 = innr_sec_id2
                        innr_subsec_header_id = re.sub(r'[\d\W]', '', header_tag.get_text()).lower()
                        innr_subsec_header_tag_id = f"{prev_child_id1}-{innr_subsec_header_id}"
                        header_tag["id"] = innr_subsec_header_tag_id

        print("tags are replaced")

    # wrap list items with ul tag
    def create_ul_tag(self):
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

    # # create a reference
    # def create_chap_sec_nav(self):
    #     count = 0
    #     for list_item in self.soup.find_all("li"):
    #         if re.match(r'^(CHAPTER)|^(Chapter)', list_item.text.strip()):
    #             chap_nav_nums = re.search(r'(\s+[^\s]+)', list_item.text.strip())
    #             chap_nums = re.search(r'(\s+[^\s]+)', list_item.text).group(0)
    #             chap_num = re.sub(r'\s+', '', chap_nums).zfill(2)
    #             if chap_nav_nums:
    #                 nav_list = []
    #                 nav_link = self.soup.new_tag('a')
    #                 nav_link.append(list_item.text)
    #                 nav_link["href"] = f"#t{self.title_id}c{chap_num}"
    #                 nav_list.append(nav_link)
    #                 list_item.contents = nav_list
    #         else:
    #             if re.match(r'^(\d+\.\d+)', list_item.text.strip()):
    #                 chap_num = re.search(r'^([^.]+)', list_item.text.strip()).group().zfill(2)
    #                 sec_num = re.search(r'^(\d+\.\d+)', list_item.text.strip()).group(1).zfill(2)
    #                 sec_pattern = re.search(r'^(\d+\.\d+)', list_item.text.strip()).group()
    #                 sec_next_tag = list_item.find_next('li')
    #                 sec_prev_tag = list_item.find_previous("li")
    #                 sec_prev_tag_text = sec_prev_tag.a
    #                 if sec_next_tag:
    #                     if sec_pattern in sec_next_tag.text:
    #                         list_link = self.soup.new_tag('a')
    #                         list_link.string = list_item.text
    #
    #                         list_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
    #                         list_item.contents = [list_link]
    #
    #                     elif sec_prev_tag_text:
    #                         if sec_pattern in sec_prev_tag.a.text:
    #                             list_link = self.soup.new_tag('a')
    #                             list_link.string = list_item.text
    #
    #                             list_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}.{count + 1}"
    #                             list_item.contents = [list_link]
    #
    #                         else:
    #                             nav_link = self.soup.new_tag('a')
    #                             nav_link.string = list_item.text
    #                             nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
    #                             list_item.contents = [nav_link]
    #                 else:
    #                     nav_link = self.soup.new_tag('a')
    #                     nav_link.string = list_item.text
    #                     nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
    #                     list_item.contents = [nav_link]
    #
    #             elif re.match(r'^(\d+\D\.\d+)', list_item.text.strip()):
    #                 chap_num = re.search(r'^([^.]+)', list_item.text.strip()).group().zfill(2)
    #                 sec_num = re.search(r'^(\d+\D\.\d+)', list_item.text.strip()).group().zfill(2)
    #                 nav_link = self.soup.new_tag('a')
    #                 nav_link.string = list_item.text
    #                 nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
    #                 list_item.contents = [nav_link]
    #
    #             else:
    #                 chapter_header = list_item.find_previous("h2")
    #                 chap_nums = re.search(r'(\s+[^\s]+)', chapter_header.text.strip()).group(0)
    #                 chap_num = re.sub(r'\s+', '', chap_nums).zfill(2)
    #                 sec_id = re.sub(r'[\s+.]', '', list_item.get_text()).lower()
    #                 new_link = self.soup.new_tag('a')
    #                 new_link.string = list_item.text
    #                 new_link["href"] = f"#t{self.title_id}c{chap_num}{sec_id}"
    #                 list_item.contents = [new_link]

    # create ol tag for note to decision nav
    def create_ul_tag_to_notes_to_decision1(self):
        new_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        # new_nav_tag = self.soup.new_tag("nav")
        innr_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        innr_ul_tag1 = self.soup.new_tag("ul", **{"class": "leaders"})
        innr_ul_tag2 = self.soup.new_tag("ul", **{"class": "leaders"})

        for head_tag in self.soup.find_all("h4"):
            if head_tag.text.strip() == "NOTES TO DECISIONS":
                if re.match(r'^(\d+\.\s*\w+)', head_tag.findNext("p").text.strip()):
                    notetodecison_nav_class = head_tag.findNext("p").get("class")

        for note_tag in self.soup.find_all(class_=notetodecison_nav_class):
            if re.match(r'^(\d+\.)', note_tag.text.strip()) and note_tag.find_previous(
                    "h4") is not None and note_tag.find_previous(
                "h4").text.strip() == 'NOTES TO DECISIONS' and note_tag.find_next().name != "span":
                note_tag.name = "li"

            # parent
            if re.match(r'^(\d+\.\s*[a-zA-Z]+)', note_tag.text.strip()) and note_tag.name == "li":
                if re.match(r'^(1\.)', note_tag.text.strip()) and note_tag.name == "li":
                    new_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    note_tag.wrap(new_ul_tag)
                    new_ul_tag.wrap(self.soup.new_tag("nav"))
                else:
                    new_ul_tag.append(note_tag)

            # child
            if re.match(r'^(\d+\.\s*—\s*[a-zA-Z]+)|^(\d+\.\d+)', note_tag.text.strip()) and note_tag.name == "li":
                if re.match(r'^(\d+\.\s*[a-zA-Z]+)|^(\d+\.\d+)', note_tag.find_previous().text.strip()) and note_tag.name == "li":
                    innr_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    note_tag.wrap(innr_ul_tag)
                    new_ul_tag.append(innr_ul_tag)
                    note_tag.find_previous("li").append(innr_ul_tag)
                else:
                    innr_ul_tag.append(note_tag)

            # # grand child
            if re.match(r'^(\d+\.\s*—\s*—\s*[a-zA-Z]+)', note_tag.text.strip()) and note_tag.name == "li":
                if re.match(r'^(\d+\.\s*—\s*—\s*[a-zA-Z]+)',
                            note_tag.find_previous().text.strip()) and note_tag.name == "li":
                    innr_ul_tag1.append(note_tag)
                else:
                    innr_ul_tag1 = self.soup.new_tag("ul", **{"class": "leaders"})
                    note_tag.wrap(innr_ul_tag1)
                    note_tag.find_previous("li").append(innr_ul_tag1)

            # # super grand child
            if re.match(r'^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)', note_tag.text.strip()) and note_tag.name == "li":
                if re.match(r'^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)',
                            note_tag.find_previous().text.strip()) and note_tag.name == "li":
                    innr_ul_tag2.append(note_tag)
                else:
                    innr_ul_tag2 = self.soup.new_tag("ul", **{"class": "leaders"})
                    note_tag.wrap(innr_ul_tag2)
                    innr_ul_tag1.append(innr_ul_tag2)

            if re.match(r'^(\d+\.)', note_tag.text.strip()) and note_tag.find_previous(
                    "p") is not None and note_tag.find_previous("p").text.strip() == 'Analysis':
                note_tag.name = "li"

                if note_tag.find_previous().text.strip() == 'Analysis':
                    new_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    note_tag.wrap(new_ul_tag)
                    new_ul_tag.wrap(self.soup.new_tag("nav"))
                else:
                    new_ul_tag.append(note_tag)

    # add links to notes to decision nav
    def create_link_to_notetodecision_nav(self):
        nav_link = self.soup.new_tag('a')
        innr_nav_link1 = self.soup.new_tag('a')
        innr_nav_link2 = self.soup.new_tag('a')

        for head_tag in self.soup.find_all("h4"):
            if head_tag.text.strip() == "NOTES TO DECISIONS":
                if re.match(r'^(\d+\.\s*\w+)', head_tag.findNext("p").text.strip()):
                    notetodecison_nav_class = head_tag.findNext("p").get("class")


        for p_tag in self.soup.find_all(class_=notetodecison_nav_class):
            if re.match(r'^(\d+\.)', p_tag.text.strip()):
                if p_tag.find_previous("h4") is not None and p_tag.find_previous(
                        "h4").text.strip() == 'NOTES TO DECISIONS' and p_tag.find_next().name != "span":

                    if not re.match(r'^(\d+\.\s*—)', p_tag.text.strip()):
                        prev_head_tag = p_tag.find_previous("h4").get("id")
                        sub_sec_id = re.sub(r'[\d\W]', '', p_tag.get_text()).lower()
                        nav_link = self.soup.new_tag('a')
                        nav_link.string = p_tag.text
                        nav_link["href"] = f"#{prev_head_tag}-{sub_sec_id}"
                        p_tag.string = ''
                        p_tag.insert(0, nav_link)


                    elif re.match(r'^(\d+\.\s*—\s*[a-zA-Z]+)', p_tag.text.strip()):
                        prev_id = nav_link["href"]
                        sub_sec_id = re.sub(r'[\d\W]', '', p_tag.get_text()).lower()
                        innr_nav_link1 = self.soup.new_tag('a')
                        innr_nav_link1.string = p_tag.text
                        innr_nav_link1["href"] = f"{prev_id}-{sub_sec_id}"
                        p_tag.string = ''
                        p_tag.insert(0, innr_nav_link1)

                    elif re.match(r'^(\d+\.\s*—\s*—\s*[a-zA-Z]+)', p_tag.text.strip()):
                        child_id = innr_nav_link1["href"]
                        sub_sec_id = re.sub(r'[\d\W]', '', p_tag.get_text()).lower()
                        innr_nav_link2 = self.soup.new_tag('a')
                        innr_nav_link2.string = p_tag.text
                        innr_nav_link2["href"] = f"{child_id}-{sub_sec_id}"
                        p_tag.string = ''
                        p_tag.insert(0, innr_nav_link2)

                    elif re.match(r'^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)', p_tag.text.strip()):
                        grand_child_id = innr_nav_link2["href"]
                        sub_sec_id = re.sub(r'[\d\W]', '', p_tag.get_text()).lower()
                        innr_nav_link3 = self.soup.new_tag('a')
                        innr_nav_link3.string = p_tag.text
                        innr_nav_link3["href"] = f"{grand_child_id}-{sub_sec_id}"
                        p_tag.string = ''
                        p_tag.insert(0, innr_nav_link3)

                elif re.match(r'^(\d+\.\s*—\s*[a-zA-Z]+)', p_tag.text.strip()):
                    sub_sec = re.sub(r'[\d\W]', '', p_tag.get_text()).lower()
                    sub_sec_id = p_tag.find_previous("h5").get("id")
                    innr_nav_link1 = self.soup.new_tag('a')
                    innr_nav_link1.string = p_tag.text
                    innr_nav_link1["href"] = f"#{sub_sec_id}-{sub_sec}"
                    p_tag.string = ''
                    p_tag.insert(0, innr_nav_link1)

    # # wrapping with ol tag
    def wrap_with_ordered_tag1(self):
        pattern = re.compile(r'^(\d+)|^([(]\d+[)]|^[(]\s*[a-z][a-z]?\s*[)])|^(\D\.)')
        Num_bracket_pattern = re.compile(r'^\(\d+\)')
        alpha_pattern = re.compile(r'^\([a-z][a-z]?\)')
        # alp_pattern = re.compile(r'\(\D+\)')
        num_pattern = re.compile(r'^\d+\.')
        # num_pattern1 = re.compile(r'^1\.')
        numAlpha_pattern = re.compile(r'^\(\d+\)\s\(\D\)')
        alphanum_pattern = re.compile(r'^\(\D+\)\s(\d)+')

        ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
        ol_tag = self.soup.new_tag("ol")
        ol_tag3 = self.soup.new_tag("ol")
        ol_tag1 = self.soup.new_tag("ol")
        ol_tag4 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
        ol_tag5 = self.soup.new_tag("ol")

        ol_num = None
        ol_alpha = None
        ol_inr_num = None
        ol_inr_apha = None

        for tag in self.soup.findAll("p", class_=self.class_regex["ol"]):
            current_tag = tag.text.strip()
            if re.match(pattern, tag.text.strip()):
                tag.name = "li"

            # (1)
            if re.match(Num_bracket_pattern, current_tag):
                # pattern1 = re.findall(r'^\(\d+\)', tag.text.strip())
                ol_num = tag
                if re.search(r'^(\(1\))', current_tag):
                    ol_tag = self.soup.new_tag("ol")
                    tag.wrap(ol_tag)
                else:
                    ol_tag.append(tag)

                tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
                prev_header_id = tag.find_previous("h3").get("id")
                tag["id"] = f"{prev_header_id}ol1{tag_id}"

            # (a)
            if re.match(alpha_pattern, current_tag):
                ol_alpha = tag
                if re.match(r'^\(a\)', tag.text.strip()):
                    ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                    tag.wrap(ol_tag2)
                    ol_num.append(ol_tag2)
                else:
                    ol_tag2.append(tag)

                tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
                prev_header_id = ol_num.get("id")
                tag["id"] = f"{prev_header_id}{tag_id}"




            # # (4)(a)
            if re.match(numAlpha_pattern, current_tag):
                ol_inr_apha = tag
                prev_header = tag.find_previous("h3")
                prev_header_id = prev_header.get("id")

                tag_id1 = re.search(r'^\((?P<id1>\d+)\)\s*\((\D+)\)', current_tag).group("id1")
                tag_id2 = re.search(r'^\((\d+)\)\s*\((?P<id2>\D+)\)', current_tag).group("id2")

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
            if re.match(r'[a-z]\.', current_tag):
                if re.match(r'a\.', current_tag):
                    ol_tag3 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                    tag.wrap(ol_tag3)
                    ol_tag.append(ol_tag3)
                    tag.find_previous("li").append(ol_tag3)

                    inr_olcount = 97
                    prev_header_id = tag.find_previous("li").get("id")
                else:
                    tag.find_previous("li").append(tag)

                tag_id = re.search(r'^(?P<id>[a-z])\.', current_tag).group('id')
                tag["id"] = f"{prev_header_id}{tag_id}"

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

                prev_id = ol_inr_apha.get("id")
                li_tag["id"] = f"{prev_id}{tag_id1}{tag_id2}"
                prev_header_id = f"{prev_id}{tag_id1}"
                main_olcount = 2

                tag.contents = []
                tag.append(ol_tag5)

                # print(tag)
                # tag.span.string = ""

            # elif re.match(num_pattern, tag.text.strip()):
            #     tag.find_previous("li").append(tag)

            # 1. and previous (1)(a)
            if re.match(num_pattern, current_tag):
                if re.match(r'^1\.', current_tag):
                    ol_tag6 = self.soup.new_tag("ol")
                    tag.wrap(ol_tag6)
                    tag.find_previous("li").append(ol_tag6)

                    main_olcount = 1
                    if tag.find_previous("li"):
                        prev_header_id = tag.find_previous("li").get("id")

                elif tag.find_previous("li"):
                    tag.find_previous("li").append(tag)

                # prev_header_id = tag.find_previous("h3").get("id")
                tag["id"] = f"{prev_header_id}{main_olcount}"
                main_olcount += 1

            # 1. previous
        print("ol tag is created")

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
        pattern = re.compile(r'^(\d+)|^(\(\d+\)|^\([a-z][a-z]?\))|^(\[a-z]\.)')
        Num_bracket_pattern = re.compile(r'^\(\d+\)')
        alpha_pattern = re.compile(r'^\(\D+\)')
        num_pattern = re.compile(r'^\d+\.')
        # numAlpha_pattern = re.compile(r'^\(\d+\)\s\(\D\)')

        for tag in self.soup.findAll("li", class_=self.class_regex["ol"]):
            if re.match(pattern, tag.text.strip()):
                if re.match(Num_bracket_pattern, tag.text.strip()) or re.match(alpha_pattern,
                                                                               tag.text.strip()) or re.match(
                        num_pattern, tag.text.strip()):
                    if tag.span:
                        tag.span.string = ""

    # add watermark and remove default class names
    def add_watermark_and_remove_class_name(self):

        for tag in self.soup.find_all():
            if tag.name in ['li','h4','h3','p']:
                del tag["class"]

        watermark_tag = self.soup.new_tag('p', Class='transformation')
        watermark_tag.string = self.watermark_text.format(self.release_number, self.release_date,
                                                        datetime.now().date())

        title_tag = self.soup.find("nav")
        title_tag.insert(0,watermark_tag)

        for meta in self.soup.findAll('meta'):
            if meta.get('http-equiv') == "Content-Style-Type":
                meta.decompose()

    # citation
    def add_citation(self):
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
                      'X': ['116', '117', '117A', '118', '118A', '119', '120', '121', '121A', '122', '123', '124',
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
            if re.match(r'^(CHAPTER)', chap_tag.a.text.strip()):
                chap_list = re.search(r'^(CHAPTER\s*(?P<chap_num>\d+))', chap_tag.a.text.strip()).group("chap_num")
                chapter_list = chapter_list + [chap_list]

        cite_p_tags = []
        cite_li_tags = []
        titleid = ""

        for tag in self.soup.find_all(["p", "li"]):
            if re.search(r"KRS\s?\d+[a-zA-Z]*\.\d+(\(\d+\))*|"
                         r"(KRS Chapter \d+[a-zA-Z]*)|"
                         r"(KRS Title \D+, Chapter \D+?,)|"
                         r"KRS\s*\d+[a-zA-Z]*\.\d+\(\d+\)|"
                         r"(KRS\s*\d+[a-zA-Z]*\.\d+\(\d+\))", tag.text.strip()):
                # cite_li_tags.append(tag)
                text = str(tag)
                # print(tag)

                for match in [x[0] for x in re.findall(r'((KRS\s?\d+[a-zA-Z]*\.\d+(\(\d+\))*(\(\D\))*)|'
                                                       r'(Chapter \d+[a-zA-Z]*)|'
                                                       r'(Title\s+?\D+,\s+?Chapter\s+?\D+?,)|'
                                                       r'(\d+?\w?\.\d+\s+?\(\d\)+?)|'
                                                       r'(\d+\.\d{3}[^\d]))|'
                                                       r'(\d+\.\d{3}\(\d+\))|'
                                                       r'(KRS\s*\d+[a-zA-Z]*\.\d+\(\d+\))'
                        , tag.get_text())]:

                    if re.search(r'^(\d+\D*\.\d+)', tag.text.strip()):
                        continue

                    elif re.search(r'^\d+', tag.text.strip()):
                        continue
                    else:

                        match = re.sub(r'KRS\s', '', match.strip())
                        # print(match)

                        inside_text = re.sub(
                            r'<p\sclass="\w\d+">|</p>|<b>|</b>|<li\sclass="\w\d+"\sid="\w+\.\d+(\.\d+)?ol\d\d+">|</li>',
                            '', text, re.DOTALL)

                        # print(inside_text)

                        tag.clear()

                        # 1.2025/1A.2025
                        if re.search(r'(\d+[a-zA-Z]*\.\d+)', match.strip()):
                            chap_num = re.search(r'(?P<chap>\d+[a-zA-Z]*)\.\d+', match.strip()).group("chap")
                            # print(chap_num)
                            sec_num = re.search(r'(\d+[a-zA-Z]*\.\d+)', match.strip()).group().zfill(2)
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

                        # print(tag)

                        text = re.sub(fr'\s{re.escape(match)}',
                                      f'<cite class="ocky"><a href="{tag_id}" target="{target}">{match}</a></cite>',
                                      inside_text, re.I)
                        tag.append(text)

                        # print(tag)


    # wrapping with ol tag
    def wrap_with_ordered_tag2(self):
        pattern = re.compile(r'^(\d+)|^(\(\d+\)|^\(\s*[a-z][a-z]?\s*\))|^([a-z]\.)')
        Num_bracket_pattern = re.compile(r'^\(\d+\)')
        alpha_pattern = re.compile(r'^\(\s*[a-z][a-z]?\s*\)')
        # alp_pattern = re.compile(r'\(\D+\)')
        num_pattern = re.compile(r'^\d+\.')
        # num_pattern1 = re.compile(r'^1\.')
        numAlpha_pattern = re.compile(r'^\(\d+\)\s\(\D\)')
        alphanum_pattern = re.compile(r'^\(\D+\)\s(\d)+')

        ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
        ol_tag = self.soup.new_tag("ol")
        ol_tag3 = self.soup.new_tag("ol")
        ol_tag1 = self.soup.new_tag("ol")
        ol_tag4 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
        ol_tag5 = self.soup.new_tag("ol")

        ol_num = None
        ol_alpha = None
        ol_inr_num = None
        ol_inr_apha = None
        ol_rom = None

        # for tag in self.soup.find_all("p", class_="p9"):
        #     print(tag)



        for tag in self.soup.findAll("p", class_=self.class_regex["ol"]):
            current_tag = tag.text.strip()
            # print(current_tag)
            if re.match(pattern, tag.text.strip()):
                tag.name = "li"

            #     # I.
            # if re.match(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", current_tag):
            #     print(current_tag)
            #     # pattern1 = re.findall(r'^\(\d+\)', tag.text.strip())
            #     ol_num = tag
            #     if re.search(r'^(\(1\))|', current_tag):
            #         ol_tag = self.soup.new_tag("ol")
            #         tag.wrap(ol_tag)
            #     else:
            #         ol_tag.append(tag)
            #
            #     # tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
            #     # prev_header_id = tag.find_previous("h3").get("id")
            #     # tag["id"] = f"{prev_header_id}ol1{tag_id}"


         # (1)
            if re.match(Num_bracket_pattern, current_tag):
                # pattern1 = re.findall(r'^\(\d+\)', tag.text.strip())
                ol_num = tag
                if re.search(r'^(\(1\))', current_tag):
                    ol_tag = self.soup.new_tag("ol")
                    tag.wrap(ol_tag)
                else:
                    ol_tag.append(tag)

                tag_id = re.search(r'^(\((?P<id>\d+)\))', current_tag).group('id')
                prev_header_id = tag.find_previous("h3").get("id")
                tag["id"] = f"{prev_header_id}ol1{tag_id}"

            # # (a)
            if re.match(alpha_pattern, current_tag):

                ol_alpha = tag
                if re.match(r'^\(a\)', tag.text.strip()):
                    ol_tag2 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                    tag.wrap(ol_tag2)
                    ol_num.append(ol_tag2)
                else:
                    ol_tag2.append(tag)

                # print(current_tag)

                tag_id = re.search(r'^(\(\s*(?P<id>[a-z][a-z]?)\s*\))', current_tag).group('id')
                prev_header_id = ol_num.get("id")
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
            if re.match(r'[a-z]\.', current_tag):

                if re.match(r'a\.', current_tag):
                    ol_tag3 = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                    tag.wrap(ol_tag3)
                    ol_tag.append(ol_tag3)
                    tag.find_previous("li").append(ol_tag3)

                    inr_olcount = 97
                    prev_header_id = tag.find_previous("li").get("id")
                else:
                    tag.find_previous("li").append(tag)

                tag_id = re.search(r'^(?P<id>[a-z])\.', current_tag).group('id')
                tag["id"] = f"{prev_header_id}{tag_id}"

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

                prev_id = ol_inr_apha.get("id")
                li_tag["id"] = f"{prev_id}{tag_id1}{tag_id2}"
                prev_header_id = f"{prev_id}{tag_id1}"
                main_olcount = 2

                tag.contents = []
                tag.append(ol_tag5)

                # print(tag)
                # tag.span.string = ""

            # elif re.match(num_pattern, tag.text.strip()):
            #     tag.find_previous("li").append(tag)

            # 1. and previous (1)(a)
            if re.match(num_pattern, current_tag):

                if re.match(r'^1\.', current_tag):
                    ol_tag6 = self.soup.new_tag("ol")
                    tag.wrap(ol_tag6)
                    tag.find_previous("li").append(ol_tag6)

                    main_olcount = 1
                    if tag.find_previous("li"):
                        prev_header_id = tag.find_previous("li").get("id")

                elif tag.find_previous("li"):
                    tag.find_previous("li").append(tag)

                # prev_header_id = tag.find_previous("h3").get("id")
                tag["id"] = f"{prev_header_id}{main_olcount}"
                main_olcount += 1

        print("ol tag is created")

    # replace title tag to "h1" and wrap it with "nav" tag
    def set_appropriate_tag_name_and_id1(self):
        snav = 0
        cnav = 0
        anav= 0
        pnav = 0
        chapter_id_list = []
        for header_tag in self.soup.body.find_all():
            if header_tag.get("class") == [self.class_regex["title"]]:
                header_tag.name = "h1"
                header_tag.attrs = {}
                header_tag.wrap(self.soup.new_tag("nav"))
                self.title_id = re.search(r'^(TITLE)\s(?P<title_id>\w+)', header_tag.text.strip()).group('title_id')

            elif header_tag.get("class") == [self.class_regex["head2"]]:

                if re.search("^(CHAPTER)|^(Chapter)", header_tag.text):

                    chap_nums = re.search(r'^(CHAPTER|Chapter)\s(?P<chapter_id>\w+)', header_tag.text.strip()).group(
                        'chapter_id').zfill(2)

                    header_tag.name = "h2"
                    header_tag.attrs = {}
                    header_tag['id'] = f"t{self.title_id}c{chap_nums}"
                    header_tag["class"] = "chapterh2"


                elif re.search("^(Article)",header_tag.text):
                    artical_nums = re.search(r'^(Article)\s(?P<chapter_id>\w+)',
                                          header_tag.text.strip()).group(
                        'chapter_id').zfill(2)
                    header_tag.name = "h2"
                    header_tag.attrs = {}
                    prev_id = header_tag.find_previous("h2", class_= "chapterh2").get("id")

                    header_tag['id'] = f"{prev_id}a{artical_nums}"
                    header_tag["class"] = "Articleh2"

                    # print(header_tag)

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
                    header_tag.name = "h2"
                    prev_id = header_tag.find_previous("h2",class_="parth2").get("id")
                    if re.match("^([A-Z]\.)",header_tag.text):
                        subpart_nums = re.search(r'^((?P<chapter_id>[A-Z])\.)',header_tag.text.strip()).groups("chapter_id")
                    if re.match(r'^(Subpart)\s(?P<chapter_id>\w+)',header_tag.text):
                        subpart_nums = re.search(r'^(Subpart)\s(?P<chapter_id>\w+)',header_tag.text.strip()).groups("chapter_id")

                    chap_nums = header_tag.find_previous("h2").get("id")
                    header_tag["id"] = f"{prev_id}sub{subpart_nums}"

                    # print(header_tag)

                else:
                    header_tag.name = "h3"
                    prev_id = header_tag.find_previous("h2", class_="chapterh2").get("id")
                    header_id = re.sub(r'\s+', '', header_tag.get_text()).lower()
                #     chap_nums = re.search(r'^(CHAPTER|Chapter)\s(?P<chapter_id>\w+)',
                #                           header_tag.find_previous("h2").text.strip()).group('chapter_id').zfill(2)

                    header_tag["id"] = f"{prev_id}{header_id}"

                    # print(header_tag)


            elif header_tag.get("class") == [self.class_regex["sec_head"]]:
                header_tag.name = "h3"

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

                if re.match(r'^(\d+[a-z]?\.\d+-\d+\.)', header_tag.text.strip()):
                    chap_num = re.search(r'^([^.]+)', header_tag.text.strip()).group().zfill(2)
                    sec_num = re.search(r'^(\d+[a-z]?\.\d+-\d+)', header_tag.text.strip()).group().zfill(2)
                    header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"

                elif re.match(r'^(\d+\D\.\d+)', header_tag.text):

                    chap_num = re.search(r'^([^.]+)', header_tag.text).group().zfill(2)
                    sec_num = re.search(r'^(\d+\D\.\d+)', header_tag.text).group().zfill(2)
                    header_pattern = re.search(r'^(\d+\D\.\d+)', header_tag.text.strip()).group()
                    if header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"]):
                        prev_tag = header_tag.find_previous(name="h3", class_=self.class_regex["sec_head"])
                        if header_pattern in prev_tag.text.split()[0]:
                            count = 0
                            header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}.{count + 1}"
                        else:
                            header_tag["id"] = f"t{self.title_id}c{chap_num}s{sec_num}"

                elif re.match(r'^(\d+\D\.\d+-\d+)|^(\d+\.\d+-\d+)', header_tag.text):
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
                    chap_nums = re.search(r'^(CHAPTER|Chapter)\s(?P<chapter_id>\w+)', header_tag.text.strip()).group(
                        'chapter_id')
                    cnav = cnav+1
                    header_tag['id'] = f"t{self.title_id}c{chap_nums.zfill(2)}-cnav{cnav:02}"

                elif re.search("^(Article)", header_tag.text):
                    art_nums = re.search(r'^(Article)\s(?P<chapter_id>\w+)', header_tag.text.strip()).group(
                        'chapter_id')
                    if header_tag.find_previous_sibling().name != "li":
                        anav = 0
                    anav = anav+ 1
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


                    if re.match("^([A-Z]\.)",header_tag.text):
                        subpart_nums = re.search(r'^(?P<chapter_id1>[A-Z])\.',header_tag.text.strip()).group("chapter_id1")
                    if re.match(r'^(Subpart)',header_tag.text):
                        subpart_nums = re.search(r'^Subpart\s(?P<chapter_id2>\w+)',header_tag.text.strip()).group("chapter_id2")

                    chap_nums = header_tag.find_previous("h2").get("id")

                    if header_tag.find_previous_sibling().name != "li":
                        spnav = 0
                    spnav = spnav + 1


                    header_tag["id"] = f"{chap_nums}sub{subpart_nums.zfill(2)}-cnav{spnav:02}"


                else:
                    prev_chapter_id = header_tag.find_previous("h2").get("id")
                    if re.match(r'^(\d+\D*\.\d+)', header_tag.text.strip()):
                        sec_id = re.search(r'^(\d+\D*\.\d+)', header_tag.text.strip()).group()
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
                                                  header_tag.find_previous("h2", class_="chapterh2").text.strip()).group(
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
                        sub_sec_text = re.sub(r'[\d\W]', '', header_tag.get_text()).lower()
                        sub_sec_id = f"{prev_head_tag}-{sub_sec_text}"
                        header_tag["id"] = sub_sec_id

                    elif re.match(r'^(\d+\.\s*—\s*[a-zA-Z]+)', header_tag.text.strip()):
                        prev_sub_tag = sub_sec_id
                        innr_sec_text = re.sub(r'[\d\W]', '', header_tag.get_text()).lower()
                        innr_sec_id1 = f"{prev_sub_tag}-{innr_sec_text}"
                        header_tag["id"] = innr_sec_id1

                    elif re.match(r'^(\d+\.\s*—\s*—\s*[a-zA-Z]+)', header_tag.text.strip()):
                        prev_child_tag = innr_sec_id1
                        innr_sec_text1 = re.sub(r'[\d\W]', '', header_tag.get_text()).lower()
                        innr_sec_id2 = f"{prev_child_tag}-{innr_sec_text1}"
                        header_tag["id"] = innr_sec_id2

                    elif re.match(r'^(\d+\.\s*—\s*—\s*—\s*[a-zA-Z]+)', header_tag.text.strip()):
                        prev_child_id1 = innr_sec_id2
                        innr_subsec_header_id = re.sub(r'[\d\W]', '', header_tag.get_text()).lower()
                        innr_subsec_header_tag_id = f"{prev_child_id1}-{innr_subsec_header_id}"
                        header_tag["id"] = innr_subsec_header_tag_id

        print("tags are replaced")

    # create a reference
    def create_chap_sec_nav1(self):
        count = 0
        for list_item in self.soup.find_all("li"):
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
                    sec_pattern = re.search(r'^(\d+\.\d+)', list_item.text.strip()).group()
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
                            if sec_pattern in sec_prev_tag.a.text:
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
                    # print(list_item)
                    chap_num = re.search(r'^([^.]+)', list_item.text.strip()).group().zfill(2)
                    sec_num = re.search(r'^(\d+\D\.\d+)', list_item.text.strip()).group().zfill(2)
                    nav_link = self.soup.new_tag('a')
                    nav_link.string = list_item.text
                    nav_link["href"] = f"#t{self.title_id}c{chap_num}s{sec_num}"
                    list_item.contents = [nav_link]

                elif re.match(r'Article',list_item.text.strip()):
                    chap_num = list_item.find_previous("h2",class_="chapterh2").get("id")
                    art_nums = re.search(r'^(Article)\s(?P<chapter_id>\w+)', list_item.text.strip()).group(
                        'chapter_id')
                    new_link = self.soup.new_tag('a')
                    new_link.string = list_item.text
                    new_link["href"] = f"#{chap_num}a{art_nums.zfill(2)}"
                    list_item.contents = [new_link]

                elif re.match(r'Part\s\d\.',list_item.text.strip()):

                    chap_num = list_item.find_previous("h2",class_="Articleh2").get("id")
                    part_nums = re.search(r'^(Part)\s(?P<chapter_id>\w+)', list_item.text.strip()).group(
                        'chapter_id')
                    new_link = self.soup.new_tag('a')
                    new_link.string = list_item.text
                    new_link["href"] = f"#{chap_num}p{part_nums.zfill(2)}"
                    list_item.contents = [new_link]

                elif re.search("^([A-Z]\.)|^(Subpart)", list_item.text.strip()):
                    chap_num = list_item.find_previous("h2", class_="parth2").get("id")

                    if re.match("^([A-Z]\.)", list_item.text.strip()):
                        subpart_nums = re.search(r'^(?P<chapter_id1>[A-Z])\.',list_item.text.strip()).group(
                            "chapter_id1")
                    if re.match(r'^(Subpart)', list_item.text.strip()):
                        subpart_nums = re.search(r'^Subpart\s(?P<chapter_id2>\w+)', list_item.text.strip()).group(
                            "chapter_id2")

                    new_link = self.soup.new_tag('a')
                    new_link.string = list_item.text

                    new_link["href"] = f"#{chap_num}p{subpart_nums.zfill(2)}"
                    list_item.contents = [new_link]

                else:
                    chapter_header = list_item.find_previous("h2")
                    chap_nums = re.search(r'(\s+[^\s]+)', chapter_header.text.strip()).group(0)
                    chap_num = re.sub(r'\s+', '', chap_nums).zfill(2)
                    sec_id = re.sub(r'[\s+.]', '', list_item.get_text()).lower()
                    new_link = self.soup.new_tag('a')
                    new_link.string = list_item.text
                    new_link["href"] = f"#t{self.title_id}c{chap_num}{sec_id}"
                    list_item.contents = [new_link]

                # if re.match(r'^(\d+\.\d+-\d+\.)', list_item.text.strip()):
                #
                #     chap_num = re.search(r'^([^.]+)', list_item.text.strip()).group().zfill(2)
                #     sec_num = re.search(r'^(\d+\.\d+-\d+)', list_item.text.strip()).group().zfill(2)
                #
                #     nav_link = self.soup.new_tag('a')
                #     nav_link.string = list_item.text
                #     nav_link["href"] = f"#t{self.title_id}c{chap_num.zfill(2)}s{sec_num}"
                #     list_item.contents = [nav_link]


    # writting soup to the file
    def write_soup_to_file(self):
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
        self.release_label = f'Release-{self.release_number}'
        print(self.html_file_name)
        start_time = datetime.now()
        print(start_time)
        self.create_page_soup()
        self.css_file()
        self.get_class_name()
        self.create_main_tag()
        self.remove_junk()
        self.set_appropriate_tag_name_and_id1()
        self.create_ul_tag()
        self.create_chap_sec_nav1()
        self.create_link_to_notetodecision_nav()
        self.create_ul_tag_to_notes_to_decision1()
        self.create_and_wrap_with_div_tag()
        self.wrap_with_ordered_tag2()
        self.create_numberical_ol()
        self.add_citation()
        self.add_watermark_and_remove_class_name()
        self.write_soup_to_file()
        print(datetime.now() - start_time)
