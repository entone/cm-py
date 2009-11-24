from campaign_monitor import *

user = User()

clis = user.GetClients()

print clis

cid = clis[0].get('ClientID')

cli = Client(ClientID=cid)

lists = cli.GetLists()

listid = lists[2].get('ListID')

camp = Campaign()

camp.Create(ClientID=cid, CampaignName='Let\'s do this!', CampaignSubject='WOOT!', FromName='Chris', FromEmail='yowza@woot.com', ReplyTo='test@test.com', HtmlUrl='http://98.193.98.74/', TextUrl='http://98.193.98.74/', SubscriberListIDs=[{'string':listid}])

