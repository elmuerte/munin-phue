#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
munin-alert-phue.py provides extreme feedback functionality of munin alerts to a Philips Hue system.
"""

import logging, os, argparse, ConfigParser, json, time
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
            return json.load(stateFile)
    except:
        pass
    return {'current_status': LEVEL_NORMAL, 'last_change': time.time()}


def save_state(filename, state):
    """
    Save the provided munin alerting state
    """
    log.info('Saving state to %s', filename)
    stateFile = open(filename, 'w')
    json.dump(state, stateFile)


def update_lights(bridge_host, bridge_user):
    """
    Update the lights with the new state
    """
    bridge = Bridge(ip=bridge_host, username=bridge_user)
    # TODO


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

    # Process status update

    save_state(stateFilename,state)



