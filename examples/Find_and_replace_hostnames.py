#Search through arcgisonline/Portal site and replace multiple references
#to hostnames, for any user. Requires an admin account.

#imports
import portalpy
from portalpy import Portal, parse_hostname, normalize_url
from pprint import pprint
from getpass import getpass

#define functions
def build_user_query(userlist):
    if len(userlist) > 0:
        return "(" + " OR ".join(["owner:" + user for user in userlist]) + ")"
    else:
        return ''

#use this function to find and report hostname references
def find_hostname_references(fslist, wmlist, hostname, portalObject, users_to_process):
    portal = portalObject
    hostname_references = []

    #find url-based items and check for hostname specified
    url_items = portal.search(['id','type','url'], portalpy.URL_ITEM_FILTER + " AND " + build_user_query(users_to_process),num=10000)
    if url_items:
        print "{} URL-based items found matching user list".format(len(url_items))
        for item in url_items:
            if parse_hostname(item['url'], include_port=True) == hostname:
                fslist.append((item['id'], item['type'], item['url']))
        print "{} total URL-based items found with hostname references".format(len(hostname_references))

    #find webmap items and check for hostname specified within the layers of the webmap
    print "searching webmaps, this may take some time"
    webmaps = portal.webmaps(build_user_query(users_to_process))
    if webmaps:
        print "{} webmaps found matching user list".format(len(webmaps))
        for webmap in webmaps:
            urls = webmap.urls(normalize=True)
            contains_update_layer = False
            for url in urls:
                if parse_hostname(url, include_port=True) == hostname:
                    contains_update_layer = True
            if contains_update_layer:
                wmlist.append((webmap.id, 'Web Map', url))
            print "{} total web maps found with hostname references".format(len(wmlist))

def update_hostname_references_wm(old_hostname, new_hostname, portalObject, users_to_process):
    portal = portalObject
    hostname_map = {old_hostname:new_hostname}
    webmaps = portal.webmaps(build_user_query(users_to_process))
    if webmaps:
        print "checking {} webmaps for users".format(len(webmaps))
        for webmap in webmaps:
            is_update = False
            for url in webmap.urls():
                normalized_url = normalize_url(url)
                host = parse_hostname(normalized_url, include_port=True)
                if host in hostname_map:
                    new_url = normalized_url.replace(host, hostname_map[host])
                    webmap.data = webmap.data.replace(url, new_url)
                    if http_to_https:
                        webmap.data = webmap.data.replace("http:","https:")
                    is_update = True
            if is_update:
                print "updating web map: " + str(webmap.info()['id'])
                wmlist.append(webmap.info()['id'])
                portal.update_webmap(webmap)

def update_hostname_references_fs(old_name, new_name, portalObject, users_to_process):
    portal = portalObject
    hostname_map = {old_name:new_name}
    url_items = portal.search(['id','type','url'], portalpy.URL_ITEM_FILTER + " AND " + build_user_query(users_to_process))
    if url_items:
        # find and update feature services and map services
        print "checking {} URL-based items".format(len(url_items))
        count = 0
        for item in url_items:
            count += 1
            if count%10 == 0:print "processed {} items".format(count)
            url = item.get('url')
            id = item.get('id')
            #if portal.user_item(id)[0]['owner'] not in users_to_process:
            #    break
            if url:
                url = normalize_url(url)
                host = parse_hostname(url, include_port=True)
                if host in hostname_map:
                    fslist.append(id)
                    print "updating item: " + id
                    url = url.replace(host, hostname_map[host])
                    portal.update_item(item['id'], {'url': url})
        print "done updating URL-based items"

portalName = 'https://a.b.c/arcgis'
user = 'slibby'
password = getpass()
hostname = "oldServer"
http_to_https = True


OrgAccess = portalpy.Portal(portalName, user, password)
users = OrgAccess.org_users(['username', 'fullName'], num=2000)
print "\nThere are currently {} user accounts on {}.".format(len(users), portalName)
NumServices = 0
Total = 0
guids = []
usercount = 0
fslist = []
wmlist = []
#users_to_process = [i['username'] for i in users[20:50]]
user_count = 0
while len(users)>0:
    users_to_process = [user['username'] for user in users[:10]]
    print users_to_process
    users = users[10:] #run 10 users' content at a time
    print str(len(users)) + " remaining users"
    print "starting users " + str(user_count) + " to " + str(user_count+10)
    find_hostname_references(fslist, wmlist, hostname, OrgAccess, users_to_process)
    update_hostname_references_fs("wdc-web-psdmz-p01:6080", "wdc-web-psdmz-p01.esri.com", OrgAccess, users_to_process)
    update_hostname_references_wm("services.arcgisonline.com","services.arcgisonline.com", OrgAccess, users_to_process)
    print "fslist: " + str(fslist) + "\n" + "wmlist: " + str(wmlist)
    Total += len(wmlist)

    print "Total number of feature services needing updating on {} is: {}".format(portalName, len(fslist))
    print "Total number of web maps needing updating on {} is: {}".format(portalName, len(wmlist))
    user_count += 10
