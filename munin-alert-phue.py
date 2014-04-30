#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
munin-alert-phue.py provides extreme feedback functionality of munin alerts to a Philips Hue system.
"""

import os, argparse, ConfigParser, json
from phue import Bridge

debug=False

cmdline = argparse.ArgumentParser(description='Use a Philips Hue system for munin alerting.')
cmdline.add_argument('-c', '--config', type=argparse.FileType('r'), 
                     metavar='FILE', help="Read the configuration from FILE.")
cmdline.add_argument('-s', '--section', default='default', 
                     metavar='SECTION', help="Use SECTION from the configuration file.")
cmdline.add_argument('--register',
                     metavar='HOSTNAME', help="Request a username from the Bridge at HOSTNAME. "
                     "Perform registration within 30 seconds after pressing the connect button on the bridge. "
                     "The created username is written to the configuration file.")

args = cmdline.parse_args()

config = ConfigParser.ConfigParser()
if (args.config == None):
    config.read(os.path.expanduser('~/.munin-alert-phue.ini'))
else:
    config.readfp(args.config)

bridge_host = config.get(args.section, 'hostname')
bridge_user = config.get(args.section, 'username')

if (bridge_host == None):
    raise Exception('hostname not defined in config section '+args.section)

if (bridge_user == None):
    raise Exception('username not defined in config section '+args.section+
                    '. Start with --register argument to generate a username')



# State processing

def load_state(filename):
    if os.access(filename, os.R_OK):
        stateFile = open(filename, 'r')
        return json.load(stateFile)
    else:
        return json.loads('{"current_status":"normal"}')

def save_state(filename, state):
    stateFile = open(filename, 'w')
    json.dump(state, stateFile)


if (config.get(args.section, 'state_file') == None):
    stateFilename = '~/.munin-alert-phue.'+key+'.db'
else:
    stateFilename = config.get(args.section, 'state_file')

stateFilename = os.path.expanduser(stateFilename)
state = load_state(stateFilename)
old_status = state['current_status']

# Process status update

save_state(stateFilename,state)



# Update the lights when needed
#bridge = Bridge(ip=bridge_host, username=bridge_user)

# ....

