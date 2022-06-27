
#!/usr/bin/python
"""
A minimal utility to send structured commands to the BPS board using Java BPS network utility
"""

import sys
import os
import re
sys.path.insert(0, '/home/km3net/applications/bps-software/host/python/codegen')


import commands
from utils import mls
from analogvariables import *
from bpsentities.descriptors import PayloadFieldEnum, PayloadFieldU8, PayloadFieldU16, PayloadFieldU32
from commutils import *
import os
import time
from datetime import datetime

#from redistimeseries.client import Client as RedisTimeSeries
#from redis import Redis

ASK_CONFIRM = False
SHOW_SENT_DATA = True
SHOW_RECEIVED_DATA = False

db_trans_map = {

    "MON_5V_I_MAXVALUE": "bps_5V_max_current",
    "MON_LBL_I_MAXVALUE": "lbl_max_current",
    "MON_DU_I_MAXVALUE" : "bps_du_max_current",
    "MON_DU_IRTN_MAXVALUE" : "bps_du_max_return_current",
    "MON_BPS_V_MAXVALUE" : "bps_V_max",
    "MON_HYDRO_I_MAXVALUE" : "bps_hydro_I_max",
    "MON_THEATSINK_MAXVALUE" : "bps_mon_max_temp_heatsink",
    "MON_TBOARD_MAXVALUE" : "bps_mon_max_temp_board",
    "MON_5V_I_MEAN":"bps_5V_mean_current",
    "MON_LBL_I_MEAN":"lbl_mean_current",
    "MON_DU_I_MEAN":"bps_du_mean_current",
    "MON_DU_IRTN_MEAN":"bps_du_mean_return_current",
    "MON_BPS_V_MEAN":"bps_V_mean",
    "MON_HYDRO_I_MEAN":"bps_hydro_mean_current",
    "MON_THEATSINK_MEAN":"bps_mon_mean_temp_heatsink",
    "MON_TBOARD_MEAN":"bps_mon_mean_temp_board",

}

bps_items= [
    "bps_5V_max_current",
    "bps_5V_max_current_A",
    "lbl_max_current",
    "lbl_max_current_A",
    "bps_du_max_current",
    "bps_du_max_current_A",
    "bps_du_max_return_current",
    "bps_du_max_return_current_A",
    "bps_V_max",
    "bps_V_max_V",
    "bps_hydro_I_max",
    "bps_hydro_I_max_A",
    "bps_mon_max_temp_heatsink",
    "bps_mon_max_temp_heatsink_AU",
    "bps_mon_max_temp_board",
    "bps_mon_max_temp_board_C",
    "bps_5V_mean_current",
    "bps_5V_mean_current_A",
    "lbl_mean_current",
    "lbl_mean_current_A",
    "bps_du_mean_current",
    "bps_du_mean_current_A",
    "bps_du_mean_return_current",
    "bps_du_mean_return_current_A",
    "bps_V_mean",
    "bps_V_mean_V",
    "bps_hydro_mean_current",
    "bps_hydro_mean_current_A",
    "bps_mon_mean_temp_heatsink",
    "bps_mon_mean_temp_heatsink_AU",
    "bps_mon_mean_temp_board",
    "bps_mon_mean_temp_board_C"
]

