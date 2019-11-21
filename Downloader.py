#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet


class Downloader(TrawlNet.Downloader):
    def addDownloadTask(self, message, current=None):
        print(message)
        sys.stdout.flush()
    


class Server(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        servant = Downloader()

        adapter = broker.createObjectAdapter("DownloaderAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("downloader1"))

        print(proxy)

        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


server = Server()
sys.exit(server.main(sys.argv))