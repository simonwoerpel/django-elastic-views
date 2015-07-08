"""
urls for elastic_views
"""

from django.conf.urls import include, url

from .views import (SimpleElasticQueryView,
                    SimpleElasticQueryJsonView)


urlpatterns = [
    url(r'^json/', 
        SimpleElasticQueryJsonView.as_view(),
        name='elastic-simple-json-result',
    ),
    url(r'^', 
        SimpleElasticQueryView.as_view(),
        name='elastic-simple-result',
    ),
]

