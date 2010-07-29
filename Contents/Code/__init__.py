from PMS import *
import re, string, datetime, pyamf
from pyamf.remoting.client import RemotingService

NAMESPACE = {'media':'http://search.yahoo.com/mrss/'}
VIDEO_PREFIX = "/video/snagfilms"

#AMF_PROXY_URL = "http://www.plexapp.com/proxy/BrightcoveAmfProxy.cgi?playerId=%s&videoId=%s"

SEARCH_URL= "http://www.snagfilms.com/films"
TOPICS_URL = "http://www.snagfilms.com/films/browse/topic/"
CHANNELS_URL = "http://www.snagfilms.com/films/browse/channel/"
AZ_URL = "http://www.snagfilms.com/films/browse/a-z/%s/%d"

RSS_BASE_URL = "http://fb.snagfilms.com"
MOST_POPULAR_FEED = RSS_BASE_URL + "/SnagFilmsMostPopular?format=xml"
TOP_RATED_FEED = RSS_BASE_URL + "/SnagFilmsUserFavorites?format=xml"
MOST_DISCUSSED_FEED = RSS_BASE_URL + "/SnagFilmsMostDiscussed?format=xml"
RECENT_ADDITIONS_FEED = RSS_BASE_URL + "/SnagFilmsRecentAdditions?format=xml"


####################################################################################################
def Start():
  Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, "SnagFilms", "icon-default.png", "art-default.png")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  MediaContainer.art = R('art-default.png')
  MediaContainer.title1 = 'SnagFilms'
  DirectoryItem.thumb = R("icon-default.png")
  

#################################
def MainMenu():
    dir = MediaContainer(mediaType='video')  
    dir.Append(Function(DirectoryItem(RssFeed, title="Recent Additions"), url=RECENT_ADDITIONS_FEED))
    dir.Append(Function(DirectoryItem(RssFeed, title="Most Popular"), url=MOST_POPULAR_FEED))
    dir.Append(Function(DirectoryItem(RssFeed, title="Top Rated"), url=TOP_RATED_FEED))
    dir.Append(Function(DirectoryItem(RssFeed, title="Most Discussed"), url=MOST_DISCUSSED_FEED))
    dir.Append(Function(DirectoryItem(Topics, title="Topics")))
    dir.Append(Function(DirectoryItem(Channels, title="Channels")))
    dir.Append(Function(DirectoryItem(AllFilms, title="All Films")))
    dir.Append(Function(InputDirectoryItem(Search, title="Search ...", thumb=R("search.png"), prompt="Search for films")))
    return dir
    
# Extract details from the RSS feeds
def RssFeed(sender, url):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
  feed = RSS.FeedFromURL(url)
  for item in feed['items']: 
      published = Datetime.ParseDate(item.updated).strftime('%a %b %d, %Y')
      summary = String.StripTags(item.description)
      thumb = item.media_thumbnail[0]['url']
      pageUrl = item.link
      dir.Append(Function(VideoItem(PlayVideo, title=item.title, summary=summary, thumb=thumb, subtitle=published), pageUrl=pageUrl))
  return dir
  
# Alphabetical list
def AllFilms(sender):
    dir = MediaContainer(title2=sender.itemTitle)
    for letter in string.uppercase:
        dir.Append(Function(DirectoryItem(AlphabeticalFilms, title=letter), letter=letter, page=0))
    return dir
    
def AlphabeticalFilms(sender, letter, page):
    url = AZ_URL % (letter, page)
    dir = MediaContainer(title2=letter, replaceParent=True)
    for item in XML.ElementFromURL(url, True).xpath('//div[@class="module_content"]/div'):
        if len(item.xpath('./div/a')) > 0:
            title = item.xpath("./div[@class='fleft']/a")[0].get('title')
            pageUrl = item.xpath("./div[@class='fleft']/a")[0].get('href')
            image = item.xpath("./div[@class='fleft']/a/img")[0].get('src')
            summary = item.xpath("./div[@class='text']")[0].text
            dir.Append(Function(VideoItem(PlayVideo, title=title, summary=summary, thumb=image, subtitle=None), pageUrl=pageUrl))
    if len(XML.ElementFromURL(url, True).xpath('//a[@href and text()="Next"]')) > 0:
        dir.Append(Function(DirectoryItem(AlphabeticalFilms, title="More ..."), letter=letter, page=page+20))
    return dir
    
# List of Topics 
def Topics(sender):
    dir = MediaContainer(title2=sender.itemTitle)
    for item in XML.ElementFromURL(TOPICS_URL, True).xpath('//div[@id="browse_content"]/div/div[@class="module_content"]'):
        title = item.xpath('./h1/a')[0].text
        topicUrl = item.xpath('./h1/a')[0].get('href')
        thumb = item.xpath('.//div[@class="browse_poster_list"]/div/a/img')[0].get('src')
        dir.Append(Function(DirectoryItem(TopicSections, title=title, thumb=thumb), url=topicUrl, topic=title))
    return dir
  
