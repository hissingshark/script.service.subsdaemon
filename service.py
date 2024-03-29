import json, xbmc

class _Monitor(xbmc.Monitor):
    # class constructor
    def __init__(self):
        super(_Monitor, self).__init__()

        # instantiate bulk-resetable variables
        self.reset()
        # then instance variables protected from reset()
        self.prev_subs_pref = False
        self.hopping = False


    # perform reset of state variables
    def reset(self):
        self.subs_player = 0
        self.subs_active = 'off'
        self.subs_forced_available = 'no'
        self.subs_forced_slot = 0
        self.subs_regular_available = 'no'
        self.subs_regular_slot = 0


    # display a notification in Kodi
    def notice(self, head, body, duration=2):
        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "GUI.ShowNotification", "params": {"title": "%s", "message": "%s", "image": "info", "displaytime": %i } }' % (head, body, duration*1000))


    # scan subtitle configuration of current media
    def scanSubs(self, data):
        # extract player ID from data
        self.subs_player = json.loads(data)['player']['playerid']
        # check and store subs availability
        reply = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetProperties", "params": { "properties": ["subtitles"], "playerid": %i }, "id": "testing"}' % self.subs_player)
        payload = json.loads(reply)
        # find first forced sub
        for item in payload['result']['subtitles']:
            if item['isforced'] == True:
                self.subs_forced_available = 'yes'
                self.subs_forced_slot = item['index']
                break
        # find first regular sub
        for item in payload['result']['subtitles']:
            if item['isforced'] == False:
                self.subs_regular_available = 'yes'
                self.subs_regular_slot = item['index']
                break

        xbmc.log("\nSUBSDAEMON State:\nsubs_player = %s\n subs_active = %s\n subs_forced_available = %s\n subs_forced_slot = %s\n subs_regular_available = %s\n subs_regular_slot = %s\n" % (self.subs_player, self.subs_active, self.subs_forced_available, self.subs_forced_slot, self.subs_regular_available, self.subs_regular_slot), xbmc.LOGINFO) # debug info


    # callback for receipt of Kodi notifications
    def onNotification(self, sender, method, data):
        if sender == 'xbmc':
            xbmc.log("\nSUBSDAEMON - Sender:%s, Method: %s; Data:%s\n" % (sender, method, data), xbmc.LOGINFO) # debug info
            if method == 'Player.OnResume':
                # hopping from one content to another - so preserve subs preference for next media item
                self.hopping = True
                if self.subs_active == 'on':
                    self.prev_subs_pref == True
                else:
                    self.prev_subs_pref == False
            elif method == 'Player.OnAVStart':
                if json.loads(data)['item']['type'] == 'song':
                    # breaks any hopping continuity
                    self.prev_subs_pref = False
                    self.hopping = False
                    return

                # playback starting (not music)
                # set state to new media subs
                self.reset()
                self.scanSubs(data)

                # silently display regular subs if available and maintaining a preference for default subs
                if self.subs_regular_available == 'yes' and self.hopping == True and self.prev_subs_pref == True:
                    xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": %i, "subtitle": %i}, "id": "subsdaemon" }' % (self.subs_player, self.subs_regular_slot))
#                    self.notice("Subtitles: ON","(showing regular subs)", 5)
                # display forced subs if present and not maintaining a preference for default subs
                elif self.subs_forced_available == 'yes' and self.hopping == False:
                    xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": %i, "subtitle": %i}, "id": "subsdaemon" }' % (self.subs_player, self.subs_forced_slot))
                    self.notice("Subtitles: ON/FORCED","(showing forced subs)", 5)
                # otherwise default to switching subs off at start of playback (silently for TV channels)
                else:
                    xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": %i, "subtitle": "off"}, "id": "subsdaemon" }' % self.subs_player)
                    if json.loads(data)['item']['type'] != 'channel':
                        self.notice("Subtitles: OFF","(no forced subs available)", 5)
        elif sender == 'hissingshark':
            if method == 'Other.subs_toggle':
            # subs being toggled from remote
                if self.subs_active == 'on':
                # regular subs were on
                    # so switch off or show forced
                    self.subs_active = 'off'
                    if self.subs_forced_available == 'yes':
                        # select first forced slot if present
                        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": %i, "subtitle": %i}, "id": "subsdaemon" }' % (self.subs_player, self.subs_forced_slot))
                        self.notice("Subtitles: ON/FORCED","(showing forced subs)")
                    else:
                        # no forced subs, so switch off
                        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": %i, "subtitle": "off"}, "id": "subsdaemon" }' % self.subs_player)
                        self.notice("Subtitles: OFF","(no forced subs available)")
                elif self.subs_active == 'off':
                # regular subs were off
                    # so switch on and select first regular slot if present
                    if self.subs_regular_available == 'yes':
                        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": %i, "subtitle": %i}, "id": "subsdaemon" }' % (self.subs_player, self.subs_regular_slot))
                        self.notice("Subtitles: ON","(showing regular subs)")
                    elif self.subs_forced_available == 'yes':
                    # no regular but already showing forced
                        self.notice("Subtitles: ON/FORCED","(no regular subs available\n- showing forced)")
                    else:
                        # no subs available - so abort
                        self.notice("Subtitles: OFF","(none available)")
                        return
                    # then switch on
                    self.subs_active = 'on'
                    xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": %i, "subtitle": "on"}, "id": "subsdaemon" }' % self.subs_player)
        else:
            return


# execution begins here
if __name__ == '__main__':
    monitor = _Monitor()

    # boilerplate code for ensuring the Monitor loop doesn't hang Kodi on shutdown
    while not monitor.abortRequested():
        # Sleep/wait for abort for 10 seconds
        if monitor.waitForAbort(10):
            # Abort was requested while waiting. We should exit
            break
