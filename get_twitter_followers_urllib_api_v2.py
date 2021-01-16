import urllib.request, csv, datetime, getopt, io, json, os, sys, time

import siaskynet as skynet

# create a client
client = skynet.SkynetClient()

follow = []

parameters_set = False
following_switch = False
handle = None
mode = ''

#instructions to save your keys to json may be found here: https://stackabuse.com/accessing-the-twitter-api-with-python/
with open('twitter_credentials.json') as f:
  data = json.load(f)

#set urllib request header
headers = {'Authorization': 'Bearer '+data['Bearer Token']}

def main(argv):#https://www.tutorialspoint.com/python/python_command_line_arguments.htm
   global handle
   global following_switch
   global parameters_set
   parameters_set = True
   try:
      opts, args = getopt.getopt(argv,"hu:f",["username="])
   except getopt.GetoptError:
      print('get_twitter_followers_urllib_v2_api.py -u <Twitter username> -f <optional switch to get following>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print('get_twitter_followers_urllib_v2_api.py -u <Twitter username> -f <optional switch to get following>')
         sys.exit()
      elif opt in ("-u", "--username"):
         handle = arg
      elif opt in ("-f", "--following"):
         following_switch = True
         mode = 'following'
   print('Twitter user is "', handle)
   if(following_switch):
       print('Following switch is ON')

def export_csv(name,dict_data): #saves follower or following data as csv
    cwd = os.getcwd()
    filename=datetime.datetime.now().strftime(name+"%Y%m%d-%H%M%S.csv")
    outfile=io.open(cwd+'/'+filename,'w',encoding="utf-8")
    writer=csv.DictWriter(outfile, delimiter=',', lineterminator='\n', fieldnames=['id', 'name', 'username'])
    writer.writeheader()
    writer.writerows(dict_data)
    return outfile.name

def useridlookup(username): #returns user id for given username
    url = "https://api.twitter.com/2/users/by?usernames="+username
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        the_page = response.read()
    string = the_page.decode('utf-8')
    json_obj = json.loads(string)
    json_data = json_obj['data']
    return json_data[0]['id']

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        main(sys.argv[1:])
    if parameters_set == False:
        print("1: Following")
        print("2: Followers")
        inp = int(input("Enter Follower / Following Option: "))
        if inp == 1:
            following_switch = True
            mode = 'following'
        elif inp == 2:
            following_switch = False
            mode = 'followers'
        else:
            print("Invalid Input")
            sys.exit()
    if not handle:
        handle = input('Enter Twitter handle?')
    id = useridlookup(handle) #alex_d_281 23563628
    if following_switch:
        url= "https://api.twitter.com/2/users/"+id+"/following?max_results=1000"
    else:
        url= "https://api.twitter.com/2/users/"+id+"/followers?max_results=1000"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
       the_page = response.read()
    string = the_page.decode('utf-8') #begin process for json conversion
    json_obj = json.loads(string)
    json_data = json_obj['data']
    for obj in json_data: #save json as list
        follow.append(obj)
    time.sleep(60) #sleep a minute to accomodate Twitter API rate limits
    while 'next_token' in json_obj['meta'].keys(): #obtain all pages of follower / following data using next token
        if(following_switch):
            url= "https://api.twitter.com/2/users/"+id+"/following?pagination_token="+json_obj['meta']['next_token']+"&max_results=1000"
        else:
            url= "https://api.twitter.com/2/users/"+id+"/followers?pagination_token="+json_obj['meta']['next_token']+"&max_results=1000"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
           the_page = response.read()
        string = the_page.decode('utf-8')
        json_obj = json.loads(string)
        json_data = json_obj['data']
        for obj in json_data:
            follow.append(obj)
        for f in follow: # sometimes the withheld field will exist which may contain country data. removing to avoid dictwriter errors in export
            if 'withheld' in f.keys():
                del f['withheld']
        time.sleep(60)
    csvfilename = export_csv(handle+'_'+mode,follow) #save to csv on disk
    skylink = client.upload_file(csvfilename) #upload to siaskynet siacoin skynet portal
    skylink_url = "https://siasky.net/"+skylink.replace("sia://","") # modify url for web browsing
    print("Upload successful, skylink: " + skylink_url)