class bps_dataset:

    def __init__(self,dom_id,du_id):

        self.dom_id=dom_id
        self.ip_addr="10.0.{}.100".format(du_id)
        self.du_nick="DU{}".format(du_id)
        self.du_id=du_id

        # all values start from 0
        self.bpsvalues = {el:0 for el in bps_items }

    def print_all(self):
        print ("IP {} DOMID {}".format(self.ip_addr,self.du_id))
        for (k,val) in self.bpsvalues.items():
            print ("{}->{}".format(k,val))

    def print_singleval(self,label):
        if label not in bps_items:
            print ("Error: {} is unknown".format(label))
        else:
            print ("{}".format(self.bpsvalues[label]))

    def redis_push(self):
        pass

    def data_refresh(self,data_type):

        CLB_IPADDR=self.ip_addr

        JSCRIPTFMT = './execute.sh BPSCmd {} [REQCODE] [RESPCODE] [RESPLEN] [REQPAYLOAD]'.format(CLB_IPADDR)

        if data_type == "mean":
            command_name="SENSOR_AVERAGE_GETALL"
        elif data_type == "max":
            command_name="SENSOR_MAXVALUES_GETALL"
        else:
            print ("ERROR: data type {} is unknown".format(data_type))

        #command_name = sys.argv[1].upper()
        filtered_commands = [command for command in commands.entries() if command.name.startswith(command_name)]

        # if len(filtered_commands) == 0:
        #     print 'No command found with name starting with: "{}"'.format(command_name)
        # elif len(filtered_commands) != 1:
        #     print 'More than one command found with name starting with: "{}":'.format(command_name)
        #     for command in filtered_commands:
        #         print '    {}'.format(command.name)
        #     sys.exit(0)

        # get the wanted command
        command = filtered_commands[0]

        # expected number of request fields:
        req_field_count = len(command.request_payload)

        # if len(sys.argv) != req_field_count + 2:
        #     print 'Number of request payload fields not correct. The {} command expects {} fields; {} where given.'.format(command.name, len(command.request_payload), len(sys.argv) - 2)
        #     sys.exit(0)

        # prepare the payload
        payload_data = list()
        payload_field_values = list()
        idx = 2
        for field in command.request_payload:
            val = int(sys.argv[idx])
            payload_field_values.append(val)
            if isinstance(field, PayloadFieldU8):
                assert val < 2**8, 'Too big value for uint8'
                payload_data.append(val)
            elif isinstance(field, PayloadFieldU16):
                assert val < 2 ** 16, 'Too big value for uint16'
                payload_data.append((val >> 8) & 0xff)
                payload_data.append(val & 0xff)
            elif isinstance(field, PayloadFieldU32):
                assert val < 2 ** 32, 'Too big value for uint32'
                payload_data.append((val >> 24) & 0xff)
                payload_data.append((val >> 16) & 0xff)
                payload_data.append((val >> 8) & 0xff)
                payload_data.append(val & 0xff)
            elif isinstance(field, PayloadFieldEnum):
                assert val < 2 ** 8, 'Too big value for enum'
                payload_data.append(val)
            else:
                assert False, 'Unmanaged type {}'.format(field.__class__.__name__)
            idx += 1

        if debug:
            print ("Sending packet:")
            print ('    Command code: {} (raw data: {})'.format(command.name, command.request_code))
            #                      print '    Payload data: {} (raw data: {})'.format(payload_field_values, payload_data)
            print ('    Request payload:')
            idx = 0
            for field in command.request_payload:
                print ('        {} = {}'.format(field.name, payload_field_values[idx]))
                idx += 1

        if ASK_CONFIRM:
            if not ask_confirm():
                print ("Operation aborted by user")
                sys.exit()

        jcmd = JSCRIPTFMT
        jcmd = jcmd.replace('[REQCODE]', str(command.request_code))
        jcmd = jcmd.replace('[RESPCODE]', str(command.response_code))
        jcmd = jcmd.replace('[RESPLEN]', str(2 * command.get_response_payload_len()))

        if not payload_data:
            jcmd = jcmd.replace('[REQPAYLOAD]', 'null')
        else:
            pl = ''
            for b in payload_data:
                # print b.__class__
                n0, n1 = uint8_to_nibbles(b)
                pl += chr(n1)
                pl += chr(n0)
            jcmd = jcmd.replace('[REQPAYLOAD]', pl)

        if debug: print ('Executing command: "{}"'.format(jcmd))
        r = mydirtyexec(jcmd)
        if debug: print ('Response:"{}"'.format(r.strip()))

        # convert nibbles to bytes
        payload_bytes = list()
        for k in range(0, len(r)-1, 2):
            d = 16 * int(r[k], 16) + int(r[k+1], 16)
            payload_bytes.append(d)

        byte_idx = 0
        rawvalues = list();
        for field in command.response_payload:
            value = -1
            if isinstance(field, PayloadFieldU8):
                value = payload_bytes[byte_idx]
                rawvalues.append(value)
                byte_idx += 1
            elif isinstance(field, PayloadFieldU16):
                value = payload_bytes[byte_idx] << 8
                value += payload_bytes[byte_idx+1]
                rawvalues.append(value)
                byte_idx += 2
            elif isinstance(field, PayloadFieldU32):
                value = payload_bytes[byte_idx] << 24
                value += payload_bytes[byte_idx+1] << 16
                value += payload_bytes[byte_idx+2] << 8
                value += payload_bytes[byte_idx+3]
                rawvalues.append(value)
                byte_idx += 4
            elif isinstance(field, PayloadFieldEnum):
                value = field.get_value_by_index(payload_bytes[byte_idx])
                rawvalues.append(value)
                byte_idx += 1
            else:
                assert False, 'Unmanaged type {}'.format(field.__class__.__name__)

        convertedvals = getconvertedvals(command, rawvalues)

        field_idx = 0
        for field in command.response_payload:
            if field.name not in db_trans_map:
                continue
            ##s = '        {} = {} '.format(field.name, rawvalues[field_idx])
            #s = '{},{}'.format(db_trans_map[field.name], rawvalues[field_idx])
            label=db_trans_map[field.name]
            self.bpsvalues[label]=rawvalues[field_idx]
            if convertedvals:
                if convertedvals[field_idx][0]:
                    #sc = '{}_{},{:0.3}'.format(db_trans_map[field.name],convertedvals[field_idx][1], convertedvals[field_idx][0])
                    label="{}_{}".format(db_trans_map[field.name],convertedvals[field_idx][1])
                    self.bpsvalues[label]="{:0.3}".format(convertedvals[field_idx][0])
                    #print sc
            #print s
            field_idx += 1


