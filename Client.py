#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet

# primer argumento es el proxy, segundo url para descargar

class Client(Ice.Application):
    def run(self, argv):
        if(len(argv)<3):
            raise RuntimeError('Invalid arguments.')
        proxy = self.communicator().stringToProxy(argv[1])
        orchestrator = TrawlNet.OrchestratorPrx.checkedCast(proxy)

        if not orchestrator:
            raise RuntimeError('Invalid proxy')

        orchestrator.downloadTask(argv[2])
        print("Cliente ejecutado.")

        return 0


sys.exit(Client().main(sys.argv))