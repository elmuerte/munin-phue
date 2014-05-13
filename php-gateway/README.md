PHP Gateway
-----------

This is a simply gateway written in PHP to forward a munin alert from a different host
to the ```munin-alert-phue.py``` script running on this machine. 

It provides an easy way to let alerts from a different network trigger lights unreachable 
from that network.

Configuration of the gateway
============================

Create the file ```config.php``` with the following contents

```PHP
$config['bin'] = '/path/to/munin-alert-phue.py';

$config['MY_SECRET_KEY']['config-file'] = '/path/to/my/config';
$config['MY_SECRET_KEY']['config-section'] = 'default';

//$config['MY_OTHER_KEY']['config-file'] = '/path/to/my/config';
//$config['MY_OTHER_KEY']['config-section'] = 'others';
```

Replace ```MY_SECRET_KEY``` with a random string you want to use in the request. This would be the "security" to prevent others from posting updates.

Munin alert configuration
=========================

Instead of calling the ```munin-alert-phue.py``` script, change the like to execute cURL:

```
contact.phue.command curl -X PUT http://example.org/munin-alert-phue/MY_SECRET_KEY -d@-
```

Where ```MY_SECRET_KEY``` should be the key you configured in the gateway configuration.



