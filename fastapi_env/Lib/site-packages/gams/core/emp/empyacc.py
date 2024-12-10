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

# module: empyacc.py
#
# This module parses the EMP model specification and generates an EMPINFO file.
#
# Contributor: Youngdae Kim (02.17.2019)
#
# -------------------------------------------------------------------------
# Syntax
#
# empinfo   :=   EQUILIBRIUM agentlist
#              | agent
#
# agentlist :=   agentlist optagent
#              | agentlist viagent
#              | agentlist dualvar
#              | agentlist implicit
#              | agentlist visol
#              | agent
#
# agent     :=   optagent
#              | viagent
#              | qviagent
#              | dualvar
#              | implicit
#              | visol
#
# optagent :=   MAX item ST itemlist
#             | MIN item ST itemlist
#
# viagent  :=      VI  itemlist
# qviagent :=     QVI  itemlist
# dualvar  := DUALVAR  itemlist
# implicit := IMPLICIT itemlist
# visol    :=   VISOL  itemlist
#
# itemlist :=   itemlist COMMA item
#             | item
#
# item     :=   ID
#             | ID(tuple)
#             | ID(tuple)$ID(dset)
#             | ID(tuple)$(ID(dset))
#             | ID(tuple)$(NOT ID(dset))
#             | NUMBER  (this should be zero, checked by empmodel)
#
# tuple    :=   tuple COMMA setitem
#             | setitem
#
# setitem  :=   'ID'
#             | "ID"
#             | 'NUMBER'
#             | "NUMBER"
#             | ID
#
# dset     :=   dset COMMA ID
#             | ID
# -------------------------------------------------------------------------

import ply.yacc as yacc
from gams.core.emp.emplexer import tokens

class Field: pass

class EMPInfo(Field):
    def __init__(self,type,agentlist):
        self.type = type
        self.agentlist = agentlist

class Agent(Field):
    def __init__(self,type,items,obj=None):
        self.type = type
        self.items = items
        self.obj = obj

    def __repr__(self):
        if self.obj is not None:
            return self.type + ' ' + self.obj.__repr__() + ' ' + self.items.__repr__()
        else:
            return self.type + ' ' + self.items.__repr__()

    def __str__(self):
        return self.__repr__()

class Item(Field):
    def __init__(self,name,sets=None,such=None,notop=False):
        self.name = name
        self.sets = sets
        self.such = such
        self.notop = notop

    def __repr__(self):
        s  = ""

        if self.notop:
            s += "(not "

        if self.sets is not None:
            s += self.name + '(' + ','.join(filter(None,[str(s) for s in self.sets])) + ')'
        else:
            s += self.name

        if self.notop:
            s += ')'

        return s

    def __str__(self):
        return self.__repr__()

class Setitem(Field):
    def __init__(self,name,inst=False):
        self.name = name
        self.inst = inst
        self.masked = False

    def __repr__(self):
        if self.inst:
            return '"' + self.name + '"'
        else:
            return self.name

    def __str__(self):
        return self.__repr__()

    def maskedRepr(self):
        if self.masked:
            return ''

        return self.__repr__()

    def strippedRepr(self):
        if self.inst:
            return '"' + self.name + '"'
        else:
            return self.name

def p_empinfo(p):
    '''empinfo :   EQUILIBRIUM agentlist
                 | agent'''
    if p[1] == 'equilibrium':
        p[0] = EMPInfo('equilibrium',p[2])
    else:
        p[0] = EMPInfo('agent',p[1])

def p_agentlist(p):
    '''agentlist :   agentlist optagent
                   | agentlist viagent
                   | agentlist dualvar
                   | agentlist implicit
                   | agentlist visol'''
    p[0] = p[1] + p[2]

def p_agentlist_term(p):
    '''agentlist : agent'''
    p[0] = p[1]

def p_agent(p):
    '''agent :   optagent
               | qviagent
               | viagent
               | dualvar
               | implicit
               | visol'''
    p[0] = p[1]

def p_optagent(p):
    '''optagent :   MAX item ST itemlist
                  | MIN item ST itemlist'''
    p[0] = [Agent(p[1].lower(),p[4],p[2])]

def p_qviagent(p):
    'qviagent : QVI itemlist'
    p[0] = [Agent('qvi',p[2])]

def p_viagent(p):
    'viagent : VI itemlist'
    p[0] = [Agent('vi',p[2])]

def p_dualvar(p):
    'dualvar : DUALVAR itemlist'
    p[0] = [Agent('dualvar',p[2])]

def p_implicit(p):
    'implicit : IMPLICIT itemlist'
    p[0] = [Agent('implicit',p[2])]

def p_visol(p):
    'visol : VISOL itemlist'
    p[0] = [Agent('visol',p[2])]

def p_itemlist_list(p):
    'itemlist : itemlist COMMA item'
    p[0] = p[1] + p[3]

def p_itemlist_item(p):
    'itemlist : item'
    p[0] = p[1]

def p_item(p):
    'item : ID'
    p[0] = [Item(p[1])]

def p_item_tuple(p):
    'item : ID LPAREN tuple RPAREN'
    p[0] = [Item(p[1],p[3])]

def p_item_suchthat(p):
    'item :  ID LPAREN tuple RPAREN DOLLAR ID LPAREN dset RPAREN'
    p[0] = [Item(p[1],p[3],Item(p[6],p[8]))]

def p_item_suchthat_inparen(p):
    'item :  ID LPAREN tuple RPAREN DOLLAR LPAREN ID LPAREN dset RPAREN RPAREN'
    p[0] = [Item(p[1],p[3],Item(p[7],p[9]))]

def p_item_suchthat_inparen_with_not(p):
    'item :  ID LPAREN tuple RPAREN DOLLAR LPAREN NOT ID LPAREN dset RPAREN RPAREN'
    p[0] = [Item(p[1],p[3],Item(p[8],p[10],None,True))]

def p_item_zero(p):
    'item : NUMBER'
    p[0] = [Item(p[1])]

def p_tuple_list(p):
    'tuple : tuple COMMA setitem'
    p[0] = p[1] + p[3]

def p_tuple_setitem(p):
    'tuple : setitem'
    p[0] = p[1]

def p_setitem_quote(p):
    '''setitem :   SQUOTE ID SQUOTE
                 | DQUOTE ID DQUOTE
                 | SQUOTE NUMBER SQUOTE
                 | DQUOTE NUMBER DQUOTE'''
    p[0] = [Setitem(p[2],True)]

def p_setitem_set(p):
    'setitem : ID'
    p[0] = [Setitem(p[1],False)]

def p_dset_list(p):
    'dset : dset COMMA ID'
    p[0] = p[1] + [Setitem(p[3],False)]

def p_dset_id(p):
    'dset : ID'
    p[0] = [Setitem(p[1],False)]

def p_error(p):
    print("\n\n    Syntax error: " + p.value + " in line " + str(p.lineno))
    print("                  wildshot: equilibrium keyword was omitted.")
    raise Exception

# Build the parser.
parser = yacc.yacc()