def TopicSections(sender, url, topic):
  dir = MediaContainer(title2=sender.itemTitle)
  dir.Append(Function(DirectoryItem(FeaturedFilms, title="Featured "+topic+" Films"), url=url))
  dir.Append(Function(DirectoryItem(NewestTopicFilms, title="Newest "+topic+" Films"), url=url))
  dir.Append(Function(DirectoryItem(PopularTopicFilms, title="Popular "+topic+" Films"), url=url))
  dir.Append(Function(DirectoryItem(AllTopicFilms, title="All "+topic+" Films"), url=url+"a-z"))
  return dir
  
def NewestTopicFilms(sender, url):
    return ParseFixedModule(sender, url, 3)

def PopularTopicFilms(sender, url):
    return ParseFixedModule(sender, url, 4)

def ParseFixedModule(sender, url, number):
    dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
    module = XML.ElementFromURL(url, True).xpath('//div[@class="module"]')[number]
    for item in module.xpath('.//div'):
        if len(item.xpath('./div[@class="fleft"]/a')) > 0:
            title = item.xpath("./div[@class='fleft']/a")[0].get('title')
            pageUrl = item.xpath("./div[@class='fleft']/a")[0].get('href')
            image = item.xpath("./div[@class='fleft']/a/img")[0].get('src')
            summary = item.xpath("./div[@class='text']")[0].text
            dir.Append(Function(VideoItem(PlayVideo, title=title, summary=summary, thumb=image, subtitle=None), pageUrl=pageUrl))
    return dir

def AllTopicFilms(sender, url, page=0):
    dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
    pagedUrl = url + "/P%d" % page
    items = XML.ElementFromURL(pagedUrl, True).xpath('//div[@class="module_content"]/div')
    for item in items:
        if len(item.xpath('./div/a')) > 0:
            title = item.xpath("./div[@class='fleft']/a")[0].get('title')
            pageUrl = item.xpath("./div[@class='fleft']/a")[0].get('href')
            image = item.xpath("./div[@class='fleft']/a/img")[0].get('src')
            summary = item.xpath("./div[@class='text']")[0].text
            dir.Append(Function(VideoItem(PlayVideo, title=title, summary=summary, thumb=image, subtitle=None), pageUrl=pageUrl))
    if len(XML.ElementFromURL(pagedUrl, True).xpath('//a[@href and text()="Next Page"]')) > 0:
        dir.Append(Function(DirectoryItem(AllTopicFilms, title="More ..."), url=url, page=page+15))
    return dir

  
# List of Channels 
def Channels(sender):
    dir = MediaContainer(title2=sender.itemTitle)
    for item in XML.ElementFromURL(CHANNELS_URL, True).xpath('//div[@id="browse_content"]/div/div[@class="module_content"]'):
        title = item.xpath('./h1/a')[0].text
        channelUrl = item.xpath('./h1/a')[0].get('href')
        thumb = item.xpath('.//div[@class="browse_poster_list"]/div/a/img')[0].get('src')
        dir.Append(Function(DirectoryItem(ChannelSections, title=title, thumb=thumb), url=channelUrl, channel=title))
    return dir
  
def ChannelSections(sender, url, channel):
  dir = MediaContainer(title2=sender.itemTitle)
  dir.Append(Function(DirectoryItem(FeaturedFilms, title="Featured "+channel+" Films"), url=url))
  dir.Append(Function(DirectoryItem(FeaturedFilms, title="Newest "+channel+" Films"), url=url+"/newest"))
  dir.Append(Function(DirectoryItem(FeaturedFilms, title="Top Rated "+channel+" Films"), url=url+"/faves"))
  dir.Append(Function(DirectoryItem(FeaturedFilms, title="Most Discussed "+channel+" Films"), url=url+"/discussed"))
  if HasAlphabeticalContent(url+"a-z"):
      dir.Append(Function(DirectoryItem(AllChannelFilms, title="All "+channel+" Films"), url=url+"a-z"))
  return dir

def HasAlphabeticalContent(url):
    items = XML.ElementFromURL(url, True).xpath('//div[@class="module_content"]/div')
    for item in items:
        if len(item.xpath('./div/a')) > 0:
            return True
    return False
 
