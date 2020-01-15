#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import Ice
import IceStorm

Ice.loadSlice("trawlnet.ice")
import TrawlNet
import os
import hashlib

try:
    import youtube_dl
except ImportError:
    print("ERROR: do you have installed youtube-dl library?")
    sys.exit(1)

from urllib.parse import urlparse


def video_id(url):
    o = urlparse(url)
    if o.netloc == "youtu.be":
        return o.path[1:]
    elif o.netloc in ("www.youtube.com", "youtube.com"):
        if o.path == "/watch":
            id_index = o.query.index("v=")
            return o.query[id_index + 2 : id_index + 13]
        elif o.path[:7] == "/embed/":
            return o.path.split("/")[2]
        elif o.path[:3] == "/v/":
            return o.path.split("/")[2]
    return None  # fail?


def computeHash(filename):
    """SHA256 hash of a file"""
    fileHash = hashlib.sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            fileHash.update(chunk)
    return fileHash.hexdigest()


def download_mp3(url, destination="./"):
    """
    Synchronous download from YouTube
    """
    options = {}
    task_status = {}

    def progress_hook(status):
        task_status.update(status)

    options.update(_YOUTUBEDL_OPTS_)
    options["progress_hooks"] = [progress_hook]
    options["outtmpl"] = os.path.join(destination, "%(title)s.%(ext)s")
    with youtube_dl.YoutubeDL(options) as youtube:
        youtube.download([url])
    filename = task_status["filename"]
    # BUG: filename extension is wrong, it must be mp3
    filename = filename[: filename.rindex(".") + 1]
    return filename + options["postprocessors"][0]["preferredcodec"]


class NullLogger:
    def debug(self, msg):
        print(msg)
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)
        pass


_YOUTUBEDL_OPTS_ = {
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
    "logger": NullLogger(),
}


class Downloader(TrawlNet.Downloader):
    updateEventsPublisher = None

    def addDownloadTask(self, message, current=None):
        fileInfo = TrawlNet.FileInfo()
        fileInfo.name = download_mp3(message)
        fileInfo.hash = video_id(message)
        self.updateEventsPublisher.newFile(fileInfo)
        return fileInfo

    def destroy(self, current):
        try:
            current.adapter.remove(current.id)
            print("TRASFER DESTROYED", flush=True)
        except Exception as e:
            print(e, flush=True)


class DownloaderFactory(TrawlNet.DownloaderFactory):
    def create(self, current):
        servant = Downloader()
        proxy = current.adapter.addWithUUID(servant)
        return TrawlNet.DownloaderPrx.checkedCast(proxy)


class Server(Ice.Application):
    def get_topic_manager(self):
        key = "IceStorm.TopicManager.Proxy"
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property {} not set".format(key))
            return None

        return IceStorm.TopicManagerPrx.checkedCast(proxy)

    def run(self, argv):
        # Parte relacionada con el canal de sincronizacion
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print("Invalid proxy")
            return 2

        topic_name = "UpdateEvents"

        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_name)

        publisher = topic.getPublisher()
        updateEventsPublisher = TrawlNet.UpdateEventPrx.uncheckedCast(publisher)

        # parte del sirviente

        broker = self.communicator()
        properties = broker.getProperties()

        servant = DownloaderFactory()
        Downloader.updateEventsPublisher = updateEventsPublisher
        adapter = broker.createObjectAdapter("DownloaderFactoryAdapter")
        factory_id = properties.getProperty("Identity")
        proxy = adapter.add(servant, broker.stringToIdentity(factory_id))

        print("{}".format(proxy), flush=True)

        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


server = Server()
sys.exit(server.main(sys.argv))
