# Copyright(C) 2014 by Abe developers.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/agpl.html>.

from .Sha256NmcAuxPowChain import Sha256NmcAuxPowChain
from . import SCRIPT_TYPE_UNKNOWN
from ..deserialize import opcodes, match_decoded

NAME_NEW         = opcodes.OP_1
NAME_FIRSTUPDATE = opcodes.OP_2
NAME_UPDATE      = opcodes.OP_3

SCRIPT_TYPE_NAME_NEW = 7
SCRIPT_TYPE_NAME_FIRSTUPDATE = 8
SCRIPT_TYPE_NAME_UPDATE = 9

NAME_NEW_TEMPLATE = [NAME_NEW, opcodes.OP_PUSHDATA4, opcodes.OP_2DROP]
NAME_FIRSTUPDATE_TEMPLATE = [NAME_FIRSTUPDATE, opcodes.OP_PUSHDATA4, opcodes.OP_PUSHDATA4, opcodes.OP_PUSHDATA4, opcodes.OP_2DROP, opcodes.OP_2DROP]
NAME_UPDATE_TEMPLATE = [NAME_UPDATE, opcodes.OP_PUSHDATA4, opcodes.OP_PUSHDATA4, opcodes.OP_2DROP, opcodes.OP_DROP]

class Namecoin(Sha256NmcAuxPowChain):
    """
    Namecoin represents name operations in transaction output scripts.
    """
    def __init__(chain, **kwargs):
        chain.name = 'Namecoin'
        chain.code3 = 'NMC'
        chain.address_version = '\x34'
        chain.magic = '\xf9\xbe\xb4\xfe'
        Sha256NmcAuxPowChain.__init__(chain, **kwargs)

    _drops = (opcodes.OP_NOP, opcodes.OP_DROP, opcodes.OP_2DROP)

    def parse_decoded_txout_script(chain, decoded):
        start = 0
        pushed = 0

        start = 0

        if match_decoded(decoded[0:len(NAME_NEW_TEMPLATE)], NAME_NEW_TEMPLATE):
            start = len(NAME_NEW_TEMPLATE)
            data = []
            script_type = SCRIPT_TYPE_NAME_NEW
        elif match_decoded(decoded[0:len(NAME_FIRSTUPDATE_TEMPLATE)], NAME_FIRSTUPDATE_TEMPLATE):
            start = len(NAME_FIRSTUPDATE_TEMPLATE)
            name = decoded[1][1]
            newtx_hash = decoded[2][1]
            value = decoded[3][1]
            data = [name, value, newtx_hash]
            script_type = SCRIPT_TYPE_NAME_FIRSTUPDATE
        elif match_decoded(decoded[0:len(NAME_UPDATE_TEMPLATE)], NAME_UPDATE_TEMPLATE):
            start = len(NAME_UPDATE_TEMPLATE) 
            name = decoded[1][1]
            value = decoded[2][1]
            data = [name, value]
            script_type = SCRIPT_TYPE_NAME_UPDATE

        script_type2, data2 = Sha256NmcAuxPowChain.parse_decoded_txout_script(chain, decoded[start:])

        if start > 0:
            fullData = [[script_type2, data2]] + data
            return script_type, fullData
        else:
            return script_type2, data2


    datadir_conf_file_name = "namecoin.conf"
    datadir_rpcport = 8336
