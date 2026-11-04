import urllib.request, sys, ssl
try:
    resp = urllib.request.urlopen('http://127.0.0.1:8000/docs')
    print('Status', resp.status)
except Exception as e:
    print('Error', e)
