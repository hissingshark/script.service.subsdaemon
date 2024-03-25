# script.service.subsdaemon  

## Kodi service to handle forced subtitle tracks in a more intuitive manner.  

## It may just be me - but I expected Kodi to show the same behaviour as DVD/Blu-ray players regarding subtitles:  
When subtitles are switched off, it should still display forced subtitles when they are available (hence the name), rather than having to go looking for them every time I start playback.  Switching subtitles on should then display the regular subtitles.

## Kodi does not seem to work that way:  
Forced subs display even if subs are technically switched off - fine, but it is necessary to manually select the correct slot.
Regular subs display when subs are switched on, but only if the correct slot has been manually selected again...

## This service will:  
- Check for the presence of forced and regular subtitle tracks at the beginning of playback;
- Select the forced track so that it will be displayed by default;
- Upon a notification signal, toggle between the forced and regular track, switching on/off as required;
The signal should be a notification from sender "hissingshark" and data of "subs_toggle".

To take over the role of the subtitles button, the remote.xml file will need to have a button configured to send the notification via the Kodi `NotifyAll` built-in function, e.g.:  
> <green>NotifyAll(hissingshark, subs_toggle)</green>

A complete example is included in this repository.
Kodi expects these to be stored at `.kodi/userdata/keymaps/`
