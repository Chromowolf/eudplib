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

import itertools
from ... import core as c, ctrlstru as cs, utils as ut
from ..memiof import f_getcurpl, f_setcurpl
from .eudprint import ptr2s, epd2s
from .cpprint import f_cpstr_print, cw
from .rwcommon import br1
from ..utilf import f_getgametick


color_codes = list(range(1, 32))
color_codes.remove(0x12)  # right align
color_codes.remove(0x13)  # center align
color_v = c.EUDVariable()


@c.EUDFunc
def f_cpchar_addstr(src):
    if cs.EUDInfLoop()():
        b1 = br1.readbyte()
        cs.EUDBreakIf(b1 == 0)
        cw.writebyte(color_v)
        cw.writebyte(b1)
        if cs.EUDIf()(b1 <= 0x7F):
            cw.flushdword()
        if cs.EUDElse()():
            b2 = br1.readbyte()
            cw.writebyte(b2)
            if cs.EUDIf()(b1 <= 0xDF):  # Encode as 2-byte
                cw.flushdword()
            if cs.EUDElse()():  # 3-byte
                cw.writebyte(br1.readbyte())
            cs.EUDEndIf()
        cs.EUDEndIf()
    cs.EUDEndInfLoop()


@c.EUDFunc
def f_cpchar_adddw(number):
    skipper = [c.Forward() for _ in range(9)]
    ch = [0] * 10

    for i in range(10):  # Get digits
        number, ch[i] = c.f_div(number, 10)
        if i != 9:
            cs.EUDJumpIf(number == 0, skipper[i])

    for i in range(9, -1, -1):  # print digits
        if i != 9:
            skipper[i] << c.NextTrigger()
        cs.DoActions(
            [
                c.SetDeaths(
                    c.CurrentPlayer, c.SetTo, color_v + ch[i] * 256 + (0x0D0D3000), 0
                ),
                c.AddCurrentPlayer(1),
            ]
        )


def f_cpchar_print(*args):
    color_code = b'\x02'
    color_v << 2
    args = ut.FlattenList(args)

    for arg in args:
        encode_func = ut.u2utf8
        if isinstance(arg, bytes):
            try:
                arg = arg.decode("cp949")
                encode_func = ut.u2b
            except (UnicodeDecodeError):
                arg = arg.decode("UTF-8")
        if isinstance(arg, str):
            bytestring = b""
            for char in arg:
                char = encode_func(char)
                if ut.b2i1(char) in color_codes:
                    color_code = char
                    continue
                while len(char) < 3:
                    char = char + b"\r"
                bytestring = bytestring + color_code + char
            cs.DoActions(color_v.SetNumber(ut.b2i1(color_code)))
            if not bytestring:
                bytestring = color_code + b"\r\r\r"
            f_cpstr_print(bytestring)
        elif ut.isUnproxyInstance(arg, ptr2s):
            br1.seekoffset(arg._value)
            f_cpchar_addstr(arg._value)
        elif ut.isUnproxyInstance(arg, epd2s):
            br1.seekepd(arg._value)
            f_cpchar_addstr(arg._value)
        elif ut.isUnproxyInstance(arg, c.EUDVariable) or c.IsConstExpr(arg):
            f_cpchar_adddw(arg)
        else:
            f_cpstr_print(arg)
    cs.DoActions(c.SetDeaths(c.CurrentPlayer, c.SetTo, 0, 0))


_TextFX_dict = dict()
id_codes = "\x18\x02\x03\x04\x06\x07\x08\x0D\x0E\x0F\x10\x11\x15\x16\x17\x19\x1A\x1B\x1C\x1D\x1E\x1F"
id_gen = itertools.cycle(itertools.product(id_codes, repeat=6))


def _add_TextFX_timer(tag):
    if tag not in _TextFX_dict:
        _TextFX_dict[tag] = (c.EUDVariable(), c.EUDLightVariable(), ut.u2b("".join(next(id_gen))))


def TextFX_SetTimer(tag, modtype, value):
    _add_TextFX_timer(tag)
    timer, _, _ = _TextFX_dict[tag]
    cs.DoActions(c.SetMemory(timer.getValueAddr(), modtype, value))


