#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Munin Alert Phue - Munin alerts updating Philips Hue lights.
# https://github.com/elmuerte/munin-phue 
# Copyright (C) 2014 Michiel Hendriks <elmuerte@drunksnipers.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
munin-alert-phue.py provides extreme feedback functionality of munin alerts to a Philips Hue system.
"""

from __future__ import print_function
import logging, os, sys, argparse, ConfigParser, json, time, pickle
from phue import Bridge
from lockfile import FileLock

LEVEL_NORMAL=0
LEVEL_WARNING=1
LEVEL_CRITICAL=2

class Config:
    sysdef = {
        'state_file': '~/.munin-alert-phue.%(section)s.db',
        'critical_interval': '270',
        'light.normal': '@normal',
        'light.warning': '@warning',
        'light.critical': '@critical'
        }

    actions = {
        '@normal': [
            {'transitiontime': 50, 'on':True, 'bri': 128, 'hue':25500},
            {'transitiontime': 3000, 'on':False}
            ],
        '@normal-bright': [
            {'transitiontime': 50, 'on':True, 'bri': 255, 'hue':25500},
            {'transitiontime': 3000, 'on':False}
            ],
        '@warning': [
            {'transitiontime': 0, 'on':True, 'hue':53000, 'bri': 128, 'alert':'select'}
            ],
        '@warning-bright': [
            {'transitiontime': 0, 'on':True, 'hue':53000, 'bri': 255, 'alert':'select'}
            ],
        '@critical': [
            {'transitiontime': 0, 'on':True, 'hue':0, 'bri': 128, 'alert':'lselect'}
            ],
        '@critical-bright': [
            {'transitiontime': 0, 'on':True, 'hue':0, 'bri': 255, 'alert':'lselect'}
            ]
        }

    def __init__(self, config, section):
        self.config = config
        self.section = section
        self.vars = {'section': section }
        self.load_config()

    def load_config(self):
        self.hostname = self.get('hostname')
        self.username = self.get('username')
        self.state_file = os.path.expanduser(self.get('state_file'))
        lights = self.get('lights')
        if (lights is None):
            self.lights = []
        else:
            self.lights = lights.split(',')
        # TODO: iterate over sections and unset self.actions

    def get(self, option):
        if (self.config.has_option(self.section, option)):
            return self.config.get(self.section, option, 0, self.vars)
        elif (self.config.has_option('*', option)):
            return self.config.get('*', option, 0, self.vars)
        # TODO: get system default
        return None

    def level_str(self, level):
        if (level == LEVEL_NORMAL):
            return 'normal'
        if (level == LEVEL_WARNING):
            return 'warning'
        if (level == LEVEL_CRITICAL):
            return 'critical'

    def load_actions(self, actionId):
        # TODO: implement
        pass

    def get_actions(self, light, level):
        levelStr = self.level_str(level)
        actId = self.get('light.'+light+'.'+levelStr)
        if (actId == None):
            actId = self.get('light.'+levelStr)
        log.debug('Actions for light %s = %s', light, actId)
        if (not self.actions.has_key(actId)):
            self.load_actions(actId)
        if (not self.actions.has_key(actId)):
            log.error('Unknown action id for light "%s" and level "%s": %s', light, level, actId)
            return []
        return self.actions[actId]

class JSONReader():
    """
    A JSON iterator reading multiple JSON objects from a file object
    """
    braceCount = 0
    line = ""
    lineIdx = 0
    inStr = False
    json = ""

    def __init__(self, fp):
        self.fp = fp

    def __iter__(self):
        return self

    def read_line(self):
        self.line = self.fp.next()
        self.lineIdx = 0;
        if (len(self.line) == 0):
            raise StopIteration

    def next(self):
        if (self.fp.closed):
            raise StopIteration
        self.json = "";

        if (len(self.line) == 0):
            self.read_line()

        while (self.lineIdx < len(self.line)):                
            c = self.line[self.lineIdx]
            if (self.inStr):
                if (c == '\\'):
                    self.lineIdx += 1
                elif (c == '"'):
                    self.inStr = False

            elif (c == '{'):
                self.braceCount += 1
            elif (c == '}'):
                if (self.braceCount == 0):
                    raise Exception("Unexpected '}'", self.lineIdx, self.line)
                self.braceCount -= 1
                if (self.braceCount == 0):
                    self.json = self.json+self.line[0:self.lineIdx+1]
                    self.line = self.line[self.lineIdx+1:]
                    self.lineIdx = 0
                    log.debug("Received update: %s", self.json)
                    return json.loads(self.json)
            elif (c == '"'):
                self.inStr = True

            self.lineIdx += 1
            if (self.lineIdx >= len(self.line)):
                self.json += self.line
                self.read_line()

        raise Exception("Invalid content")


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
                         "The created username is written to the standard output in the configuration file format.")
    cmdline.add_argument('-v', '--verbose', action='count', default=0,
                         help="Increase verbosity. Can be used multiple times to keep increasing verbosity. "
                         "You will probably not see much up to -vv.")
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

def update_state(current_state, updates):
    """
    Update the current state
    """

    for update in updates:
        key = update.get('group', ''), update.get('host', ''), update.get('graph', '')
        if ('entries' not in current_state):
            current_state['entries'] = dict()
        current_state['entries'][key] = { 'warnings': update.get('warnings', []), 'criticals': update.get('criticals', []) }

    cleanup_state(current_state)
    current_state['current_status'] = get_max_status(current_state)

def cleanup_state(state):
    """
    Removes entries which have no warning or critical state
    """
    for (key, entry) in state['entries'].items():
        if len(entry['criticals']) == 0 and len(entry['warnings']) == 0:
            del state['entries'][key]

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


def update_lights(config, level):
    """
    Update the lights with the new state
    """
    bridge = Bridge(ip=config.hostname, username=config.username)
    for light in config.lights:
        log.debug('Updating light "%s"', light)
        actions = config.get_actions(light, level)
        for act in actions:
            bridge.set_light(light, act)


def register(bridge_host):
    """
    Register for a user at the provided host
    """
    class BridgeEx(Bridge):
        """
        Subclass of Bridge to perform a different way of registration
        """
        def register_app(self):
            registration_request = {"devicetype": "munin-alert-phue"}
            data = json.dumps(registration_request)
            response = self.request('POST', '/api', data)
            for line in response:
                for key in line:
                    if 'success' in key:
                        print("# User registration succesful")
                        print("[*]")
                        print("hostname="+self.ip)
                        print("username="+line['success']['username'])
                    if 'error' in key:
                        error_type = line['error']['type']
                        if error_type == 101:
                            print('ERROR: The link button has not been pressed in the last 30 seconds.', file=sys.stderr)
                        if error_type == 7:
                            print('ERROR: Unknown username.', file=sys.stderr)

    bridge = BridgeEx(ip=bridge_host)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s [%(name)s]: %(message)s', level=logging.ERROR)
    log = logging.getLogger('munin.alert.phue')

    args = parse_args()

    if (args.register != None):
        register(args.register)
        sys.exit()

    if (args.verbose > 0):
        lvl = logging.DEBUG;
        if (args.verbose == 1):
            lvl = logging.WARNING
        elif (args.verbose == 2):
            lvl = logging.INFO
        logging.getLogger().setLevel(lvl)

    config = Config(load_config(args.config), args.section)

    if (config.hostname == None):
        log.fatal('hostname not defined in config section [%s].', config.section)
        sys.exit(1)

    if (config.username == None):
        log.fatal('username not defined in config section [%s]. Start with --register argument to generate a username', config.section)
        sys.exit(1)

    lock = FileLock(config.state_file)
    try:
        lock.acquire(timeout=30)

        state = load_state(config.state_file)
        old_status = state['current_status']

        update_state(state, JSONReader(sys.stdin))

        updatePulse = int(config.get('critical_interval'))

        if (state['current_status'] != old_status
            or (state['current_status'] == LEVEL_CRITICAL and state['last_change'] < time.time() - updatePulse)
            ):
            log.info('Status changed from %d to %d', old_status, state['current_status'])
            update_lights(config, state['current_status'])
            state['last_change'] = time.time()

        log.debug("New state: %s", state)
        save_state(config.state_file, state)

    except LockTimeout:
        log.error('Failed to acquire lock on state file %s', config.state_file)
    finally:
        lock.release()
