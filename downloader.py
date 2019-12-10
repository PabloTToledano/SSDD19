#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet
try:
    import youtube_dl
except ImportError:
    print('ERROR: do you have installed youtube-dl library?')
    sys.exit(1)
    
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
    updateEventsPrinter=None

    def addDownloadTask(self, message, current=None):
        filename=download_mp3(message)
        sys.stdout.flush()
        newFile(filename)
        return filename
    
    def newFile(fileInfo):
        updateEventsPrinter.write(fileInfo)

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
    


class Server(Ice.Application):
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property {} not set".format(key))
            return None

        print("Using IceStorm in: '%s'" % key)
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
        updateEventsPrinter = Example.PrinterPrx.uncheckedCast(publisher)


        #parte del sirviente
        broker = self.communicator()
        servant = Downloader()
        servant.updateEventsPrinter=updateEventsPrinter
        adapter = broker.createObjectAdapter("DownloaderAdapter")
        proxy = adapter.add(servant, broker.stringToIdentity("downloader1"))
        

        print(proxy)

        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0



server = Server()
sys.exit(server.main(sys.argv))