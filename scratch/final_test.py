import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'khatabook.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

print('=== SHOPKEEPER DASHBOARD TEST ===')
c = Client()
user = User.objects.get(username='testshop2')
c.force_login(user)

pages = [
    ('/', 'Dashboard'),
    ('/expenses/', 'Expenses'),
    ('/subscriptions/', 'Subscriptions'),
    ('/settings/', 'Settings'),
    ('/bill/', 'Bill Select'),
    ('/drivers/', 'Drivers'),
    ('/milkorder/', 'Milk Orders'),
    ('/transactions/', 'Transactions'),
    ('/report/daily/', 'Daily Report'),
    ('/customers/', 'Customers'),
    ('/shop/deliveries/', 'Delivery Dashboard'),
    ('/shop/pending-orders/', 'Pending Orders'),
]

all_ok = True
for url, name in pages:
    r = c.get(url, follow=True)
    ok = r.status_code == 200
    if not ok:
        all_ok = False
    status = 'OK' if ok else 'FAIL'
    print(f'  {status} ({r.status_code}) - {name} [{url}]')

print('')
print('=== CUSTOMER PORTAL TEST ===')
c2 = Client()
r = c2.post('/c/login/', {'phone': '9876543210', 'password': 'password123'}, follow=True)
status = 'OK' if r.status_code == 200 else 'FAIL'
print(f'  Customer login: {status}')

customer_pages = [
    ('/c/dashboard/', 'Dashboard'),
    ('/c/my-orders/', 'My Orders'),
    ('/c/statement/', 'Statement'),
    ('/c/order/', 'Place Order'),
]
for url, name in customer_pages:
    r = c2.get(url, follow=True)
    ok = r.status_code == 200
    if not ok:
        all_ok = False
    status = 'OK' if ok else 'FAIL'
    print(f'  {status} ({r.status_code}) - {name} [{url}]')

print('')
if all_ok:
    print('OVERALL RESULT: ALL TESTS PASSED!')
else:
    print('OVERALL RESULT: SOME TESTS FAILED')
