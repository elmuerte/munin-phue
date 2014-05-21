munin-phue
==========

Munin alerting to Philips Hue for extreme feedback.

This script will translate [munin alerts](http://munin-monitoring.org/wiki/HowToContact) to a visual feedback using lights connected to a Philips hue system. It talks to a the [Philips Hue Bridge](http://www.zigbee.org/DesktopModules/ZigbeeCompanyProducts/ProductDetails.aspx?ProductID=635&Ctrl=ViewProducts) and from there is should be able to control up to 50 lights.

Munin-phue will change the color of the light based on the highest severity reported. 

![Lamps in warning state](http://i.imgur.com/7m0RTir.jpg)

Configuration
-------------

### configuration file

The `munin-alert-phue.py` by default reads the configuration from `~/.munin-alert-phue.ini` , but this can be changed using the `-c` commandline argument. The configuration file consist out of two kinds of elements.

1. Actions
2. Sections

#### Actions
Actions are a list of commands send to the lights. An aciton name starts with a @. The contents of an actions element is simply a list of JSON commands which should be send to the light in sequence. The key of the values do not matter.

Below is the standard configuration. Each action can be overwritten when defined in your configuration file.

```
[@normal]
1={"transitiontime": 50, "on":true, "bri": 128, "hue":25500}
2={"transitiontime": 3000, "on":false}

[@normal-bright]
1={"transitiontime": 50, "on":true, "bri": 255, "hue":25500}
2={"transitiontime": 3000, "on":false}

[@warning]
1={"transitiontime": 0, "on":true, "hue":53000, "bri": 128, "alert":"select"}

[@warning-bright]
1={"transitiontime": 0, "on":true, "hue":53000, "bri": 255, "alert":"select"}

[@critical]
1={"transitiontime": 0, "on":true, "hue":0, "bri": 128, "alert":"lselect"}

[@critical-bright]
1={"transitiontime": 0, "on":true, "hue":0, "bri": 255, "alert":"lselect"}
```

The JSON line accepts all values as defined in the [Philips hue Lights API](http://developers.meethue.com/1_lightsapi.html#16_set_light_state). 

The `normal` action will turn the light to green in 5 seconds, and then schedule the light to be turned off after 5 minutes. The `warning` action turns the light to purple and perform a single "breath" cycle. With the `critical` action the light is turned red and will "breath" for 30 seconds.

The action elements are used from the normal sections to tell which light configuration to apply for a light under certain circumstances.

#### Sections

You can define multiple sections in a single configuration file. This will allow you do have a single configuration file for different alert commands. The section to be used in the alert is defined by the `-s` command argument. By default it will use the `default` section.

There is a special section with the name `*` which can be used to define the defaults which can then be overwritten in a specific section. Below is the built in standard configuration.

```INI
[*]
state_file=~/.munin-alert-phue.%(section)s.db
critical_interval=270
light.normal=@normal
light.warning=@warning
light.critical=@critical
```
	
Below is an example configuration

```INI
[default]
hostname=bridge.hostname
username=bridge.username
lights=one,two
light.one.normal=@normal-bright
light.one.warning=@warning-bright
light.one.critical=@critical-bright
```

| Variable | Description |
|----------|-------------|
| `hostname` | The hostname, or IP, to the light bridge. |
| `username` | The username to use to connect to the bridge. |
| `critical_interval` | Number of seconds to wait before executing the commands for the critical state again. Set to 0 to disable. |
| `lights` | A comma separated list of lights to update. This is the name of the light. |
| `light.normal` | The actions to perform when everything returned to normal. |
| `light.warning` | The actions to perform when a warning level is reached. |
| `light.critical` | The actions to perform in a critical state. |
| `state_file` | The filename where to store the state. Each section should point to a different file otherwise they will conflict. `%(section)s` will be substituted with the section name. |


### Munin alert config

In order for this all to work you need to configure a munin alert command with a special input to be fed to `munin-alert-phue.pu`.

	contact.phue.command munin-alert-phue.py -c config.ini
	contact.phue.text { \
		"group": "${var:group}", \
		"host": "${var:host}", \
		"graph": "${var:graph_title}",\
		"warnings": [${loop<,>:wfields "${var:label}"}], \
		"criticals": [${loop<,>:cfields "${var:label}"}] \
		}

You probably also want to set `contact.phue.always_send critical` so that the light actions will be executed at the set `critical_interval`.


Dependencies
------------

* Python 2.7 or later
* [Python Phue (v0.8 or later)](https://github.com/studioimaginaire/phue)

Technical Documentation
-----------------------

* [Philips hue API](http://developers.meethue.com/)
