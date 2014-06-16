from eudtrg import *

vt = EUDVTable(1)
a = vt.GetVariables()[0]

main = Trigger()

DoActions(SetMemory(0x58A364, SetTo, 1234))
DoActions(a.SetNumber(200000))

loopstart, loopend = Forward(), Forward()

loopstart << NextTrigger()
EUDJumpIfNot(a.AtLeast(1), loopend)
DoActions(a.SubtractNumber(1))
EUDJump(loopstart)

loopend << Trigger()

DoActions([
	SetMemory(0x58A364, SetTo, 5678),
	SetDeaths(203151, SetTo, 0, 0)
	#SetNextPtr(main, triggerend)
])


Inject('outputmap/basemap.scx', 'outputmap/perfest.scx', main)