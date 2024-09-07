"""
Better Emphasis.

pymdownx.betterem
Add intelligent handling of to em and strong notations

MIT license.

Copyright (c) 2014 - 2017 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
import re
from markdown import Extension
from markdown.inlinepatterns import SimpleTextInlineProcessor
from . import util

SMART_UNDER_CONTENT = r'(.+?_*?)'
SMART_STAR_CONTENT = r'(.+?\**?)'
UNDER_CONTENT = r'(_|(?:(?<=\s)_|[^_])+?)'
UNDER_CONTENT2 = r'((?:[^_]|(?<!_{2})_)+?)'
STAR_CONTENT = r'(\*|(?:(?<=\s)\*|[^\*])+?)'
STAR_CONTENT2 = r'((?:[^\*]|(?<!\*{2})\*)+?)'

# Avoid starting a pattern with asterisk or underscore tokens that are surrounded by white space.
NOT_STRONG = r'((^|(?<=\s))(\*+|_+)(?=\s|$))'

# ***strong,em***
STAR_STRONG_EM = r'(\*{3})(?!\s)(\*{1,2}|[^\*]+?)(?<!\s)\1'
# ___strong,em___
UNDER_STRONG_EM = r'(_{3})(?!\s)(_{1,2}|[^_]+?)(?<!\s)\1'
# ***strong,em*strong**
STAR_STRONG_EM2 = r'(\*{{3}})(?![\s\*]){}(?<!\s)\*{}(?<!\s)\*{{2}}'.format(STAR_CONTENT, STAR_CONTENT2)
# ___strong,em_strong__
UNDER_STRONG_EM2 = r'(_{{3}})(?![\s_]){}(?<!\s)_{}(?<!\s)_{{2}}'.format(UNDER_CONTENT, UNDER_CONTENT2)
# ***em,strong**em*
STAR_EM_STRONG = r'(\*{{3}})(?![\s\*]){}(?<!\s)\*{{2}}{}(?<!\s)\*'.format(STAR_CONTENT2, STAR_CONTENT)
# **strong*em,strong***
STAR_STRONG_EM3 = r'(\*{{2}})(?![\s\*]){}\*(?![\s\*]){}(?<!\s)\*{{3}}'.format(STAR_CONTENT, STAR_CONTENT)
# ___em,strong__em_
UNDER_EM_STRONG = r'(_{{3}})(?![\s_]){}(?<!\s)_{{2}}{}(?<!\s)_'.format(UNDER_CONTENT2, UNDER_CONTENT)
# __strong_em,strong___
UNDER_STRONG_EM3 = r'(_{{2}})(?![\s_]){}_(?![\s_]){}(?<!\s)_{{3}}'.format(UNDER_CONTENT, UNDER_CONTENT)
# **strong**
STAR_STRONG = r'(\*{2})(?!\s)%s(?<!\s)\1' % STAR_CONTENT2
# __strong__
UNDER_STRONG = r'(_{2})(?!\s)%s(?<!\s)\1' % UNDER_CONTENT2

# Prioritize *value* when **value** is nested within
STAR_EM2 = r'(?<!\*)(\*)(?![\*\s])(.+?)(?<![\*\s])(\*)(?!\*)'
# Prioritize _value_ when __value__ is nested within
UNDER_EM2 = r'(?<!_)(_)(?![_\s])(.+?)(?<![_\s])(_)(?!_)'

# *emphasis*
STAR_EM = r'(\*)(?!\s)%s(?<!\s)\1' % STAR_CONTENT
# _emphasis_
UNDER_EM = r'(_)(?!\s)%s(?<!\s)\1' % UNDER_CONTENT

# Smart rules for when "smart underscore" is enabled
# SMART: ___strong,em___
SMART_UNDER_STRONG_EM = r'(?<!\w)(_{3})(?![\s_])%s(?<!\s)\1(?!\w)' % SMART_UNDER_CONTENT
# ___strong,em_ strong__
SMART_UNDER_STRONG_EM2 = \
    r'(?<!\w)(_{{3}})(?![\s_]){}(?<!\s)_(?!\w){}(?<!\s)_{{2}}(?!\w)'.format(SMART_UNDER_CONTENT, SMART_UNDER_CONTENT)
# ___em,strong__ em_
SMART_UNDER_EM_STRONG = \
    r'(?<!\w)(_{{3}})(?![\s_]){}(?<!\s)_{{2}}(?!\w){}(?<!\s)_(?!\w)'.format(SMART_UNDER_CONTENT, SMART_UNDER_CONTENT)
# __strong__
SMART_UNDER_STRONG = r'(?<!\w)(_{2})(?![\s_])%s(?<!\s)\1(?!\w)' % SMART_UNDER_CONTENT
# SMART _em_
SMART_UNDER_EM = r'(?<!\w)(_)(?![\s_])%s(?<!\s)\1(?!\w)' % SMART_UNDER_CONTENT
# Prioritize _value_ when __value__ is nested within
SMART_UNDER_EM2 = r'(?<![\w_])(_)(?![_\s])(.+?)(?<![_\s])(_)(?![_\w])'

# Smart rules for when "smart asterisk" is enabled
# SMART: ***strong,em***
SMART_STAR_STRONG_EM = r'(?:(?<=\w)|(?<![\w\*]))(\*{3})(?![\s\*])%s(?<!\s)\1(?:(?=\w)|(?![\w\*]))' % SMART_STAR_CONTENT
# ***strong,em* strong**
SMART_STAR_STRONG_EM2 = \
    r'(?:(?<=\w)|(?<![\w\*]))(\*{{3}})(?![\s\*]){}(?<!\s)\*(?:(?=_)|(?![\w\*])){}(?<!\s)\*{{2}}(?:(?=\w)|(?![\w\*]))'.format(
        SMART_STAR_CONTENT, SMART_STAR_CONTENT
    )
# ***em,strong** em*
SMART_STAR_EM_STRONG = \
    r'(?:(?<=\w)|(?<![\w\*]))(\*{{3}})(?![\s\*]){}(?<!\s)\*{{2}}(?:(?=_)|(?![\w\*])){}(?<!\s)\*(?:(?=\w)|(?![\w\*]))'.format(
        SMART_STAR_CONTENT, SMART_STAR_CONTENT
    )
# **strong**
SMART_STAR_STRONG = r'(?:(?<=\w)|(?<![\w\*]))(\*{2})(?![\s\*])%s(?<!\s)\1(?:(?=\w)|(?![\w\*]))' % SMART_STAR_CONTENT
# SMART *em*
SMART_STAR_EM = r'(?:(?<=\w)|(?<![\w\*]))(\*)(?![\s\*])%s(?<!\s)\1(?:(?=\w)|(?![\w\*]))' % SMART_STAR_CONTENT
# Prioritize *value* when **value** is nested within
SMART_STAR_EM2 = r'(?<![\w\*])(\*)(?![\*\s])(.+?)(?<![\*\s])(\*)(?![\*\w])'


class AsteriskProcessor(util.PatternSequenceProcessor):
    """Emphasis processor for handling strong and em matches."""

    PATTERNS = [
        util.PatSeqItem(re.compile(STAR_STRONG_EM, re.DOTALL | re.UNICODE), 'double', 'strong,em'),
        util.PatSeqItem(re.compile(STAR_EM_STRONG, re.DOTALL | re.UNICODE), 'double', 'em,strong'),
        util.PatSeqItem(re.compile(STAR_STRONG_EM2, re.DOTALL | re.UNICODE), 'double', 'strong,em'),
        util.PatSeqItem(re.compile(STAR_STRONG_EM3, re.DOTALL | re.UNICODE), 'double2', 'strong,em'),
        util.PatSeqItem(re.compile(STAR_STRONG, re.DOTALL | re.UNICODE), 'single', 'strong'),
        util.PatSeqItem(re.compile(STAR_EM2, re.DOTALL | re.UNICODE), 'single', 'em', True),
        util.PatSeqItem(re.compile(STAR_EM, re.DOTALL | re.UNICODE), 'single', 'em')
    ]


class SmartAsteriskProcessor(util.PatternSequenceProcessor):
    """Smart emphasis and strong processor."""

    PATTERNS = [
        util.PatSeqItem(re.compile(SMART_STAR_STRONG_EM, re.DOTALL | re.UNICODE), 'double', 'strong,em'),
        util.PatSeqItem(re.compile(SMART_STAR_EM_STRONG, re.DOTALL | re.UNICODE), 'double', 'em,strong'),
        util.PatSeqItem(re.compile(SMART_STAR_STRONG_EM2, re.DOTALL | re.UNICODE), 'double', 'strong,em'),
        util.PatSeqItem(re.compile(SMART_STAR_STRONG, re.DOTALL | re.UNICODE), 'single', 'strong'),
        util.PatSeqItem(re.compile(SMART_STAR_EM2, re.DOTALL | re.UNICODE), 'single', 'em', True),
        util.PatSeqItem(re.compile(SMART_STAR_EM, re.DOTALL | re.UNICODE), 'single', 'em')
    ]


class UnderscoreProcessor(util.PatternSequenceProcessor):
    """Emphasis processor for handling strong and em matches."""

    PATTERNS = [
        util.PatSeqItem(re.compile(UNDER_STRONG_EM, re.DOTALL | re.UNICODE), 'double', 'strong,em'),
        util.PatSeqItem(re.compile(UNDER_EM_STRONG, re.DOTALL | re.UNICODE), 'double', 'em,strong'),
        util.PatSeqItem(re.compile(UNDER_STRONG_EM2, re.DOTALL | re.UNICODE), 'double', 'strong,em'),
        util.PatSeqItem(re.compile(UNDER_STRONG_EM3, re.DOTALL | re.UNICODE), 'double2', 'strong,em'),
        util.PatSeqItem(re.compile(UNDER_STRONG, re.DOTALL | re.UNICODE), 'single', 'strong'),
        util.PatSeqItem(re.compile(UNDER_EM2, re.DOTALL | re.UNICODE), 'single', 'em', True),
        util.PatSeqItem(re.compile(UNDER_EM, re.DOTALL | re.UNICODE), 'single', 'em')
    ]


class SmartUnderscoreProcessor(util.PatternSequenceProcessor):
    """Emphasis processor for handling strong and em matches."""

    PATTERNS = [
        util.PatSeqItem(re.compile(SMART_UNDER_STRONG_EM, re.DOTALL | re.UNICODE), 'double', 'strong,em'),
        util.PatSeqItem(re.compile(SMART_UNDER_EM_STRONG, re.DOTALL | re.UNICODE), 'double', 'em,strong'),
        util.PatSeqItem(re.compile(SMART_UNDER_STRONG_EM2, re.DOTALL | re.UNICODE), 'double', 'strong,em'),
        util.PatSeqItem(re.compile(SMART_UNDER_STRONG, re.DOTALL | re.UNICODE), 'single', 'strong'),
        util.PatSeqItem(re.compile(SMART_UNDER_EM2, re.DOTALL | re.UNICODE), 'single', 'em', True),
        util.PatSeqItem(re.compile(SMART_UNDER_EM, re.DOTALL | re.UNICODE), 'single', 'em')
    ]


class BetterEmExtension(Extension):
    """Add extension to Markdown class."""

    def __init__(self, *args, **kwargs):
        """Initialize."""

        self.config = {
            'smart_enable': ["underscore", "Treat connected words intelligently - Default: underscore"]
        }

        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md):
        """Modify inline patterns."""

        # Not better yet, so let's make it better
        md.registerExtension(self)
        self.make_better(md)

    def make_better(self, md):
        """
        Configure all the pattern rules.

        This should be used instead of smart_strong package.
        pymdownx.extra should be used in place of markdown.extensions.extra.
        """

        config = self.getConfigs()
        enabled = config["smart_enable"]
        enable_all = enabled == "all"
        enable_under = enabled == "underscore" or enable_all
        enable_star = enabled == "asterisk" or enable_all

        # If we don't have to move an existing extension, use the same priority,
        # but if we do have to, move it closely to the relative needed position.
        md.inlinePatterns.deregister('not_strong', False)
        md.inlinePatterns.deregister('strong_em', False)
        md.inlinePatterns.deregister('em_strong', False)
        md.inlinePatterns.deregister('em_strong2', False)
        md.inlinePatterns.deregister('strong', False)
        md.inlinePatterns.deregister('emphasis', False)
        md.inlinePatterns.deregister('strong2', False)
        md.inlinePatterns.deregister('emphasis2', False)

        md.inlinePatterns.register(SimpleTextInlineProcessor(NOT_STRONG), 'not_strong', 70)
        asterisk = SmartAsteriskProcessor(r'\*') if enable_star else AsteriskProcessor(r'\*')
        md.inlinePatterns.register(asterisk, "strong_em", 50)
        underscore = SmartUnderscoreProcessor('_') if enable_under else UnderscoreProcessor('_')
        md.inlinePatterns.register(underscore, "strong_em2", 40)


def makeExtension(*args, **kwargs):
    """Return extension."""

    return BetterEmExtension(*args, **kwargs)
