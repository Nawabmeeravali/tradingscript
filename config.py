login_id = "userid"
password = "yourpassword"
twofa = "xx"

try:
    access_token = open('access_token.txt', 'r').read().rstrip()
except Exception as e:
    print('Exception occurred :: {}'.format(e))
    access_token = None