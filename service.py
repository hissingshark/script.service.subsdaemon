import json, time, xbmc

class _Monitor(xbmc.Monitor):
    def __init__(self):
        super(_Monitor, self).__init__()
        self.subs_player = 0
        self.subs_active = 'off'
        self.subs_forced_available = 'no'
        self.subs_forced_slot = 0
        self.subs_regular_available = 'no'
        self.subs_regular_slot = 0

    def notice(self, head, body, duration=2):
        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "GUI.ShowNotification", "params": {"title": "%s", "message": "%s", "image": "info", "displaytime": %i } }' % (head, body, duration*1000))

    def onNotification(self, sender, method, data):
        if sender == 'xbmc':
#            xbmc.log("\nSUBSDAEMON - Sender:%s, Method: %s; Data:%s\n" % (sender, method, data), xbmc.LOGINFO) # debug info
            if method == 'Player.OnAVStart' and json.loads(data)['item']['type'] != 'song':
            # playback starting (ignoring music)
                # reset state
                self.__init__()
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
                # switch off subs always at start of playback
                xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": %i, "subtitle": "off"}, "id": "subsdaemon" }' % self.subs_player)
                # select first forced subs slot if present
                if self.subs_forced_available == 'yes':
                    xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": %i, "subtitle": %i}, "id": "subsdaemon" }' % (self.subs_player, self.subs_forced_slot))
                    self.notice("Subtitles: OFF/FORCED","(showing forced subs)", 5)
                else:
                    self.notice("Subtitles: OFF","(no forced subs available)", 5)
        elif sender == 'hissingshark':
            if method == 'Other.subs_toggle':
            # subs being toggled from remote
                if self.subs_active == 'on':
                # subs were on
                    # so switch off
                    self.subs_active = 'off'
                    xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": %i, "subtitle": "off"}, "id": "subsdaemon" }' % self.subs_player)
                    # select first forced slot if present
                    if self.subs_forced_available == 'yes':
                        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": %i, "subtitle": %i}, "id": "subsdaemon" }' % (self.subs_player, self.subs_forced_slot))
                        self.notice("Subtitles: OFF/FORCED","(showing forced subs)")
                    else:
                        self.notice("Subtitles: OFF","(no forced subs available)")
                elif self.subs_active == 'off':
                # subs were off
                    # so switch on and select first regular slot if present
                    if self.subs_regular_available == 'yes':
                        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": %i, "subtitle": %i}, "id": "subsdaemon" }' % (self.subs_player, self.subs_regular_slot))
                        self.notice("Subtitles: ON","(showing regular subs)")
                    elif self.subs_forced_available == 'yes':
                    # no regular but already showing forced
                        self.notice("Subtitles: OFF/FORCED","(no regular subs available\n- showing forced)")
                    else:
                        # no subs available - so abort
                        self.notice("Subtitles: OFF","(none available)")
                        return
                    # then switch on
                    self.subs_active = 'on'
                    xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.SetSubtitle", "params": {"playerid": %i, "subtitle": "on"}, "id": "subsdaemon" }' % self.subs_player)
        else:
            return


if __name__ == '__main__':
    monitor = _Monitor()

    # boilerplate code for ensuring the Monitor loop doesn't hang Kodi on shutdown
    while not monitor.abortRequested():
        # Sleep/wait for abort for 10 seconds
        if monitor.waitForAbort(10):
            # Abort was requested while waiting. We should exit
            break
