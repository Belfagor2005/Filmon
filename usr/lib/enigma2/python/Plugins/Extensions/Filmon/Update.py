#!/usr/bin/python
# -*- coding: utf-8 -*-

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
