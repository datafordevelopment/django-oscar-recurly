from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from oscar.apps.customer.forms import EmailUserCreationForm
from oscar_recurly.admin import *
from oscar_recurly.models import *

from .utils import *

import datetime, decimal, logging, random, recurly

logger = logging.getLogger(__file__)

recurly.SUBDOMAIN = settings.RECURLY_SUBDOMAIN
recurly.API_KEY = settings.RECURLY_API_KEY
recurly.PRIVATE_KEY = settings.RECURLY_PRIVATE_KEY

class TestCase(TestCase):
    account = None
    user = None
    billing_info = None
    plan = None
    subscription = None
    
    def test_recurly_functionality(self):
        random.seed()
        
        # create random user registration.
        email = address_generator().next()
        first_name = gen_name(7)
        last_name = gen_name(8)
        password = 'oscar_recurly'

        registration_form_data = {
            'email': email,
            'password1': password,
            'password2': password
        }
        
        percent_off_coupon_code = percent_off_coupon_name = gen_name(15)
        percent_off = random.randrange(100)
        
        dollar_off_coupon_code = dollar_off_coupon_name = gen_name(15)
        dollar_off = random.randrange(50)
        
        reg_form = EmailUserCreationForm(data=registration_form_data)
        self.user = reg_form.save()
        
        self.user.first_name = first_name
        self.user.last_name = last_name
        self.user.save()
        
        self.account = Account.objects.get(account_code=self.user.username)
        self.assertTrue(self.account.recurly_account.state == 'active')
        self.assertTrue(self.account.hosted_login_url.find(self.account.hosted_login_token) >= 0)
        self.assertTrue(unicode(self.account) == self.account.account_code)

        unit_amount = decimal.Decimal(random.randrange(10000))/100
        quantity = random.randrange(10)
        adjustment = Adjustment.create(self.account, "Unit test.", unit_amount, quantity, 'USD', accounting_code='unittest')
        
        found_adjustment = False
        for recurly_adjustment in self.account.recurly_account.adjustments():
            if recurly_adjustment.uuid == adjustment.uuid: 
                self.assertTrue(recurly_adjustment.state == 'pending')
                found_adjustment = True
                break
        self.assertTrue(found_adjustment)
        
        adjustment = self.account.charge(gen_name(random.randrange(8,20)), decimal.Decimal(random.randrange(10000))/100, random.randrange(10), 'USD', 'adj2')
        found_adjustment = False
        for recurly_adjustment in self.account.recurly_account.adjustments():
            if recurly_adjustment.uuid == adjustment.uuid: 
                self.assertTrue(recurly_adjustment.state == 'pending')
                found_adjustment = True
                break
        self.assertTrue(found_adjustment)
        
        address1 = '{number} {street}'.format(number=random.randrange(20000), street=gen_name(random.randrange(4, 8)))
        address2 = ''
        city = gen_name(random.randrange(4, 8))
        state = 'CA'
        zipcode = '00001'
        country = 'US'
        phone = '123-123-1234'
        vat_number = ''
        ip_address = '127.0.0.1'
        number = '4111111111111111'
        verification_value = '123'
        month = 12
        year = 2020
        self.billing_info = BillingInfo.create(self.account, self.account.first_name, self.account.last_name, self.account.company_name, address1, address2, city, state, zipcode, country, phone, vat_number, ip_address, number, verification_value, month, year)
        self.assertTrue(self.billing_info.recurly_billing_info.last_four == '1111' == self.billing_info.last_four)
        
        self.billing_info.first_name = 'Updated'
        self.billing_info.save()
        self.billing_info.number, self.billing_info.verification_value = '1', '123'
        self.billing_info.save()
        
        plan_code = plan_name = plan_description = plan_accounting_code = gen_name(10)
        self.plan = Plan.create(plan_code, plan_name, plan_description, 39.99, accounting_code=plan_accounting_code)
        self.assertTrue(self.plan.recurly_plan.plan_code == self.plan.plan_code)
        
        plan_code_2 = plan_name_2 = plan_description_2 = plan_accounting_code_2 = gen_name(10)
        plan_2 = Plan.create(plan_code_2, plan_name_2, plan_description_2, 5, accounting_code=plan_accounting_code_2, trial_interval_length=1, setup_fee=2, total_billing_cycles=12, success_url="http://fakeurl.com/", cancel_url="http://fakecancelurl.com/")
        plan_2.unit_amount = 10
        plan_2.save()
        
        percent_off_coupon = Coupon.create(percent_off_coupon_code, percent_off_coupon_name, discount_type='percent', discount_percent=percent_off, hosted_description='hosted coupon description', invoice_description='invoice coupon description', applies_to_all_plans=True, redeem_by_date=timezone.now()+datetime.timedelta(days=1), applies_for_months=3, max_redemptions=10, plan_codes=[plan_code,])
        self.assertTrue(percent_off_coupon.state == percent_off_coupon.recurly_coupon.state == 'redeemable')
        
        dollar_off_coupon = Coupon.create(dollar_off_coupon_code, dollar_off_coupon_name, discount_type='dollars', discount_percent=dollar_off, hosted_description='hosted coupon description', invoice_description='invoice coupon description', applies_to_all_plans=True)
        
        coupon_redemption = CouponRedemption.create(percent_off_coupon, self.account, 'USD')
        self.assertTrue(self.account.recurly_account.redemption().coupon().coupon_code == percent_off_coupon.coupon_code)
        
        invoice = Invoice.create(self.account)
        self.assertTrue(invoice.invoice_number == invoice.recurly_invoice.invoice_number)
        
        self.account.recurly_account.charge(recurly.Adjustment(description='direct charge to account', unit_amount_in_cents=random.randrange(1000), currency='USD', accounting_code='direct'))
        invoice_clean = Invoice.create(self.account)
        
        
        plan_addon_code = addon_name = gen_name(10)
        plan_add_on = PlanAddOn.create(self.plan, plan_addon_code, addon_name, 9.99, default_quantity=1)
        self.assertTrue(plan_add_on.recurly_plan_add_on.add_on_code == plan_add_on.add_on_code)
        plan_add_on.unit_amount = 5
        plan_add_on.save()
        
        # for full coverage of transactions
        transaction = Transaction.create(self.account, decimal.Decimal(random.randrange(10000))/100, 'USD', 'unit test transaction')
        
        self.subscription = Subscription.create(self.plan, self.account)
        self.assertTrue(self.subscription.uuid == self.subscription.recurly_subscription.uuid)
        self.subscription.recurly_subscription.terminate(refund='none')
        
        self.subscription = Subscription.create(self.plan, self.account, [plan_addon_code,], coupon_code=dollar_off_coupon_code, unit_amount=50.01, trial_ends_at=timezone.now()+datetime.timedelta(days=7), starts_at=timezone.now()+datetime.timedelta(days=1), total_billing_cycles=12, first_renewal_date=timezone.now()+datetime.timedelta(days=2))
        self.assertTrue(self.subscription.uuid == self.subscription.recurly_subscription.uuid)
        
        self.subscription.unit_amount = 60
        self.subscription.save()
        
        transaction = Transaction.create(self.account, decimal.Decimal(random.randrange(10000))/100, 'USD', 'unit test transaction')
        self.assertTrue(transaction.uuid == transaction.recurly_transaction.uuid)
        
        
        
        # clean up recurly stuff when finished.
        self.account.recurly_account.delete()
        self.plan.recurly_plan.delete()
        plan_2.recurly_plan.delete()
        dollar_off_coupon.recurly_coupon.delete()
        percent_off_coupon.recurly_coupon.delete()
        self.user.delete()