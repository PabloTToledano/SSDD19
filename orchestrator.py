#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet

class Orchestrator(TrawlNet.Orchestrator):

    downloader = None
    fileList = {}
    orchestrators={}

    def downloadTask(self, url, current=None):
        print(url)
        sys.stdout.flush()
        if self.downloader is not None:
            return self.downloader.addDownloadTask(url)
    
    def getFileList(self, message, current=None):
        fileList[message.name]=message.hash
        return fileList
    
    def hello(self):
        return self
    def announce(otroOrchestrator):
        print("Nuevo orchestrator: ")#Y aquí no sé cómo corcho mostrar un orchestrator ni qué hay que pasars
    


    

    
class Server(Ice.Application):

    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property '{}' not set".format(key))
            return None

        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)


    def run(self, argv):
        #Parte del servidor
        broker = self.communicator()
        servant = Orchestrator() 
                
        adapter = broker.createObjectAdapter("OrchestratorAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("Orchestrator1"))
        print(proxy, flush=True)
        proxyServer = self.communicator().stringToProxy(argv[1])

        #Parte de canal
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print("Invalid proxy")
            return 2

        subscriber = adapter.addWithUUID(servant)
        #Aquí me suscribo a los dos topics
        topic_name = "UpdateEvents"
        topic_name2= "OrchestratorSync"
        qos = {}

        try:
            topic = topic_mgr.retrieve(topic_name)
            topic2 = topic_mgr.retrieve(topic2)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_name)
            topic2 = topic_mgr.create(topic2)
        
        topic.subscribeAndGetPublisher(qos, subscriber)
        
        #Me anuncio
        servant.hello()

        print("Waiting events... '{}'".format(subscriber))        

        downloader = TrawlNet.DownloaderPrx.checkedCast(proxyServer)

        if not downloader:
            raise RuntimeError('Invalid proxy')

        servant.downloader = downloader

        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        topic.unsubscribe(subscriber)

        return 0
