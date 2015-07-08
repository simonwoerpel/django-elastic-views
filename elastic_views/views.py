from django.conf import settings
from django.http import Http404, JsonResponse
from django.views.generic import TemplateView, View
from django.utils.functional import cached_property

from .connection import CONNECTION as E
from .utils import FakedListPaginator, FakedPaginatedViewMixin


class BaseSimpleElasticView(FakedPaginatedViewMixin):
    """
    simple view that queries Elasticsearch 
    based on keywords via get Parameter 'q'

    search results will occur as object_list in templates
    """
    index = settings.ELASTICSEARCH['DEFAULT_INDEX']
    paginate_by = 50
    query_template = {
        "query":{
            "bool":{
                "must":[{
                    "query_string":{
                        "default_field":"_all",
                        "query": None,
                    }
                }],
                "must_not":[],
                "should":[]
            }
        },
        "from":0,
        "size":None,
        "sort":[],
        "facets":{}
    }

    # def __init__(self, *args, **kwargs):
    #     """
    #     do the Elastic query at initializing
    #     to have the self.result 
    #     """
    #     super().__init__(*args, **kwargs)
    #     self.result = self.get_query_result()

    def get_index(self):
        """
        may be overriden
        """
        return self.index

    def get_paginate_by(self):
        """
        may be overriden
        """
        return self.paginate_by

    def get_query_template(self):
        """
        may be overriden
        """
        return self.query_template

    def get_query_term(self):
        """
        what should happen if q is null?
        default: 404
        """
        q = self.request.GET.get('q', None)
        if not q:
            raise Http404
        return q

    def get_query(self):
        """
        may be overriden
        """
        query = {
            "query":{
                "bool":{
                    "must":[{
                        "query_string":{
                            "default_field":"_all",
                            "query": self.get_query_term(),
                        }
                    }],
                    "must_not":[],
                    "should":[]
                }
            },
            "from":self.range_start,
            "size": self.get_paginate_by(),
            "sort":[],
            "facets":{}
        }

        return query

    def get_query_result(self, *args, **kwargs):
        """
        fetches results from Elasticsearch
        """
        result = E.search(index=self.get_index(), body=self.get_query())
        return result

    @cached_property
    def result(self):
        return self.get_query_result()

    @property
    def total_results(self):
        return self.result['hits']['total']

    def get_total_num(self):
        """
        for FakedPagination
        """
        return self.total_results

    def get_result_object_url(self, row):
        """
        may be overriden

        if implemented, the return of this method will be used
        to add a 'get_absoulte_url' attr to the objects
        """
        return None

    def get_result_object_name(self, row):
        """
        may be overriden

        if implemented, this will be the display value in the
        default result list
        """
        return None

    def get_result_object(self, row):
        """
        will be runned for each row in self.get_query_result
        """
        url = self.get_result_object_url(row)
        name = self.get_result_object_name(row)

        if name and url:
            return {'score': row['_score'],
                    'name': name,
                    'get_absolute_url': url}
        return {'score': row['_score'],
                'id': row['_id']}

    def get_processed_result_rows(self):
        """
        do something with the rows, if necessary
        may be overriden
        """
        result = self.result

        return [self.get_result_object(r) 
                for r in result['hits']['hits']]

    def get_data(self):
        """
        will be passed to context data in TemplateView,
        or as JsonResponse in JsonView
        """
        return {
            'object_list': self.get_processed_result_rows(),
            'total_results': self.total_results,
            'elastic_index': self.get_index(),
            'elastic_query': self.get_query_term(),
            'page': self.page,
            'range_start': self.range_start,
            'range_end': self.range_end,
        }


class SimpleElasticQueryView(BaseSimpleElasticView, 
                             TemplateView):

    template_name = 'elastic_views/simple_result.html'

    def get_context_data(self, *args, **kwargs):
        """
        adds object_list to the context
        """
        context = super().get_context_data(*args, **kwargs)
        context.update(self.get_data())

        return context


class SimpleElasticQueryJsonView(BaseSimpleElasticView, View):

    def get(self, *args, **kwargs):
        return JsonResponse({'data': self.get_data()})