def AllChannelFilms(sender, url):
    dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
    items = XML.ElementFromURL(url, True).xpath('//div[@class="module_content"]/div')
    for item in items:
        if len(item.xpath('./div/a')) > 0:
            title = item.xpath("./div[@class='fleft']/a")[0].get('title')
            pageUrl = item.xpath("./div[@class='fleft']/a")[0].get('href')
            image = item.xpath("./div[@class='fleft']/a/img")[0].get('src')
            summary = item.xpath("./div[@class='text']")[0].text
            dir.Append(Function(VideoItem(PlayVideo, title=title, summary=summary, thumb=image, subtitle=None), pageUrl=pageUrl))
    return dir

# Those contained in the scrolling module
def FeaturedFilms(sender, url):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
  for item in XML.ElementFromURL(url, True).xpath('//div[@class="dl_container"]'):
        pageUrl = item.xpath("./div[@class='dl_text']//span[@class='title']/a")[0].get('href')
        title = item.xpath("./div[@class='dl_text']//span[@class='title']/a")[0].text
        image = item.xpath("./div[@class='dl_image']/a/img")[0].get('src')
        summary = item.xpath("./div[@class='dl_text']//span[@class='txt']")[0].text
        dir.Append(Function(VideoItem(PlayVideo, title=title, summary=summary, thumb=image, subtitle=None), pageUrl=pageUrl))
  return dir
  
# Search is a POST driven form with lots of hidden parameters
def Search(sender, query):
    dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
    queryData = dict()
    queryData['XID'] = ''
    queryData['ACT'] = '19'
    queryData['RP'] = 'search&#47;results'
    queryData['NRP'] = 'search'
    queryData['RES'] = ''
    queryData['status'] = 'open'
    queryData['weblog'] = 'film_blog|snagfilmsnews_blog'
    queryData['search_in'] = 'entries'
    queryData['where'] = 'all'
    queryData['site_id'] = '1'
    queryData['keywords'] = query
    response = HTTP.Request(SEARCH_URL, queryData)
    if response != None:
        items = XML.ElementFromString(response, True).xpath('//div[@class="module_content"]')
        for item in items:
            if len(item.xpath('./div/a')) > 0:
                 title = item.xpath("./div[@class='fleft']/a")[0].get('title')
                 pageUrl = item.xpath("./div[@class='fleft']/a")[0].get('href')
                 image = item.xpath("./div[@class='fleft']/a/img")[0].get('src')
                 summary = item.xpath("./div[@class='text']")[0].text
                 dir.Append(Function(VideoItem(PlayVideo, title=title, summary=summary, thumb=image, subtitle=None), pageUrl=pageUrl))
    return dir
    
# Extracts the rtmp player and clip from the AMF proxy and redirects
def PlayVideo(sender, pageUrl):
    response = HTTP.Request(pageUrl)
    Log("PageURL:"+pageUrl)

    playerId = re.findall("'playerid':'([0-9]+)'", response)[-1]
    videoId = re.findall("'videoid':'([0-9]+)'", response)[-1]
    Log("PlayerID:"+playerId+" VideoID:"+videoId)

    rtmp = AmfRequest(playerId, videoId, 'http://www.snagfilms.com/')
    #proxyUrl = AMF_PROXY_URL % (playerId, videoId)
    #Log("ProxyUrl:"+proxyUrl)
    #rtmp = XML.ElementFromURL(proxyUrl).xpath('/amfProxy/result/message')[0].text
    tokens = rtmp.split('&')
    return Redirect(RTMPVideoItem(tokens[0], tokens[1]))


####################################################################################################
class ContentOverride(object):
  def __init__ (self, videoId=None):
    self.contentType = int(0)
    self.contentIds = None
    self.target = 'videoPlayer'
    self.contentId = int(videoId)
    self.featuredRefId = None
    self.contentRefIds = None
    self.featuredId = float('nan')
    self.contentRefId = None

class ViewerExperienceRequest(object):
  def __init__ (self, playerId=None, video=None, url=None):
    self.experienceId = int(playerId)
    self.contentOverrides = []
    self.contentOverrides.append(video)
    self.TTLToken = ''
    self.URL = url

def AmfRequest(playerId, videoId, url):
  client = RemotingService('http://c.brightcove.com/services/messagebroker/amf', user_agent='', client_type=3)
  service = client.getService('com.brightcove.experience.ExperienceRuntimeFacade')

  pyamf.register_class(ContentOverride, 'com.brightcove.experience.ContentOverride')
  pyamf.register_class(ViewerExperienceRequest, 'com.brightcove.experience.ViewerExperienceRequest')

  video = ContentOverride(videoId)
  experience = ViewerExperienceRequest(playerId, video, url)

  result = service.getDataForExperience('', experience)

  flvUrl = result['programmedContent']['videoPlayer']['mediaDTO']['FLVFullLengthURL']
  return flvUrl
   
