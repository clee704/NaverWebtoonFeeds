import HTMLParser
import re

import lxml.html


htmlparser = HTMLParser.HTMLParser()


def br2nl(html):
    """
    Convert newlines to spaces, <br> tags to newlines, collapse consecutive
    whitespaces into single whitespace, remove leading and trailing
    whitespaces, and unescape HTML entities.

    >>> br2nl('hello,<br>world! ')
    'hello,\\nworld!'
    >>> br2nl('\\nnice to meet you!<br />')
    'nice to meet you!'
    >>> br2nl(' <br> welcome<br >to  <br/>  earth')
    'welcome\\nto\\nearth'

    """
    newlines_removed = html.replace('\r\n', '\n').replace('\n', ' ')
    br_converted = re.sub(r'<br */?>', '\n', newlines_removed)
    whitespaces_collapsed = re.sub(r' +', ' ', br_converted)
    whitespaces_merged = re.sub(r' ?\n ?', '\n', whitespaces_collapsed)
    return htmlparser.unescape(whitespaces_merged.strip())


def inner_html(element):
    """
    Return the string for this HtmlElement, without enclosing start and end
    tags, or an empty string if this is a self-enclosing tag.

    >>> lxml.html.fromstring('<p>hello,<br>world!</p>').inner_html()
    u'hello,<br>world!'
    >>> lxml.html.fromstring('<div class="foo"><span>bar <span>bar</span></span> bar</div>').inner_html()
    u'<span>bar <span>bar</span></span> bar'
    >>> lxml.html.fromstring('<img src="http://nowhere.com/nothing.jpg" />').inner_html()
    u''
    >>> lxml.html.fromstring(u'<p>\ub17c\uc544\uc2a4\ud0a4</p>').text
    u'\ub17c\uc544\uc2a4\ud0a4'

    """
    outer = lxml.html.tostring(element, encoding='UTF-8').decode('UTF-8')
    i, j = outer.find('>'), outer.rfind('<')
    return outer[i + 1:j]
