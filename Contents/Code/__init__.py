import re
import string

VIDEO_PREFIX = "/video/snagfilms"

TITLE = "SnagFilms"
BASE_URL = "http://www.snagfilms.com"

BASE_BROWSE = "http://www.snagfilms.com/films/browse/"
MOST_LIKED = "http://www.snagfilms.com/films/browse/?sort=likes"
NEW_ARIVALS = "http://www.snagfilms.com/films/browse/?sort=newest"
AZ_URL = "http://www.snagfilms.com/films/browse/?sort=alpha&ltr=%s"

ART = 'art-default.jpg'
ICON = 'icon-default.png'

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, TITLE, ICON, ART)
  Plugin.AddViewGroup("InfoList", viewMode = "InfoList", mediaType = "items")
  Plugin.AddViewGroup("List", viewMode = "List", mediaType = "items")

  # Set the default ObjectContainer attributes
  ObjectContainer.title1 = TITLE
  ObjectContainer.view_group = 'List'
  ObjectContainer.art = R(ART)

  # Default icons for DirectoryObject and VideoClipObject in case there isn't an image
  DirectoryObject.thumb = R(ICON)
  DirectoryObject.art = R(ART)
  VideoClipObject.thumb = R(ICON)
  VideoClipObject.art = R(ART)

  HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.16) Gecko/20110319 Firefox/3.6.16"
  HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
def MainMenu():
    oc = ObjectContainer()
    
    oc.add(DirectoryObject(key = Callback(ListItems, title = "Most Liked", url = MOST_LIKED), title = "Most Liked"))
    oc.add(DirectoryObject(key = Callback(ListItems, title = "New Arrivals", url = NEW_ARIVALS), title = "New Arrivals"))
    oc.add(DirectoryObject(key = Callback(Categories, title = "Categories"), title = "Categories"))
    oc.add(DirectoryObject(key = Callback(Channels, title = "Channels"), title = "Channels"))
    oc.add(DirectoryObject(key = Callback(AllFilms, title = "All Films"), title = "All Films"))
    oc.add(SearchDirectoryObject(identifier="com.plexapp.plugins.snagfilms", title = "Search...", prompt = "Search for films", thumb = R(ICON)))

    return oc

####################################################################################################

def Categories(title):
    oc = ObjectContainer(title2 = title)

    page = HTML.ElementFromURL(BASE_BROWSE)
    for category in page.xpath("//ul[@class = 'categories']/li")[1:-1]:
    
        title = category.xpath(".//a")[0].get('title')
        url = BASE_URL + category.xpath(".//a")[0].get('href')
        oc.add(DirectoryObject(key = Callback(ListItems, title = title, url = url), title = title))
    
    return oc

####################################################################################################

def Channels(title):
    oc = ObjectContainer(title2 = title)

    page = HTML.ElementFromURL(BASE_BROWSE)
    for channel in page.xpath("//li[@class='channels']//li/a"):

        title = channel.get('title')
        url = BASE_URL + channel.get('href')
        oc.add(DirectoryObject(key = Callback(ListItems, title = title, url = url), title = title))
    
    return oc

####################################################################################################

def AllFilms(title):
    oc = ObjectContainer(title2 = title)
    
    for letter in list(string.uppercase):
        oc.add(DirectoryObject(key = Callback(ListItems, title = letter, url = AZ_URL % letter), title = letter))
    
    return oc

####################################################################################################

def ListItems(title, url, replace_parent = False):
    oc = ObjectContainer(view_group = 'InfoList', title2 = title, replace_parent = replace_parent)

    # Add all the items currently found on the page.
    page = HTML.ElementFromURL(url)
    for item in page.xpath("//ul[contains(@class, 'films-list')]/li"):
        title = item.xpath(".//h3[@class='title']//text()")[0].strip()
        pageUrl = BASE_URL + item.xpath(".//a")[0].get('href')
        thumb = item.xpath(".//img")[0].get('src')
        summary = item.xpath(".//div[@class='summary']/p/text()")[0].strip()

        date = None
        duration = None
        extra = ''.join(item.xpath(".//div[@class='f-footer']/p/text()")).strip('\n').strip()
        try:
            extra_dict = re.match(".*\((?P<date>[0-9]+)\) (?P<mins>[0-9]+)  mins.*", extra).groupdict()
            date = Datetime.ParseDate(extra_dict['date'])
            duration = int(extra_dict['mins'])
            duration = duration * 60 * 1000
        except: pass
        
        rating_desc = item.xpath(".//span[contains(@class, 'stars')]")[0].get('class')
        rating_dict = re.match(".*s(?P<rating>[0-5]+)", rating_desc).groupdict()
        rating = float(rating_dict['rating']) * 2
        
        oc.add(VideoClipObject(
            url = pageUrl,
            title = title,
            summary = summary,
            thumb = Function(GetThumb, url = thumb),
            duration = duration,
            originally_available_at = date,
            rating = rating
        ))

    # If we find another page, add it so that the user can further navigate.
    next_page = page.xpath("//div[@class = 'pagination']//li[@class = 'next']")
    if len(next_page) > 0:
        next_url = next_page[0].xpath(".//a")[0].get('href')
        oc.add(DirectoryObject(key = Callback(ListItems, title = title, url = BASE_URL + next_url, replace_parent = True), title = "Next..."))
    
    if len(oc) == 0:
        return MessageContainer(title, "No titles were found...")   

    return oc

####################################################################################################

def GetThumb(url):
    try:
        image = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
        return DataObject(image, 'image/jpeg')
    except:
        return Redirect(R(ICON))