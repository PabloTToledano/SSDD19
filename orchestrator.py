#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import Ice
import IceStorm
Ice.loadSlice('trawlnet.ice')
import TrawlNet


class Orchestrator(TrawlNet.Orchestrator):

    downloader = None
    server=None

    def downloadTask(self, url, current=None):
        print(url)
        sys.stdout.flush()
        if self.downloader is not None:
            return self.downloader.addDownloadTask(url)
    
    def getFileList(self, message, current=None):
        #fileList[message.name]=message.hash
        #convertir dic a lista y return
        return 
    
    def hello(self):
        return self
    def announce(otroOrchestrator):
        print("Nuevo orchestrator: ")#Y aquí no sé cómo corcho mostrar un orchestrator ni qué hay que pasars
    

class UpdateEvents(TrawlNet.UpdateEvent):
    server=None
    def newFile(self,fileInfo,current=None):
        self.server.fileList[fileInfo.hash]=fileInfo.name
        print("New event: %s " %fileInfo)        
    

    
class Server(Ice.Application):
    fileList = {}   

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
        updateEvents=UpdateEvents()
        updateEvents.server=self
                
        adapter = broker.createObjectAdapter("OrchestratorAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("Orchestrator1"))
        print(proxy, flush=True)
        proxyServer = self.communicator().stringToProxy(argv[1])

        #Parte de canal
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print("Invalid proxy")
            return 2

        subscriberUpdate = adapter.addWithUUID(updateEvents)
        #Aquí me suscribo a los dos topics
        topic_name = "UpdateEvents"
        topic_name2= "OrchestratorSync"
        qos = {}

        try:
            topicUpdate = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topicUpdate = topic_mgr.create(topic_name)
        
        try:        
            topicOrches = topic_mgr.retrieve(topic_name2)
        except IceStorm.NoSuchTopic:
            topicOrches = topic_mgr.create(topic_name2)
        
        
        topicUpdate.subscribeAndGetPublisher(qos, subscriberUpdate)
        
        #Me anuncio
        servant.hello()

        print("Waiting events... '{}'".format(subscriberUpdate))        

        downloader = TrawlNet.DownloaderPrx.checkedCast(proxyServer)

        if not downloader:
            raise RuntimeError('Invalid proxy')

        servant.downloader = downloader
        servant.server=self
        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        topicUpdate.unsubscribe(subscriberUpdate)

        return 0

server = Server()
sys.exit(server.main(sys.argv))