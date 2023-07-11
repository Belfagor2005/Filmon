#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
PY3 = sys.version_info.major >= 3
print("Update.py")


def upd_done():
    from os import popen, remove
    cmd01 = "wget http://patbuweb.com/filmon/filmon.tar -O /tmp/filmon.tar ; tar -xvf /tmp/filmon.tar -C /"
    cmd02 = "wget --no-check-certificate -U 'Enigma2 - filmon Plugin' -c 'http://patbuweb.com/filmon/filmon.tar' -O '/tmp/filmon.tar'; tar -xvf /tmp/filmon.tar -C /"
    cmd22 = 'find /usr/bin -name "wget"'
    res = popen(cmd22).read()
    if 'wget' not in res.lower():
        cmd23 = 'apt-get update && apt-get install wget'
        popen(cmd23)
    try:
        popen(cmd02)
    except:
        popen(cmd01)
    remove('/tmp/filmon.tar')
    return

'''

import os
import sys
PY3 = sys.version_info.major >= 3
print("Update.py")


def upd_done():
    from twisted.web.client import downloadPage
    print("In upd_done")
    xfile = 'http://patbuweb.com/filmon/filmon.tar'
    if PY3:
        xfile = b"http://patbuweb.com/filmon/filmon.tar"
        print("Update.py in PY3")
    import requests
    response = requests.head(xfile)
    if response.status_code == 200:
        # print(response.headers['content-length'])
        fdest = "/tmp/filmon.tar"
        print("Code 200 upd_done xfile =", xfile)
        downloadPage(xfile, fdest).addCallback(upd_last)
    elif response.status_code == 404:
        print("Error 404")
    else:
        return


def upd_last(fplug):
    import os
    import time
    time.sleep(5)
    if os.path.exists('/tmp/filmon.tar') and os.stat('/tmp/filmon.tar').st_size > 100:
        cmd = "tar -xvf /tmp/filmon.tar -C /"
        print("cmd A =", cmd)
        os.system(cmd)
        os.remove('/tmp/filmon.tar')
    return
'''