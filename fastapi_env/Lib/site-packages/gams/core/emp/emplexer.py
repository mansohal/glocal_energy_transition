#
# GAMS - General Algebraic Modeling System Python API
#
# Copyright (c) 2017-2024 GAMS Development Corp. <support@gams.com>
# Copyright (c) 2017-2024 GAMS Software GmbH <support@gams.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

# module: emplexer.py
#
# This module contains the lexing rules for the EMP.
#
# Contributor: Youngdae Kim (02.17.2019)

import ply.lex as lex

tokens = [
    'COMMA',
    'ID',
    'NUMBER',
    'LPAREN',
    'RPAREN',
    'SQUOTE',
    'DQUOTE',
    'DOLLAR',
]

reserved = {
    'dualvar'     : 'DUALVAR',
    'equilibrium' : 'EQUILIBRIUM',
    'implicit'    : 'IMPLICIT',
    'max'         : 'MAX',
    'min'         : 'MIN',
    'not'         : 'NOT',
    'qvi'         : 'QVI',
    's.t.'        : 'ST',
    'vi'          : 'VI',
    'visol'       : 'VISOL'
}

tokens += list(reserved.values())

t_COMMA  = r'\,'
t_NUMBER = r'\d+'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_SQUOTE = r'\''
t_DQUOTE = r'\"'
t_DOLLAR = r'\$'

# s.t. should com first as the OR operator | matches from left to right.
def t_ID(t):
    r's\.t\. | [a-zA-Z][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value.lower(),'ID') # Check for reserved words.
    return t

def t_COMMENT(t):
    r'\*.*'
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print("\n\n    Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

t_ignore = ' \t'

# Build the lexer.
lexer = lex.lex()
