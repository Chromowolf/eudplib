#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Copyright (c) 2014 trgk

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

from eudplib import (
    core as c,
    ctrlstru as cs,
    utils as ut
)
from ..eudarray import EUDArray
from ..memiof import (
    f_dwread_epd,
    f_dwwrite_epd
)

_patchstack = EUDArray(3 * 8192)
_ps_top = c.EUDVariable()


@c.EUDFunc
def f_dwpatch_epd(addrepd, value):
    global _patchstack, _ps_top

    prev_value = f_dwread_epd(addrepd)
    f_dwwrite_epd(addrepd, value)

    _patchstack[_ps_top] = addrepd
    _ps_top += 1
    _patchstack[_ps_top] = prev_value
    _ps_top += 1


@c.EUDFunc
def f_unpatchall():
    global _ps_top
    prev_value, addrepd = c.EUDCreateVariables(2)
    if cs.EUDWhile()(_ps_top >= 1):
        _ps_top -= 1
        prev_value << _patchstack[_ps_top]
        _ps_top -= 1
        addrepd << _patchstack[_ps_top]
        f_dwwrite_epd(addrepd, prev_value)
    cs.EUDEndWhile()