def ask_confirm():
    answer = ""
    while answer not in ["y", "n"]:
        answer = raw_input("Confirm [Y/N]? ").lower()
    return answer == "y"


def mydirtyexec(_cmd):
    # like it dirty...
    os.system(_cmd + ' > __tmp')
    return open('__tmp', 'r').read()

def getconvertedvals(command, fields):
    vals = list()

    # the pork way (with great respect for porks)
    # if command.name == 'SENSOR_GET_SINGLE':
    #     vn = fields[0]
    #     converter = None
    #     if vn == 'MON_5V_I':
    #         converter = channel2current_MON_5V_I
    #         units = 'A'
    #     elif vn in ['MON_LBL_I', 'MON_HYDRO_I']:
    #         converter = channel2current_12V
    #         units = 'A'
    #     elif vn in ['MON_DU_I', 'MON_DU_IRTN']:
    #         converter = channel2current_MON_DU_I
    #         units = 'A'
    #     elif vn == 'MON_BPS_V':
    #         converter = channel2voltage_MON_BPS_V
    #         units = 'V'
    #     elif vn == 'MON_THEATSINK':
    #         converter = channel2temperature_THEATSINK
    #         units = 'V (A.U.)'
    #     elif vn == 'MON_TBOARD':
    #         converter = channel2temperature_TBOARD
    #         units = 'C'
    #     else:
    #         pass
    #     if converter:
    #         vals.append(['',''])
    #         vals.append([converter(fields[1]), units]) # VALUE
    #         vals.append([converter(fields[2]), units]) # OFFSET
    #         vals.append([converter(fields[3]), units]) # MAXVALUE
    #         vals.append([converter(fields[4]), units]) # MEANVALUE
    if command.name in ['SENSOR_VALUES_GETALL', 'SENSOR_AVERAGE_GETALL', 'SENSOR_OFFSETS_GETALL', 'SENSOR_MAXVALUES_GETALL']:
        vals.append([channel2current_MON_5V_I(fields[0]), 'A']) # MON_5V_I_MEAN
        vals.append([channel2current_12V(fields[1]), 'A']) # MON_LBL_I_MEAN
        vals.append([channel2current_MON_DU_I(fields[2]), 'A']) # MON_DU_I_MEAN
        vals.append([channel2current_MON_DU_I(fields[3]), 'A']) # MON_DU_IRTN_MEAN
        vals.append([channel2voltage_MON_BPS_V(fields[4]), 'V']) # MON_BPS_V_MEAN
        vals.append([channel2current_12V(fields[5]), 'A']) # MON_HYDRO_I_MEAN
        ## vals.append([channel2temperature_THEATSINK(fields[6]), 'V (A.U.)'])
        vals.append([channel2temperature_THEATSINK(fields[6]), 'AU'])
         # MON_THEATSINK_MEAN
        vals.append([channel2temperature_TBOARD(fields[7]), 'C']) # MON_TBOARD_MEAN

    return vals

