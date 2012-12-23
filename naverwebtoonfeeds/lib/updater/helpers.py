import HTMLParser
import re

import lxml.html


htmlparser = HTMLParser.HTMLParser()


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
