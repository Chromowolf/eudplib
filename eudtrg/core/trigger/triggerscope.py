from ..utils import CreateBlock, GetLastBlock, PopBlock
from ..allocator import Forward


def PushTriggerScope():
    CreateBlock('triggerscope', {
        'nexttrigger_list': []
    })
    return True  # Allow `if PushTriggerScope()` syntax for indent


def NextTrigger():
    fw = Forward()
    nt_list = GetLastBlock('triggerscope')[1]['nexttrigger_list']
    nt_list.append(fw)
    return fw


def _RegisterTrigger(trg):
    nt_list = GetLastBlock('triggerscope')[1]['nexttrigger_list']
    for fw in nt_list:
        fw << trg
    nt_list.clear()


def PopTriggerScope():
    nt_list = PopBlock('triggerscope')[1]['nexttrigger_list']
    for fw in nt_list:
        fw << 0
