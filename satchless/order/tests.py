# -*- coding: utf-8 -*-
from decimal import Decimal
import os

from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import Client

from satchless.pricing import handler
from satchless.product.tests import DeadParrot
from satchless.product.tests.pricing import FiveZlotyPriceHandler
from satchless.cart.models import Cart
from .app import order_app
#from . import models
#from . import urls
from ..util.tests import ViewsTestCase

class OrderTest(ViewsTestCase):
    class urls:
        urlpatterns = patterns('',
            url(r'^order/', include(order_app.urls)),
        )

    def setUp(self):
        self.macaw = DeadParrot.objects.create(slug='macaw',
                species="Hyacinth Macaw")
        self.cockatoo = DeadParrot.objects.create(slug='cockatoo',
                species="White Cockatoo")
        self.macaw_blue = self.macaw.variants.create(color='blue',
                                                     looks_alive=False)
        self.macaw_blue_fake = self.macaw.variants.create(color='blue',
                                                          looks_alive=True)
        self.cockatoo_white_a = self.cockatoo.variants.create(color='white',
                                                              looks_alive=True)
        self.cockatoo_white_d = self.cockatoo.variants.create(color='white',
                                                              looks_alive=False)
        self.cockatoo_blue_a = self.cockatoo.variants.create(color='blue',
                                                             looks_alive=True)
        self.cockatoo_blue_d = self.cockatoo.variants.create(color='blue',
                                                             looks_alive=False)
        self.anon_client = Client()

        self.original_handlers = settings.SATCHLESS_PRICING_HANDLERS
        handler.pricing_queue = handler.PricingQueue(FiveZlotyPriceHandler)
        app_dir = os.path.dirname(__file__)
        self.custom_settings = {
            'SATCHLESS_PRODUCT_VIEW_HANDLERS': ('satchless.cart.add_to_cart_handler',),
            'TEMPLATE_DIRS': [os.path.join(app_dir, 'templates'),
                              os.path.join(app_dir, '..', 'product',
                                           'tests', 'templates')]
        }
        self.original_settings = self._setup_settings(self.custom_settings)

    def tearDown(self):
        handler.pricing_queue = handler.PricingQueue(*self.original_handlers)
        self._teardown_settings(self.original_settings,
                                self.custom_settings)

    def test_order_is_updated_when_cart_content_changes(self):
        cart = Cart.objects.create(typ='satchless.test_cart')
        cart.set_quantity(self.macaw_blue, 1)

        order = order_app.order_model.objects.get_from_cart(cart)

        cart.set_quantity(self.macaw_blue_fake, Decimal('2.45'))
        cart.set_quantity(self.cockatoo_white_a, Decimal('2.45'))

        order_items = set()
        for group in order.groups.all():
            order_items.update(group.items.values_list('product_variant',
                                                       'quantity'))
        self.assertEqual(set(cart.items.values_list('variant', 'quantity')),
                         order_items)

    def test_order_view(self):
        cart = Cart.objects.create(typ='satchless.test_cart')
        cart.set_quantity(self.macaw_blue, 1)
        cart.set_quantity(self.macaw_blue_fake, Decimal('2.45'))
        cart.set_quantity(self.cockatoo_white_a, Decimal('2.45'))

        order = order_app.order_model.objects.get_from_cart(cart)
        self._test_GET_status(reverse('satchless-order-view',
                                      args=(order.token,)))
