munin-phue
==========

Munin alerting to Philips Hue for extreme feedback.

This script is to be for translating munin alerts (http://munin-monitoring.org/wiki/HowToContact) to a visual feedback using lights connected to a Philips hue system.

Munin-phue will change the color of the light based on the highest severity reported. 

Munin alert config:

contact.phue.command | munin-alert-phue.py munin-alert-phue.py
contact.phue.text { \
		"group": "${var:group}", \
		"host": "${var:host}", \
		"graph": "${var:graph_title}",\
		"warnings": [${loop<,>:wfields "${var:label}"}], \
		"criticals": [${loop<,>:cfields "${var:label}"}], \
	}


Configuration
-------------

[default]
hostname=bridge-hostname
username=bridge-username
state_file=~/.munin-alert-phue.db
normal_hue=25500
warning_hue=5000
critical_hue=0


Dependencies
------------

* Python Phue : https://github.com/studioimaginaire/phue

Technical Documentation
-----------------------

* Philips hue API : http://developers.meethue.com/
