import os
import time
import hmac, hashlib
import urllib.parse
import urllib.request
import ssl
import json

os.environ['TZ'] = 'GMT+0'

datetime=time.strftime('%y%m%d')+'T'+time.strftime('%H%M%S')+'Z'
method = "POST"

path = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"

message = datetime+method+path

#replace with your own accesskey
accesskey = "****"
#replace with your own secretKey
secretkey = "****"

#********************************************************#
#authorize, demonstrate how to generate hmac signature here
signature=hmac.new(secretkey.encode('utf-8'),message.encode('utf-8'),hashlib.sha256).hexdigest()
authorization  = "CEA algorithm=HmacSHA256, access-key="+accesskey+", signed-date="+datetime+", signature="+signature
#print out the hmac key
#print(authorization)
#********************************************************#

# ************* SEND THE REQUEST *************
url = "https://api-gateway.coupang.com"+path