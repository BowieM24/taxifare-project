import requests
USSD_URL = 'http://127.0.0.1:8000/ussd'
def simulate_ussd_step(s_id, phone, text_in):
    p = {'sessionId': s_id, 'serviceCode': '*120*1234#', 'phoneNumber': phone, 'text': text_in}
    return requests.post(USSD_URL, data=p).text
if __name__ == '__main__':
    s = 'session_bree_rank_999'; ph = '+27831234567'
    print('\n[Step 1] Dialing...'); print(simulate_ussd_step(s, ph, ''))
    print('\n[Step 2] Option 1...'); print(simulate_ussd_step(s, ph, '1'))
    print('\n[Step 3] Seat 4...'); print(simulate_ussd_step(s, ph, '1*4'))
    print('\n[Step 4] Confirm...'); print(simulate_ussd_step(s, ph, '1*4*1'))
    print('\n[Step 5] Checking balance (Registered)...'); print(simulate_ussd_step(s, ph, '2'))
    print('\n[Step 6] Checking balance (Unregistered)...'); print(simulate_ussd_step(s, '+27710000000', '2'))
