#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet

# primer argumento es el proxy, segundo url para descargar



class Client(Ice.Application):
    orchestrator = None
   
    def transfer_request(self, file_name):
        remote_EOF = False
        BLOCK_SIZE = 1024
        transfer = None

        try:
            transfer = self.orchestrator.getFile(file_name)
        except TrawlNet.TransferError as e:
            print(e.reason)
            return 1

        with open(os.path.join(DOWNLOADS_DIRECTORY, file_name), 'wb') as file_:
            remote_EOF = False
            while not remote_EOF:
                data = transfer.recv(BLOCK_SIZE)
                if len(data) > 1:
                    data = data[1:]
                data = binascii.a2b_base64(data)
                remote_EOF = len(data) < BLOCK_SIZE
                if data:
                    file_.write(data)
            transfer.close()

        transfer.destroy()
        print('Transfer finished!')

    def run(self, argv):
        if(len(argv)<1):
            raise RuntimeError('Invalid arguments.')

        proxy = self.communicator().stringToProxy(argv[1])
        self.orchestrator = TrawlNet.OrchestratorPrx.checkedCast(proxy)
        if not self.orchestrator:
            raise RuntimeError('Invalid proxy')

        # argv[1]=proxy , 2=opcion , 3=url o name del archivo

        if(len(argv)==3): #si hay link envio peticion de descarga
            if(argv[2] == "-d"):
                fileInfoName = self.orchestrator.downloadTask(argv[3]).name
                print(fileInfoName)
                transfer_request(fileInfoName)
            if(argv[2] == "-t"):
                transfer_request(argv[3])     
                
        if(len(argv) == 2):
            print(str(self.orchestrator.getFileList()))
        print("Cliente ejecutado.")

        return 0



sys.exit(Client().main(sys.argv))