from bs4 import BeautifulSoup
import re

class kyOperations:

    def header_function(self, soup):

        nav_tag = soup.new_tag("nav")
        ul_tag = soup.new_tag("ul")
        chap_sec_headers = soup.findAll("p", class_="p2")

        for tag in soup.findAll("p"):
            # title head
            if tag["class"] == ['p1']:
                tag.name = "h1"
                tag.wrap(nav_tag)

            # section head
            if tag["class"] == ['p4']:
                chap_num = re.findall(r'^([^\.]+)', tag.text)
                chap_id = "".join(chap_num)
                sec_num = re.findall(r'^([^\s]+)', tag.text)
                sec_id = "".join(sec_num)
                tag['id'] = f"t01c0{chap_id}s{sec_id}"
                tag.name = "h3"

            # chapter head
            if tag["class"] == ['p3']:
                chap_nums = re.findall(r'\d', tag.text)
                chap_id = "".join(chap_nums)
                tag['id'] = f"t01c0{chap_id}"
                #tag.name = "h2"

            # sections
            if tag["class"] == ["p6"]:
                tag.wrap(soup.new_tag("div"))

            # list items
            if tag["class"] == ['p2'] and tag.find_previous_sibling("p") == None :
                tag.name = "li"
                #tag.wrap(soup.new_tag("ul"))
            #
            # elif tag["class"] == ["p2"] and tag.find_previous_sibling("li") != None:
            #     tag.append(soup.new_tag("ul"))

                # if tag.name == "li":
                #     tag.wrap(soup.new_tag("ul"))


                #tag.wrap(soup.new_tag("a"))

                    #tag.wrap(ul_tag)
                     #nav_tag.append(tag)
                    #tag.append(nav_tag)




                   #print(tag.find_previous_siblings("h1"))
                   # if tag.find_previous_sibling("p") == None:
                   #      #print(tag)
                   #      tag.wrap(ul_tag)












with open("/home/mis/gov.ky.krs.title.01.html") as fp:
    soup = BeautifulSoup(fp, "lxml")

kyOperations_obj = kyOperations()
kyOperations_obj.header_function(soup)

with open("ky.html", "w") as file:
    file.write(str(soup))