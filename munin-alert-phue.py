#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
munin-alert-phue.py provides extreme feedback functionality of munin alerts to a Philips Hue system.
"""

import logging, os, sys, argparse, ConfigParser, json, time, pickle
from phue import Bridge


LEVEL_NORMAL=0
LEVEL_WARNING=1
LEVEL_CRITICAL=2


def parse_args():
    """
    Parse the commandline arguments
    """
    cmdline = argparse.ArgumentParser(description='Use a Philips Hue system for munin alerting.')
    cmdline.add_argument('-c', '--config', type=argparse.FileType('r'), 
                         metavar='FILE', help="Read the configuration from FILE.")
    cmdline.add_argument('-s', '--section', default='default', 
                         metavar='SECTION', help="Use SECTION from the configuration file.")
    cmdline.add_argument('--register',
                         metavar='HOSTNAME', help="Request a username from the Bridge at HOSTNAME. "
                         "Perform registration within 30 seconds after pressing the connect button on the bridge. "
                         "The created username is written to the configuration file.")
    return cmdline.parse_args()


def load_config(fp):
    """
    Load the configuration file
    """
    config = ConfigParser.ConfigParser()
    if (fp == None):
        log.info('Reading config from ~/.munin-alert-phue.ini')
        config.read(os.path.expanduser('~/.munin-alert-phue.ini'))
    else:
        log.info('Reading config from %s', fp.name)
        config.readfp(fp)
    return config


def load_state(filename):
    """
    Load the previous munin alerting state
    """
    log.info('Loading state from %s', filename)
    try:
        if os.access(filename, os.R_OK):
            stateFile = open(filename, 'r')
            return pickle.load(stateFile)
    except:
        pass
    return {'current_status': LEVEL_NORMAL, 'last_change': time.time()}


def save_state(filename, state):
    """
    Save the provided munin alerting state
    """
    log.info('Saving state to %s', filename)
    stateFile = open(filename, 'w')
    pickle.dump(state, stateFile)


def read_munin_alert(fp):
    """
    Read a munin alert from a file pointer
    """
    return json.load(fp)


def update_state(current_state, update):
    """
    Update the current state
    """
    key = update.get('group', ''), update.get('host', ''), update.get('graph', '')
    if ('entries' not in current_state):
        current_state['entries'] = dict()
    current_state['entries'][key] = { 'warnings': update.get('warnings', []), 'criticals': update.get('criticals', []) }
    current_state['current_status'] = get_max_status(current_state)

def get_max_status(current_state):
    """
    Get the highest state
    """
    maxState = LEVEL_NORMAL
    for entry in current_state['entries'].values():
        if len(entry['criticals']) > 0:
            return LEVEL_CRITICAL                    
        elif len(entry['warnings']) > 0 and maxState < LEVEL_WARNING:
            maxState = LEVEL_WARNING
    return maxState


def update_lights(bridge_host, bridge_user, level):
    """
    Update the lights with the new state
    """
    bridge = Bridge(ip=bridge_host, username=bridge_user)
    if level == LEVEL_CRITICAL:
        bridge.set_light([1,2], {'transitiontime': 0, 'on':True, 'hue':0, 'alert':'lselect'})
    elif level == LEVEL_WARNING:
        bridge.set_light([1,2], {'transitiontime': 0, 'on':True, 'hue':53000, 'alert':'select'})
    elif level == LEVEL_NORMAL:
        bridge.set_light([1,2], {'transitiontime': 50, 'on':True, 'hue':25500})
        bridge.set_light([1,2], {'transitiontime': 3000, 'on':False})


def register(bridge_host):
    """
    Register for a user at the provided host
    """
    # TODO



if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s [%(name)s]: %(message)s', level=logging.DEBUG)
    log = logging.getLogger('munin.alert.phue')

    args = parse_args()

    if (args.register != None):
        register(args.register)
        sys.exit()

    config = load_config(args.config)


    bridge_host = config.get(args.section, 'hostname')
    bridge_user = config.get(args.section, 'username')

    if (bridge_host == None):
        log.fatal('hostname not defined in config section [%s].', args.section)
        sys.exit(1)

    if (bridge_user == None):
        log.fatal('username not defined in config section [%s]. Start with --register argument to generate a username', args.section)
        sys.exit(1)


    if (config.get(args.section, 'state_file') == None):
        stateFilename = '~/.munin-alert-phue.'+key+'.db'
    else:
        stateFilename = config.get(args.section, 'state_file')

    stateFilename = os.path.expanduser(stateFilename)
    state = load_state(stateFilename)
    old_status = state['current_status']

    munin_alert = read_munin_alert(sys.stdin)
    update_state(state, munin_alert)

    updatePulse = 5 * 60

    if (state['current_status'] != old_status
        or (state['current_status'] == LEVEL_CRITICAL and state['last_change'] < time.time() - updatePulse)
        ):
        update_lights(bridge_host, bridge_user, state['current_status'])
        state['last_change'] = time.time()

    save_state(stateFilename,state)



