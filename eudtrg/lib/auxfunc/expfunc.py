 #!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 trgk

# This software is provided 'as-is', without any express or implied
# warranty. In no event will the authors be held liable for any damages
# arising from the use of this software.

# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:

#    1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
#    2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
#    3. This notice may not be removed or altered from any source
#    distribution.
#
# See eudtrg.LICENSE for more info


from eudtrg.base import *
from eudtrg.lib.baselib import *
from .muldiv import f_mul, f_div


@EUDFunc
def f_exp(a, b):
    global f_exp

    ret = EUDCreateVariables(1)

    expvt = EUDVTable(32)
    expvar = expvt.GetVariables()

    chain = [Forward() for _ in range(32)]
    ret << 1
    expvar[0] << a

    for i in range(1, 31):
        EUDJumpIf(expvar[i - 1].Exactly(0), chain[i - 1])
        EUDJumpIf(b.AtMost(2 ** i - 1), chain[i - 1])

        SetVariables(expvar[i], f_mul(expvar[i - 1], expvar[i - 1]))

        skipcond_skip = Forward()
        EUDJumpIfNot(expvar[i].Exactly(1), skipcond_skip)

        SetVariables(b, f_div(b, 2 ** i)[1])
        EUDJump(chain[i - 1])

        skipcond_skip << NextTrigger()

    for i in range(31, -1, -1):
        chain[i] << NextTrigger()

        mul_skip = Forward()
        EUDJumpIfNot(b.AtLeast(2 ** i), mul_skip)

        SeqCompute((
            (b, Subtract, 2 ** i),
            (ret, SetTo, f_mul(ret, expvar[i]))
        ))

        mul_skip << NextTrigger()

    return ret
