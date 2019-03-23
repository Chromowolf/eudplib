#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2019 Armoha

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
"""

from ... import core as c, ctrlstru as cs, utils as ut
from ...core.mapdata.stringmap import ForcedAddString, ApplyStringMap, GetStringMap
from ..memiof import f_getcurpl, f_setcurpl, f_wread_epd, f_dwread_epd
from .cpstr import GetStringAddr
from .cpprint import prevcp, f_cpstr_print
from .strfunc import f_strlen_epd
from .texteffect import TextFX_FadeIn, TextFX_FadeOut
from ..eudarray import EUDArray


@c.EUDFunc
def f_gettextptr():
    ret = c.EUDVariable()
    ret << 0
    for i in range(3, -1, -1):
        c.RawTrigger(
            conditions=c.MemoryX(0x640B58, c.AtLeast, 1, 2**i),
            actions=ret.AddNumber(2**i)
        )
    return ret


class StringBuffer:
    """Object for storing single modifiable string.

    Manipluating STR section is easy. :)
    You can do anything you would do with normal string with StringBuffer.
    """
    _method_template = c.Forward()
    _cpbranch = c.Forward()
    _ontrue = c.Forward()

    def __init__(self, content=None):
        """Constructor for StringBuffer

        :param content: Initial StringBuffer content / capacity. Capacity of
            StringBuffer is determined by size of this. If content is integer, then
            initial capacity and content of StringBuffer will be set to
            content(int) and empty string.

        :type content: str, bytes, int
        """
        chkt = c.GetChkTokenized()
        filler = ForcedAddString(b"Arta")
        if content is None:
            content = "\r" * 218
        elif isinstance(content, int):
            content = "\r" * content
        else:
            content = ut.u2utf8(content)
        self.capacity = len(content)
        self.StringIndex = ForcedAddString(content)
        self.epd, self.pos = c.EUDVariable(), c.EUDVariable()

        strID_fw, epd_fw = c.Forward(), c.Forward()
        ExtendedStringIndex_FW(strID_fw, epd_fw)
        strID_fw << self.StringIndex
        epd_fw << ut.EPD(self.epd.getValueAddr())

        def _fill():
            # calculate offset of buffer string
            stroffset = []
            strmap = GetStringMap()
            outindex = 2 * len(strmap._dataindextb) + 2

            for s in strmap._datatb:
                stroffset.append(outindex)
                outindex += len(s) + 1
            bufferoffset = stroffset[strmap._dataindextb[self.StringIndex - 1]]
            if bufferoffset % 4 != 0:
                strmap._datatb[strmap._dataindextb[filler - 1]] = b"Arta"[:(2 - bufferoffset) % 4]
                strmap._capacity -= 2 + bufferoffset % 4

        c.RegisterCreatePayloadCallback(_fill)

    @c.EUDMethod
    def _init_epd(self):
        if cs.EUDExecuteOnce()():
            cs.DoActions(self.epd.SetNumber(ut.EPD(GetStringAddr(self.StringIndex))))
        cs.EUDEndExecuteOnce()

    @classmethod
    def _init_template(cls):
        c.PushTriggerScope()
        cls._method_template << c.NextTrigger()
        cp = f_getcurpl()
        c.VProc(
            cp,
            cp.QueueAssignTo(ut.EPD(cls._cpbranch) + 4)
        )
        cls._cpbranch << c.RawTrigger(
            nextptr=0,
            conditions=c.Memory(0x512684, c.Exactly, 0),
            actions=c.SetNextPtr(cls._cpbranch, cls._ontrue)
        )
        cls._ontrue << c.RawTrigger(
            nextptr=cp.GetVTable(),
            actions=[
                c.SetNextPtr(cp.GetVTable(), 0),
                cp.QueueAssignTo(prevcp),
            ]
        )
        c.PopTriggerScope()

    def append(self, *args):
        self._init_epd()
        if not StringBuffer._method_template.IsSet():
            StringBuffer._init_template()
        end, ontrue = c.Forward(), c.Forward()
        c.RawTrigger(
            nextptr=StringBuffer._method_template,
            actions=[
                c.SetNextPtr(StringBuffer._cpbranch, end),
                c.SetMemory(StringBuffer._ontrue + 348, c.SetTo, ontrue),
            ]
        )
        ontrue << c.NextTrigger()
        f_setcurpl(self.pos)
        f_cpstr_print(*args)
        self.pos << f_getcurpl()
        cs.DoActions(
            [c.SetDeaths(c.CurrentPlayer, c.SetTo, 0, 0), c.SetCurrentPlayer(prevcp)]
        )
        end << c.NextTrigger()

    def insert(self, index, *args):
        self._init_epd()
        if not StringBuffer._method_template.IsSet():
            StringBuffer._init_template()
        end, ontrue = c.Forward(), c.Forward()
        c.RawTrigger(
            nextptr=StringBuffer._method_template,
            actions=[
                c.SetNextPtr(StringBuffer._cpbranch, end),
                c.SetMemory(StringBuffer._ontrue + 348, c.SetTo, ontrue),
            ]
        )
        ontrue << c.NextTrigger()
        f_setcurpl(self.epd + index)
        f_cpstr_print(*args)
        self.pos << f_getcurpl()
        f_setcurpl(prevcp)
        end << c.NextTrigger()

    def delete(self, start, length=1):
        if not StringBuffer._method_template.IsSet():
            StringBuffer._init_template()
        end, ontrue = c.Forward(), c.Forward()
        c.RawTrigger(
            nextptr=StringBuffer._method_template,
            actions=[
                c.SetNextPtr(StringBuffer._cpbranch, end),
                c.SetMemory(StringBuffer._ontrue + 348, c.SetTo, ontrue),
            ]
        )
        ontrue << c.NextTrigger()
        index = self.epd + start
        f_setcurpl(index)
        self.pos << index
        cs.DoActions(
            [
                [
                    c.SetDeaths(c.CurrentPlayer, c.SetTo, 0x0D0D0D0D, 0),
                    c.AddCurrentPlayer(1),
                ]
                for _ in range(length)
            ]
        )
        f_setcurpl(prevcp)
        end << c.NextTrigger()

    def Display(self):
        cs.DoActions(c.DisplayText(self.StringIndex))

    def DisplayAt(self, line):
        prevptr = f_gettextptr()
        cs.DoActions(c.SetMemory(0x640B58, c.Add, line))
        c.RawTrigger(
            conditions=c.Memory(0x640B58, c.AtLeast, 11),
            actions=c.SetMemory(0x640B58, c.Subtract, 11),
        )
        cs.DoActions([
            c.DisplayText(self.StringIndex),
            c.SetMemory(0x640B58, c.SetTo, prevptr)
        ])

    def Play(self):
        cs.DoActions(c.PlayWAV(self.StringIndex))

    def fadeIn(self, *args, color=None, wait=1, reset=True, tag=None):
        if not StringBuffer._method_template.IsSet():
            StringBuffer._init_template()
        end, ontrue = c.Forward(), c.Forward()
        c.RawTrigger(
            nextptr=StringBuffer._method_template,
            actions=[
                c.SetNextPtr(StringBuffer._cpbranch, end),
                c.SetMemory(StringBuffer._ontrue + 348, c.SetTo, ontrue),
            ]
        )
        ontrue << c.NextTrigger()
        f_setcurpl(self.pos)
        ret = TextFX_FadeIn(*args, color=color, wait=wait, reset=reset, tag=tag)
        self.pos << f_getcurpl()
        f_setcurpl(prevcp)
        end << c.NextTrigger()
        return ret

    def fadeOut(self, *args, color=None, wait=1, reset=True, tag=None):
        if not StringBuffer._method_template.IsSet():
            StringBuffer._init_template()
        end, ontrue = c.Forward(), c.Forward()
        c.RawTrigger(
            nextptr=StringBuffer._method_template,
            actions=[
                c.SetNextPtr(StringBuffer._cpbranch, end),
                c.SetMemory(StringBuffer._ontrue + 348, c.SetTo, ontrue),
            ]
        )
        ontrue << c.NextTrigger()
        f_setcurpl(self.pos)
        ret = TextFX_FadeOut(*args, color=color, wait=wait, reset=reset, tag=tag)
        self.pos << f_getcurpl()
        f_setcurpl(prevcp)
        end << c.NextTrigger()
        return ret

    def length(self):
        return f_strlen_epd(self.epd)


class ExtendedStringIndex_FW(c.ConstExpr):
    def __init__(self, strID, epd):
        super().__init__(self)
        self._strID = strID
        self._epd = epd

    def Evaluate(self):
        _RegisterInit(self._strID, self._epd)


_init_list = list()


def RCPC_ResetInitList():
    _init_list.clear()


c.RegisterCreatePayloadCallback(RCPC_ResetInitList)


def _RegisterInit(strID, epd):
    _init_list.append((strID, epd))


class InitBuffer(c.EUDObject):
    def __init__(self):
        super().__init__()

    def GetDataSize(self):
        if len(_init_list) % 2 == 1:
            return len(_init_list) * 6 + 6
        else:
            return len(_init_list) * 6 + 8

    def WritePayload(self, pbuf):
        pbuf.WriteDword((len(_init_list) + 2) // 2)
        for strID, _ in _init_list:
            pbuf.WriteWord(strID)
        if len(_init_list) % 2 == 1:
            pbuf.WriteWord(0xFFFF)
        else:
            pbuf.WriteDword(0xFFFFFFFF)
        for _, epd in _init_list:
            pbuf.WriteDword(epd)


def _f_initstrbuffer():
    ib = InitBuffer()
    ptr, epd, mod = c.EUDVariable(), c.EUDVariable(), c.EUDVariable()
    eib = ut.EPD(ib)
    cs.DoActions([
        ptr.SetNumber(eib + f_dwread_epd(eib)),
        epd.SetNumber(eib + 1)
    ])

    if cs.EUDInfLoop()():
        strID = f_wread_epd(epd, mod)
        cs.EUDBreakIf(strID == 0xFFFF)
        strEPD = ut.EPD(GetStringAddr(strID))
        cs.DoActions(
            [
                c.SetMemoryEPD(f_dwread_epd(ptr), c.SetTo, strEPD),
                mod.AddNumber(1),
                ptr.AddNumber(1)
            ]
        )
        c.RawTrigger(
            conditions=mod.AtLeast(2),
            actions=[
                mod.SetNumber(0),
                epd.AddNumber(1)
            ]
        )

    cs.EUDEndInfLoop()