@c.EUDFunc
def _remove_TextFX(o0, o1, e0, e1):
    txtPtr = c.EUDVariable()
    con_o0, con_o1, con_e0, con_e1 = [c.Forward() for _ in range(4)]
    setPtr_o, setPtr_e = c.Forward(), c.Forward()
    del_o, del_e = c.Forward(), c.Forward()
    cs.DoActions(
        [
            txtPtr.SetNumber(-1),
            c.SetMemory(con_o0 + 4, c.SetTo, ut.EPD(0x640B60)),
            c.SetMemory(con_o0 + 8, c.SetTo, o0),
            c.SetMemory(con_o1 + 4, c.SetTo, ut.EPD(0x640B64)),
            c.SetMemory(con_o1 + 8, c.SetTo, o1),
            c.SetMemory(setPtr_o + 8, c.SetTo, 0),
            c.SetMemory(del_o + 4, c.SetTo, ut.EPD(0x640B60)),
            c.SetMemory(con_e0 + 4, c.SetTo, ut.EPD(0x640C38)),
            c.SetMemory(con_e0 + 8, c.SetTo, e0),
            c.SetMemory(con_e1 + 4, c.SetTo, ut.EPD(0x640C3C)),
            c.SetMemory(con_e1 + 8, c.SetTo, e1),
            c.SetMemory(setPtr_e + 8, c.SetTo, 1),
            c.SetMemory(del_e + 4, c.SetTo, ut.EPD(0x640C38)),
        ]
    )
    if cs.EUDLoopN()(6):
        c.RawTrigger(
            conditions=[
                con_o0 << c.Memory(0x640B60, c.Exactly, 0),
                con_o1 << c.MemoryX(0x640B64, c.Exactly, 0, 0xFFFF),
            ],
            actions=[
                setPtr_o << txtPtr.SetNumber(0),
                del_o << c.SetMemory(0x640B60, c.SetTo, 0),
            ]
        )
        c.RawTrigger(
            actions=[
                c.SetMemory(con_o0 + 4, c.Add, 109),
                c.SetMemory(con_o1 + 4, c.Add, 109),
                c.SetMemory(setPtr_o + 8, c.Add, 2),
                c.SetMemory(del_o + 4, c.Add, 109),
            ]
        )
    cs.EUDEndLoopN()
    if cs.EUDLoopN()(5):
        c.RawTrigger(
            conditions=[
                con_e0 << c.MemoryX(0x640C38, c.Exactly, 0, 0xFFFF0000),
                con_e1 << c.Memory(0x640C3C, c.Exactly, 0),
            ],
            actions=[
                setPtr_e << txtPtr.SetNumber(1),
                del_e << c.SetMemoryX(0x640C38, c.SetTo, 0, 0xFFFF0000),
            ]
        )
        c.RawTrigger(
            actions=[
                c.SetMemory(con_e0 + 4, c.Add, 109),
                c.SetMemory(con_e1 + 4, c.Add, 109),
                c.SetMemory(setPtr_e + 8, c.Add, 2),
                c.SetMemory(del_e + 4, c.Add, 109),
            ]
        )
    cs.EUDEndLoopN()
    return txtPtr


def TextFX_Remove(tag):
    _add_TextFX_timer(tag)
    _, _, identifier = _TextFX_dict[tag]
    o0 = ut.b2i4(identifier[0:4])
    o1 = ut.b2i2(identifier[4:6])
    e0 = ut.b2i4(b"\0\0" + identifier[0:2])
    e1 = ut.b2i4(identifier[2:6])
    return _remove_TextFX(o0, o1, e0, e1)


_check_cp = c.Forward()
_is_below_start = None
_cpbelowbuffer = c.EUDLightVariable()


def _is_CP_less_than_start(actions):
    global _is_below_start
    if _is_below_start is None:
        c.PushTriggerScope()
        _is_below_start = c.RawTrigger(
            conditions=[
                _check_cp << c.Memory(0x6509B0, c.AtMost, 1)
            ],
            actions=_cpbelowbuffer.SetNumber(1)
        )
        c.PopTriggerScope()
    _next = c.Forward()
    c.RawTrigger(
        nextptr=_is_below_start,
        actions=[actions]
        + [_cpbelowbuffer.SetNumber(0), c.SetNextPtr(_is_below_start, _next)],
    )
    _next << c.NextTrigger()


def R2L(colors, colors_dict={}):
    try:
        _f = colors_dict[colors]
    except (KeyError):

        @c.EUDFunc
        def _f():
            _jump, _isend, _end = [c.Forward() for _ in range(3)]
            ret = c.EUDVariable()
            _is_CP_less_than_start([ret.SetNumber(1), c.SetNextPtr(_isend, _jump)])
            _isend << c.RawTrigger(
                conditions=_cpbelowbuffer.Exactly(1),
                actions=[ret.SetNumber(0), c.SetNextPtr(_isend, _end)],
            )
            _jump << c.NextTrigger()
            for color in reversed(colors):
                _is_CP_less_than_start([])
                c.RawTrigger(
                    conditions=_cpbelowbuffer.Exactly(0),
                    actions=[
                        c.SetDeathsX(c.CurrentPlayer, c.SetTo, color, 0, 0xFF),
                        c.AddCurrentPlayer(-1),
                    ],
                )
            _end << c.NextTrigger()
            return ret

        colors_dict[colors] = _f
    return _f()


