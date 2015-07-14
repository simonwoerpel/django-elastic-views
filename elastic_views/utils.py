"""
utils for elastic_views
"""

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class FakedListPaginator(Paginator):
    """
    wrapper for `django.core.paginator.Paginator`
    for paginating only the count of a list, not the 
    list itself.
    it creates a faked list based on the count param
    that the django Paginator uses to work with
    """
    
    def __init__(self, count, per_page):
        objects = range(0, count)
        super().__init__(objects, per_page)


class FakedPaginatedViewMixin(object):
    """
    a mixin for django class based views that
    provides pagination based on the FakedListPaginator
    it has properties like range that can be used
    for the "real" list on which will be paginated on

    this view accepts a 'p' in GET, unless defined different
    in subclassing
    """
    page_get_parm = 'p'
    total_num = None
    paginate_by = 25

    def get_page_get_param(self):
        """
        may be overidden
        """
        return self.page_get_parm

    def get_paginate_by(self):
        """
        may be overriden
        """
        return self.limit

    def get_total_num(self):
        """
        must be overriden!
        """
        raise ImproperlyConfigured(
            '%s must have a get_total_num method for pagination'\
             % self.__class__.__name__
        )

    def get_page_num(self):
        """
        default page is 1

        may be overriden
        """
        try:
            page_num = int(self.request.GET.get(self.get_page_get_param(), 1))
        except ValueError:
            page_num = 1

        if page_num <= 0:
            return 1
        return page_num

    def get_paginator(self):
        """
        returns the `FakedListPaginator` based on self.get_total_num()
        and self.get_paginate_by()

        may be overriden
        """
        return FakedListPaginator(self.get_total_num(), self.get_paginate_by())

    @property
    def page(self):
        p = self.get_page_num()
        try:
            page = self.get_paginator().page(p)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            page = self.get_paginator().page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            page = self.get_paginator().page(self.get_paginator().num_pages)

        return page

    @property
    def next_page_url(self):
        pass

    @property
    def prev_page_url(self):
        pass

    def get_range(self):
        """
        returns tuple of (start, end) index
        based on self.get_paginate_by() and self.total_num()
        
        may be overriden
        """
        
        start = (self.get_page_num()-1) * self.get_paginate_by()
        end = start+self.get_paginate_by()

        # FIXME ("recursive depth max exceeded")
        # start = min(self.get_paginator().object_list)
        # end = max(self.get_paginator().object_list)

        return (start, end)

    @property
    def range_start(self):
        return self.get_range()[0]

    @property
    def range_end(self):
        return self.get_range()[1]

