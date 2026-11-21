"""
Compatibility rules of the PC builder.

The rules work with the parts of a build: a dict {slot: part}, for example
{'cpu': <CPU>, 'motherboard': <Motherboard>}. A part is any object with the fields of
the model (socket, form_factor, ...), so the rules can be tested without a database.

Each rule looks at the parts it needs and says what is wrong. A rule is skipped
while one of its parts is not chosen yet.
"""
import re
from dataclasses import dataclass

SLOTS = ('cpu', 'motherboard', 'ram', 'gpu', 'storage', 'psu', 'case', 'cooling')

# The slot -> the model (name of the class in goods.models) that fills it
SLOT_MODELS = {
    'cpu': 'CPU',
    'motherboard': 'Motherboard',
    'ram': 'RAM',
    'gpu': 'GraphicsCard',
    'storage': 'HardDrive',
    'psu': 'PowerSupply',
    'case': 'Case',
    'cooling': 'CoolingSystem',
}


@dataclass(frozen=True)
class Problem:
    slots: tuple  # the slots that do not fit together
    message: str


def normalize(text):
    """'LGA 1700', 'lga1700' and 'LGA-1700' are the same socket."""
    return re.sub(r'[\s\-_]', '', str(text)).upper()


# --- form factors ------------------------------------------------------------

FORM_FACTOR_ALIASES = {'MATX': 'MICROATX', 'MICROATX': 'MICROATX', 'MINIITX': 'MINIITX', 'ATX': 'ATX'}

# The motherboard form factors that a case takes. The case names in the database
# are not exact form factors ("ATX mid-tower"), so they are listed here.
# "Compact tower" is an assumption: we take it as a case for Micro ATX and smaller.
CASE_TAKES = {
    'ATXFULLTOWER': {'ATX', 'MICROATX', 'MINIITX'},
    'ATXMIDTOWER': {'ATX', 'MICROATX', 'MINIITX'},
    'COMPACTTOWER': {'MICROATX', 'MINIITX'},
    'MINIITX': {'MINIITX'},
}


def board_form_factor(text):
    return FORM_FACTOR_ALIASES.get(normalize(text))


def case_takes(case_form_factor):
    """The set of motherboard form factors for this case, or None if the case is unknown."""
    return CASE_TAKES.get(normalize(case_form_factor))


# --- cooling: the sockets in the text "Intel LGA 1700, 1200; AMD AM4, AM5" -------

def cooling_sockets(compatibility):
    """
    "Intel LGA 1700, 1200, 1150; AMD AM4, AM5" -> {'LGA1700', 'LGA1200', 'LGA1150', 'AM4', 'AM5'}
    After a socket like "LGA 1700" the bare numbers belong to the same family (LGA).
    """
    sockets = set()
    for brand_group in str(compatibility).split(';'):
        family = None
        for token in brand_group.split(','):
            token = re.sub(r'\b(Intel|AMD)\b', '', token, flags=re.IGNORECASE).strip()
            named = re.fullmatch(r'([A-Za-z]+)\s*(\d\w*)', token)
            if named:
                family = named.group(1)
                sockets.add(normalize(family + named.group(2)))
            elif re.fullmatch(r'\d\w*', token) and family:
                sockets.add(normalize(family + token))
    return sockets


# --- power -------------------------------------------------------------------

BASE_LOAD_W = 150  # motherboard, memory, drives, fans
PSU_MARGIN = 1.2  # a power supply should have 20% more than the load
CONNECTOR_W = {6: 75, 8: 150, 12: 300, 16: 450}  # what a graphics card takes by its connector
UNKNOWN_GPU_W = 150


def gpu_power(gpu):
    """The power of a graphics card (estimate) from the text "8-pin x 2"."""
    total = 0
    for pins, count in re.findall(r'(\d+)-pin\s*x\s*(\d+)', str(gpu.power_connector)):
        total += CONNECTOR_W.get(int(pins), 0) * int(count)
    return total or UNKNOWN_GPU_W


def estimated_load(parts):
    load = BASE_LOAD_W
    if 'cpu' in parts:
        load += parts['cpu'].thermal_design_power
    if 'gpu' in parts:
        load += gpu_power(parts['gpu'])
    return load


# --- rules -------------------------------------------------------------------

def _socket_rule(parts):
    cpu, board = parts['cpu'], parts['motherboard']
    if normalize(cpu.socket) != normalize(board.socket):
        return f'The processor socket is {cpu.socket}, but the motherboard socket is {board.socket}.'


def _memory_rule(parts):
    ram, board = parts['ram'], parts['motherboard']
    if normalize(ram.type) != normalize(board.memory_type):
        return f'The memory is {ram.type}, but the motherboard needs {board.memory_type}.'


def _case_rule(parts):
    board, case = parts['motherboard'], parts['case']
    takes = case_takes(case.form_factor)
    if takes is None:
        return f'The case type "{case.form_factor}" is not known to the builder.'
    if board_form_factor(board.form_factor) not in takes:
        return f'The {board.form_factor} motherboard does not fit into the "{case.form_factor}" case.'


def _cooling_rule(parts):
    cpu, cooling = parts['cpu'], parts['cooling']
    if normalize(cpu.socket) not in cooling_sockets(cooling.compatibility):
        return f'The cooler does not support the {cpu.socket} socket.'


def _power_rule(parts):
    needed = round(estimated_load(parts) * PSU_MARGIN)
    if parts['psu'].power < needed:
        return f'The power supply is {parts["psu"].power} W, but about {needed} W is needed.'


# (the slots the rule needs, the rule). A rule returns a message or None.
RULES = [
    (('cpu', 'motherboard'), _socket_rule),
    (('ram', 'motherboard'), _memory_rule),
    (('motherboard', 'case'), _case_rule),
    (('cpu', 'cooling'), _cooling_rule),
    # the power depends on the processor and the graphics card, if they are chosen
    (('psu',), _power_rule),
]
POWER_SLOTS = ('psu', 'cpu', 'gpu')


def find_problems(parts):
    """All the problems of a build (a list of Problem). An empty list means the build is fine."""
    problems = []
    for slots, rule in RULES:
        if all(slot in parts for slot in slots):
            message = rule(parts)
            if message:
                # the power problem is about every part that takes power
                involved = tuple(s for s in POWER_SLOTS if s in parts) if rule is _power_rule else slots
                problems.append(Problem(involved, message))
    return problems


def check_candidate(slot, candidate, parts):
    """
    Why a part does not fit the build: a list of messages (empty if it fits).
    The part that is in this slot now is not counted: the candidate would replace it.
    """
    trial = {**parts, slot: candidate}
    return [problem.message for problem in find_problems(trial) if slot in problem.slots]
