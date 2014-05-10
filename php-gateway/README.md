PHP Gateway
-----------

This is a simply gateway written in PHP to forward a munin alert from a different host
to the munin-alert-phue.py script running on this machine. 

It provides an easy way to let alerts from a different network trigger lights unreachable 
from that network.

Configuration of the gateway
============================

Create the file ```config.php``` with the following contents

```PHP
$config['bin'] = '/path/to/munin-alert-phue.py';
$config['my_secret_key']['config-file'] = '/path/to/my/config';
$config['my_secret_key']['config-section'] = 'default';
```

Munin alert configuration
=========================

Instead of calling the munin-alert-phue.py script, change the like to execute cURL:

```
contact.phue.command curl -X PUT http://example.org/munin-alert-phue/MY_KEY
```

Where MY_KEY should be the key you configured in the gateway configuration.


