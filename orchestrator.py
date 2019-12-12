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
    proxy=None
    def downloadTask(self, url, current=None):
        print(url)
        sys.stdout.flush()
        if self.downloader is not None:
            return self.downloader.addDownloadTask(url)
    
    def getFileList(self, message, current=None):
        fileNameList=[]
        for value in self.server.fileList:
            fileNameList.append(value)
        #fileList[message.name]=message.hash
        #convertir dic a lista y return
        return fileNameList 

class UpdateEvents(TrawlNet.UpdateEvent):
    server=None
    def newFile(self,fileInfo,current=None):
        self.server.fileList[fileInfo.hash]=fileInfo.name
        print("New event: %s " %fileInfo)        

class OrchestratorEvent(TrawlNet.OrchestratorEvent):
    ultimoOrchestrator=None
    def hello(self,orchestrator,current=None):
        print("Me ha dicho hola: %s" %orchestrator)
        ultimoOrchestrator=orchestrator

    def announce(self, neworches, current=None):
        print("Nuevo orchestrator: %s" % neworches)
        
        

    
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
        orchestratorEvent=OrchestratorEvent()
        updateEvents.server=self
                
        adapter = broker.createObjectAdapter("OrchestratorAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("Orchestrator1"))
        print(proxy, flush=True)
        servant.proxy=proxy
        proxyServer = self.communicator().stringToProxy(argv[1])

        #Parte de canal
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print("Invalid proxy")
            return 2

        subscriberUpdate = adapter.addWithUUID(updateEvents)
        subscriberOrches = adapter.addWithUUID(orchestratorEvent)
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
        
        publisherOrches = topicOrches.getPublisher()
        orchestratorPublisher = TrawlNet.OrchestratorEventPrx.uncheckedCast(publisherOrches)
        topicUpdate.subscribeAndGetPublisher(qos, subscriberUpdate)
        topicOrches.subscribeAndGetPublisher(qos, subscriberOrches)
        

        print("Waiting events... '{}'".format(subscriberUpdate))        

        downloader = TrawlNet.DownloaderPrx.checkedCast(proxyServer)

        if not downloader:
            raise RuntimeError('Invalid proxy')

        servant.downloader = downloader
        servant.server=self
        adapter.activate()

        me = TrawlNet.OrchestratorPrx.uncheckedCast(servant.proxy)
        orchestratorPublisher.hello(me)
        
        #if orchestratorPublisher != servant:
        #    orchestratorPublisher.announce(orchestratorPublisher.ultimoOrchestrator)

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        topicUpdate.unsubscribe(subscriberUpdate)

        return 0

server = Server()
sys.exit(server.main(sys.argv))
