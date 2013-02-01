# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Copyright 2011 Sam Liu.
#
# The Initial Developer of the Original Code is
# Sam Liu
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s): Sam Liu <sam@ambushnetworks.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import urllib
import simplejson as json
import re
import BeautifulSoup
import sys

# Wikipedia's api url
WIKI_REQUEST_URL = ("http://en.wikipedia.org/w/api.php?action=parse&prop=text"
                    "&format=json&disablepp=true&page=")


class WikipediaAPI(object):

    def init(self):
        pass

    def smart_str(self, text):
        return unicode(text).encode("utf-8")

    def visible(self, element):
        if element.parent.name is not None:
            visible_elements = ['table', 'ul', 'li', 'tr', 'td', 'style',
                                'script', '[document]', 'head', 'title']
            if element.parent.name in visible_elements:
                return False
            return True

    def query(self, keyword, section=-1):
        # Generate the request url
        request_url = self.smart_str(WIKI_REQUEST_URL + keyword)

        # Get a certain section
        if(section > -1):
            request_url = request_url + "&section=" + str(section)

        # Load into JSON
        json_result = json.load(urllib.urlopen(request_url))
        if 'error' in json_result:
            print json_result['error']['info']
            return

        # The HTML is retrieved from the JSON
        html = json_result['parse']['text']['*']

        # Load result HTML into BeautifulSoup for parsing
        soup = BeautifulSoup.BeautifulSoup(html)

        # Decide if the page is a redirect. If so, requery
        redirect = soup('li', text=re.compile(r'REDIRECT\b'))
        if(len(redirect) > 0):
            redirect_target = soup('a')[0]['title']
            print redirect_target
            return self.query(redirect_target, section=section)

        # Remove any elements we don't want from our html tree
        unwanted = []

        # We add each element tree to our unwanted array for later processing
        unwanted.append(soup.findAll('div', {'class': "dablink"}))
        unwanted.append(soup.findAll('div', {'class': "thumbcaption"}))
        unwanted.append(soup.findAll(
            'div', {'class': "rellink relarticle mainarticle"}))
        unwanted.append(soup.findAll(
            'div', {'class': "rellink boilerplate seealso"}))
        unwanted.append(soup.findAll('strong', {'class': "error"}))
        unwanted.append(soup.findAll('span', {'class': "mw-headline"}))
        unwanted.append(soup.findAll('table'))
        unwanted.append(soup.findAll('ul'))
        unwanted.append(soup.findAll('ol'))
        unwanted.append(soup.findAll('li'))
        unwanted.append(soup.findAll('h2'))

        # For each subtree in the unwanted array, delete its elements
        for x in unwanted:
            for element in x:
                element.extract()

        # Get the html tree without the removed elements
        texts = soup.findAll(text=True)

        # Only retain elements containing "visible text"
        visible_texts = filter(self.visible, texts)

        # Create string from array of strings
        textblob = "".join(x + str(" ") for x in visible_texts)

        # Use regex to remove bracketed items e.g [14], and html encoded
        # artifacts e.g &#1924;
        textblob = re.sub(r'\[.*?\]|&#\w+;', ' ', textblob)

        # Clean up multiple spaces
        textblob = " ".join(textblob.split())

        return unicode(textblob).encode("utf-8")


def cli():
    if len(sys.argv) > 1:
        wiki = WikipediaAPI()
        print wiki.query("".join(sys.argv[1:]), 0)
    else:
        print "Usage: ./" + sys.argv[0] + " \"keyword string here\""

if __name__ == "__main__":
    cli()
