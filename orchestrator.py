#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet

class Orchestrator(TrawlNet.Orchestrator):
    def downloadTask(self, message, current=None):
        print(message)
        downloader.addDownloadTask()


        sys.stdout.flush()
    
    

class Server(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        servant = Orchestrator()

        adapter = broker.createObjectAdapter("OrchestratorAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("Orchestrator1"))

        print(proxy, flush=True)

        proxyServer = self.communicator().stringToProxy(argv[1])
        print(argv[1])
        downloader = TrawlNet.DownloaderPrx.checkedCast(proxyServer)

        if not downloader:
            raise RuntimeError('Invalid proxy')

        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


server = Server()
sys.exit(server.main(sys.argv))