if __name__ == '__main__':
    # command line options
    # example
    # python sendcommand.py COMMAND_NAME payload0 payload1 ...
    # COMMAND_NAME is the human readable name of the command (e.g.: )

    # redirect stdout to null in order to avoid the warnings during object creation
    stdout = sys.stdout
    f = open(os.devnull, 'w')
    sys.stdout = f

    switch_list = commands.SwitchList()
    analog_variable_list = commands.AnalogVariableList()
    digital_variable_list = commands.DigitalVariableList()
    user_pin_list = commands.UserPinList()
    commands = commands.CommandList(switch_list, analog_variable_list, digital_variable_list, user_pin_list)
    debug=True

    # restore normal stdout
    sys.stdout = stdout

    # if len(sys.argv) <= 1:
    #     print "Command code missing"
    #     sys.exit(0)

    bps_map_file=""
    #DET_N=sys.argv[1]
    #RUN_NUMBER = sys.argv[2]
    TIMESTAMP=int(time.time())
    #redis_host=sys.argv[4]
    outfile="/home/km3net/applications/bps-test/csv_bps/bpsout{}.csv".format(TIMESTAMP)
    #sys.argv.pop(3)


    #if debug: print ("Detector {} Run Number{} timestamp {} redis host".format(DET_N,RUN_NUMBER,TIMESTAMP,redis_host))
    #rts = RedisTimeSeries(host=redis_container,port=6379)

    if len(sys.argv) > 5:
        bps_map_file=sys.argv[5]
        #sys.argv.pop(1)
    else:
        bps_map_file="/home/km3net/applications/bps-test/bps-map.txt"

    # use a dict, insteed that a list, to eventually address a specific du
    BPS_dict={}

    with open(bps_map_file) as fp:
        lines = fp.readlines()
        for line in lines:
            linesplit=line.split(",")
        du_nick=linesplit[0]
            dom_id=linesplit[1][:-1]
            du_id=du_nick[2:5]
            if debug: print (" found nick {} domid {} du_id {}".format( du_nick,dom_id,du_id))
            bps_new=bps_dataset(dom_id,du_id)
            BPS_dict[du_id]=bps_new
    
    #this is needed for the cronjob in order to execute the commands as if it was inside this directory, otherwise it would not load the BPSClass module
    os.chdir("/home/km3net/applications/bps-test")
    
    for bps in BPS_dict.values():
         bps.data_refresh("max")
         bps.data_refresh("mean")
         print ("{} BPS is refreshed".format(bps.du_nick))
         #bps.print_all()

    fout=open(outfile,'w+')
    head_line="{},{}".format("source","machine_time")
    for label in bps_items:
        head_line+=",{}".format(label)
        #print (first_line)
    head_line+="\n"
    fout.write(head_line)

    for bps in BPS_dict.values():
        bps_line="{},{}".format(bps.du_id,TIMESTAMP)
        for label in bps_items:
            bps_line+=",{}".format(bps.bpsvalues[label])
            #print(line)

        bps_line+="\n"
        fout.write(bps_line)

    fout.close()

    sys.exit(0)
