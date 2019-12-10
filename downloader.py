#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import Ice
import IceStorm
Ice.loadSlice('trawlnet.ice')
import TrawlNet
import os
import hashlib
try:
    import youtube_dl
except ImportError:
    print('ERROR: do you have installed youtube-dl library?')
    sys.exit(1)
    
def computeHash(filename):
    '''SHA256 hash of a file'''
    fileHash = hashlib.sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            fileHash.update(chunk)
    return fileHash.hexdigest()

def download_mp3(url, destination='./'):
    '''
    Synchronous download from YouTube
    '''
    options = {}
    task_status = {}
    def progress_hook(status):
        task_status.update(status)
    options.update(_YOUTUBEDL_OPTS_)
    options['progress_hooks'] = [progress_hook]
    options['outtmpl'] = os.path.join(destination, '%(title)s.%(ext)s')
    with youtube_dl.YoutubeDL(options) as youtube:
        youtube.download([url])
    filename = task_status['filename']
    # BUG: filename extension is wrong, it must be mp3
    filename = filename[:filename.rindex('.') + 1]
    return filename + options['postprocessors'][0]['preferredcodec']        

class NullLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

_YOUTUBEDL_OPTS_ = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'logger': NullLogger()
}

class Downloader(TrawlNet.Downloader):
    updateEventsPublisher=None

    def addDownloadTask(self, message, current=None):
        fileInfo=TrawlNet.FileInfo()
        fileInfo.name=download_mp3(message)
        fileInfo.hash=computeHash(fileInfo.name)
        self.updateEventsPublisher.newFile(fileInfo)
        return fileInfo

    


class Server(Ice.Application):
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property {} not set".format(key))
            return None

        return IceStorm.TopicManagerPrx.checkedCast(proxy)

    def run(self, argv):
        #Parte relacionada con el canal de sincronizacion
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print('Invalid proxy')
            return 2

        topic_name = "UpdateEvents"

        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            print("no such topic found, creating")
            topic = topic_mgr.create(topic_name)

        publisher = topic.getPublisher()
        updateEventsPublisher = TrawlNet.UpdateEventPrx.uncheckedCast(publisher)


        #parte del sirviente
        broker = self.communicator()
        servant = Downloader()
        servant.updateEventsPublisher=updateEventsPublisher
        adapter = broker.createObjectAdapter("DownloaderAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("downloader1"))
        

        print(proxy,flush=True)

        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0



server = Server()
sys.exit(server.main(sys.argv))

