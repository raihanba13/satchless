import os

from django.conf.urls.defaults import patterns, include, url
from django.core.urlresolvers import reverse, NoReverseMatch
from django.test import TestCase

from ...util.tests import ViewsTestCase
from ...product.tests import DeadParrot

from ..models import Category
from ..app import product_app, CategorizedProductApp

__all__ = ['Views', 'Models', 'CategorizedProductUrlTests',
           'NonCategorizedProductUrlTests']


class urls:
    urlpatterns = patterns('',
        url(r'^products/', include(product_app.urls)),
    )


class Views(ViewsTestCase):
    urls = urls

    def setUp(self):
        self.animals = Category.objects.create(slug='animals', name=u'Animals')
        self.birds = Category.objects.create(slug='birds', name=u'Birds',
                                             parent=self.animals)
        self.parrots = Category.objects.create(slug='parrots', name=u'Parrorts',
                                               parent=self.birds)
        test_dir = os.path.dirname(__file__)
        self.custom_settings = {
            'TEMPLATE_DIRS': (os.path.join(test_dir, '..', 'templates'),
                              os.path.join(test_dir, 'templates')),
        }
        self.original_settings = self._setup_settings(self.custom_settings)

    def tearDown(self):
        self._teardown_settings(self.original_settings,
                                self.custom_settings)

    def test_category_list(self):
        self._test_GET_status(reverse('product:category-index'))

    def test_category_details(self):
        response = self._test_GET_status(self.animals.get_absolute_url())
        self.assertTrue('category' in response.context)
        self.assertEqual(response.context['category'], self.animals)

        response = self._test_GET_status(self.parrots.get_absolute_url())
        self.assertTrue('category' in response.context)
        self.assertEqual(response.context['category'], self.parrots)

    def test_category_product_view(self):
        parrot_macaw = DeadParrot.objects.create(slug='macaw', species='Hyacinth Macaw')
        self.animals.products.add(parrot_macaw)
        self.parrots.products.add(parrot_macaw)
        response = self._test_GET_status(parrot_macaw.get_absolute_url(category=self.animals))
        self.assertTrue('product' in response.context)
        self.assertEqual(response.context['product'], parrot_macaw)

        self._test_GET_status(parrot_macaw.get_absolute_url(category=self.parrots))
        self.assertTrue('product' in response.context)
        self.assertEqual(response.context['product'], parrot_macaw)


class Models(TestCase):

    def setUp(self):
        self.animals = Category.objects.create(slug='animals', name=u'Animals')
        self.birds = Category.objects.create(slug='birds', name=u'Birds',
                                             parent=self.animals)
        self.parrots = Category.objects.create(slug='parrots', name=u'Parrorts',
                                               parent=self.birds)

    def test_paths(self):
        birds = Category.objects.create(slug='birds', name=u'Birds')
        storks = Category.objects.create(slug='storks', name=u'Storks', parent=birds)
        forks = Category.objects.create(slug='forks', name=u'Forks', parent=storks)
        Category.objects.create(slug='porks', name=u'Porks', parent=forks)
        borks = Category.objects.create(slug='borks', name=u'Borks', parent=forks)
        forks2 = Category.objects.create(slug='forks', name=u'Forks', parent=borks)
        yorks = Category.objects.create(slug='yorks', name=u'Yorks', parent=forks2)
        Category.objects.create(slug='orcs', name=u'Orcs', parent=forks2)
        self.assertEqual(
                [birds, storks, forks],
                product_app.path_from_slugs(['birds', 'storks', 'forks']))
        self.assertEqual(
                [birds, storks, forks, borks, forks2],
                product_app.path_from_slugs(['birds', 'storks', 'forks', 'borks', 'forks']))
        self.assertRaises(
                Category.DoesNotExist,
                product_app.path_from_slugs,
                (['birds', 'storks', 'borks', 'forks']))
        self.assertEqual(
                [birds, storks, forks, borks, forks2, yorks],
                product_app.path_from_slugs(['birds', 'storks', 'forks', 'borks', 'forks', 'yorks']))
        self.assertRaises(
                Category.DoesNotExist,
                product_app.path_from_slugs,
                (['birds', 'storks', 'forks', 'porks', 'forks', 'yorks']))


class CategorizedProductUrlTests(TestCase):
    urls = urls

    def setUp(self):
        self.animals = Category.objects.create(slug='animals', name=u'Animals')
        self.birds = Category.objects.create(slug='birds', name=u'Birds',
                                             parent=self.animals)
        self.parrots = Category.objects.create(slug='parrots', name=u'Parrorts',
                                               parent=self.birds)
        self.parrot_macaw = DeadParrot.objects.create(slug='macaw',
                                                 species='Hyacinth Macaw')

    def test_categorised_product_url(self):
        self.animals.products.add(self.parrot_macaw)
        self.assertTrue('/products/animals/+macaw/' in self.parrot_macaw.get_absolute_url())

    def test_second_tier_categorised_product_url(self):
        self.birds.products.add(self.parrot_macaw)
        self.assertTrue('/products/animals/birds/+macaw/' in self.parrot_macaw.get_absolute_url())

    def test_third_tier_categorised_product_url(self):
        self.parrots.products.add(self.parrot_macaw)
        self.assertTrue('/products/animals/birds/parrots/+macaw/' in self.parrot_macaw.get_absolute_url())

    def test_product_url(self):
        """Products not in a Category should raise an exception."""
        self.assertRaises(NoReverseMatch, self.parrot_macaw.get_absolute_url)


class CategorizedProductAppWithOrphans(CategorizedProductApp):
    """A CategorizedProductApp that allows Products not in Categories"""

    allow_uncategorized_product_urls = True


class NonCategorizedProductUrlTests(TestCase):
    """Urls include satchless-product-details"""

    class urls:
        urlpatterns = patterns('',
            url(r'^products/',
                include(CategorizedProductAppWithOrphans().urls)),
        )

    def setUp(self):
        self.animals = Category.objects.create(slug='animals', name=u'Animals')
        self.birds = Category.objects.create(slug='birds', name=u'Birds',
                                             parent=self.animals)
        self.parrots = Category.objects.create(slug='parrots', name=u'Parrorts',
                                               parent=self.birds)
        self.parrot_macaw = DeadParrot.objects.create(slug='macaw',
                                                 species='Hyacinth Macaw')

    def test_categorised_product_url(self):
        self.animals.products.add(self.parrot_macaw)
        self.assertTrue('/products/animals/+macaw/' in
                        self.parrot_macaw.get_absolute_url())

    def test_second_tier_categorised_product_url(self):
        self.birds.products.add(self.parrot_macaw)
        self.assertTrue('/products/animals/birds/+macaw/' in
                        self.parrot_macaw.get_absolute_url())

    def test_third_tier_categorised_product_url(self):
        self.parrots.products.add(self.parrot_macaw)
        self.assertTrue('/products/animals/birds/parrots/+macaw/' in
                        self.parrot_macaw.get_absolute_url())

    def test_product_url(self):
        """Products not in a Category should have a url."""
        self.assertTrue('/products/+1-macaw/' in
                        self.parrot_macaw.get_absolute_url())