def TextFX_FadeIn(*args, color=None, wait=1, reset=True, tag=None):
    """Print multiple string / number and apply color from Left To Right

    Keyword arguments:
    color -- tuple of color codes (default 0x03, 0x04, 0x05, 0x14)
    wait  -- time interval between effect (default 1)
    reset -- automatically reset when didn't run for a moment (default True)
    tag   -- internal tag and identifier (default: vargs)
    """
    if color is None:
        color = (0x03, 0x04, 0x05, 0x14)
    if tag is None:
        if len(args) == 1:
            tag = args[0]
        else:
            tag = args

    _add_TextFX_timer(tag)
    timer, counter, identifier = _TextFX_dict[tag]

    start = f_getcurpl()
    c.VProc(
        start,
        [
            c.SetMemory(_check_cp + 8, c.SetTo, 1),
            start.QueueAddTo(ut.EPD(_check_cp + 8))
        ]
    )
    f_cpstr_print(identifier)
    f_cpchar_print(*args)
    f_setcurpl(start + (3 - len(color)))

    if reset is True:
        check_gametick = c.Forward()
        if cs.EUDIf()([check_gametick << c.Memory(0x57F23C, c.AtLeast, 0)]):
            gametick = f_getgametick()
            c.VProc(
                gametick,
                [
                    timer.SetNumber(0),
                    c.SetMemory(check_gametick + 8, c.SetTo, 1),
                    gametick.QueueAddTo(ut.EPD(check_gametick) + 2),
                ],
            )
        cs.EUDEndIf()

    _end = c.Forward()
    _is_finished, _draw_color = c.Forward(), c.Forward()
    ret = c.EUDVariable()

    cs.DoActions([
        counter.AddNumber(1),
        [c.SetMemory(check_gametick + 8, c.Add, 1) if reset is True else []],
        ret.SetNumber(1),
        c.SetNextPtr(_is_finished, _draw_color),
        c.AddCurrentPlayer(timer),
    ])
    _is_finished << c.RawTrigger(
        conditions=[
            c.Deaths(c.CurrentPlayer, c.Exactly, 0, 0),
            timer.AtLeast(2 + len(color)),
        ],
        actions=[
            ret.SetNumber(0),
            counter.SetNumber(0),
            c.SetNextPtr(_is_finished, _end),
        ],
    )
    _draw_color << c.RawTrigger(actions=c.AddCurrentPlayer(len(color) - 1))
    R2L(color)
    c.RawTrigger(
        conditions=counter.AtLeast(max(wait, 1)),
        actions=[counter.SetNumber(0), timer.AddNumber(1)],
    )
    _end << c.NextTrigger()
    return ret


def TextFX_FadeOut(*args, color=None, wait=1, reset=True, tag=None):
    """Print multiple string / number and apply color from Left To Right

    Keyword arguments:
    color -- tuple of color codes (default 0x03, 0x04, 0x05, 0x14)
    wait  -- time interval between effect (default 1)
    reset -- automatically reset when didn't run for a moment (default True)
    tag   -- internal tag and identifier (default: vargs)
    """
    if color is None:
        color = (0x03, 0x04, 0x05, 0x14)
    if tag is None:
        if len(args) == 1:
            tag = args[0]
        else:
            tag = args

    _add_TextFX_timer(tag)
    timer, counter, identifier = _TextFX_dict[tag]

    start = f_getcurpl()
    c.VProc(
        start,
        [
            c.SetMemory(_check_cp + 8, c.SetTo, 1),
            start.QueueAddTo(ut.EPD(_check_cp + 8))
        ]
    )
    f_cpstr_print(identifier)
    f_cpchar_print(*args)

    if reset is True:
        check_gametick = c.Forward()
        if cs.EUDIf()([check_gametick << c.Memory(0x57F23C, c.AtLeast, 0)]):
            gametick = f_getgametick()
            c.VProc(
                gametick,
                [
                    timer.SetNumber(0),
                    c.SetMemory(check_gametick + 8, c.SetTo, 1),
                    gametick.QueueAddTo(ut.EPD(check_gametick) + 2),
                ],
            )
        cs.EUDEndIf()

    cs.DoActions([
        counter.AddNumber(1),
        [c.SetMemory(check_gametick + 8, c.Add, 1) if reset is True else []],
        c.AddCurrentPlayer((len(color) - 1) - timer),
    ])
    ret = R2L(color)
    c.RawTrigger(conditions=ret.Exactly(0), actions=counter.SetNumber(0))
    c.RawTrigger(
        conditions=counter.AtLeast(max(wait, 1)),
        actions=[counter.SetNumber(0), timer.AddNumber(1)],
    )
    return ret
