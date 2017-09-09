https://github.com/thijsbekke/OctoPrint-Pushover/
# OctoPrint-Pushjet

Notification plugin for [Octoprint](octoprint.org). It can be used to receive push notifications on your phone using [Pushjet](https://pushjet.io/).
This is practically an adaptation of the plugin from [thijsbekke](https://github.com/thijsbekke/OctoPrint-Pushover/) with minor modification and 
the possibility to sent the notification asynchronously.
 

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/dipusone/OctoPrint-Pushjet/archive/master.zip


## Configuration

To configure the plugin the only two settings needed are:
 - the **API Url** which is the endpoint address.
 - the **Token** which is the secret token you receive when creating a pushjet service.
 
You can read on how to to create a service to dispatch the notification on [Pushjet](http://docs.pushjet.io/docs/getting-started).

## Features

The features of this plugin are similar to [OctoPrint-Pushover](https://github.com/thijsbekke/OctoPrint-Pushover/) with some twists.

### Retry

The messages are sent asynchronously for performance reasons and if the pushjet
endpoint is not stable the sending can fail. In this case the plugin will try 
resend the message up to the configured number of times.

### Time between retry

It is possible to specify a sleep time between the retry.

### Append timestamp

This option will append at the end of the message the time at which was generated.

For example:

```
Print finished ...  on 23:15

``` 

### Remove Extension

This option will remove the extension from the filename. If for any reason you 
need the extension you can re-enable it by un-checking this setting.
For example *marvin.gcode* would become *marvin*.


### Pause/Waiting Event

This feature is from the original plugin [OctoPrint-Pushover](https://github.com/thijsbekke/OctoPrint-Pushover/).

When for example a ```M0``` or a ```M226``` command is received and the settings are complied. This plugin will send a notification. And as bonus it will append any ```M70``` message to the notification, so you can remind yourself which colour you need to switch.

For example
```GCODE
G1 X109.071 Y96.268 E3.54401
G1 X109.186 Y97.500 E3.63927
M70 Sleep Message
M0
G1 X109.186 Y102.500 E4.02408
G1 X108.789 Y104.770 E4.20140
```


### Priority

It is possible to set the notification level for the various events.
I swear I cannot find the meaning of the levels in the Pushjet documentation :).

