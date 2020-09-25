import os
import hmac

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# caclulate hmac digest of payload with webhook secret token
def calc_signature(payload):
    digest = hmac.new(key=WEBHOOK_SECRET.encode('utf-8'), msg=payload, digestmod='sha1').hexdigest()
    return f'sha1={digest}'
