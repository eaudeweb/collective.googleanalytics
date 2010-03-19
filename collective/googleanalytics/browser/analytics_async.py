from zope.interface import implements
from zope.publisher.browser import BrowserPage
from plone.memoize.instance import memoize
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics.interfaces.async import IAnalyticsAsyncLoader
from collective.googleanalytics import error
from string import Template
import md5
import time
import os

class DefaultAnalyticsAsyncLoader(object):
    
    implements(IAnalyticsAsyncLoader)
    
    def __init__(self, context):
        self.context = context
    
    @memoize
    def getContainerId(self):
        random_id = md5.new()
        random_id.update(str(time.time()))
        return 'analytics-%s' % random_id.hexdigest()
    
    def getJavascript(self, report_ids, profile_id, date_range='month', container_id=None):
        if not report_ids or not profile_id:
            return ''
            
        if not container_id:
            container_id = self.getContainerId()
            
        analytics_tool = getToolByName(self.context, 'portal_analytics')
        reports = []
        packages = []
        for report_id in report_ids:
            try:
                report = analytics_tool[report_id]
                reports.append(report_id)
                package = report.viz_type.lower()
                if not package in packages:
                    packages.append(package)
            except KeyError:
                continue
                
        url_tool = getToolByName(self.context, 'portal_url')
        portal_url = url_tool.getPortalObject().absolute_url()
        
        template_file = os.path.join(os.path.dirname(__file__), 'analytics_async_loader.js.tpl')
        template = Template(open(template_file).read())
        
        template_vars = {
            'visualization_packages': '[%s]' % ', '.join(["'%s'" % p for p in packages]), 
            'container_id': container_id, 
            'report_ids': '[%s]' % ', '.join(["'%s'" % r for r in reports]), 
            'profile_id': profile_id,
            'portal_url': portal_url,
            'request_url': self.context.request.ACTUAL_URL, 
            'date_range': date_range,
        }
            
        return template.substitute(template_vars)

class AsyncAnalyticsResults(BrowserPage):
    """
    Returns a HTML snippet for report results to be inserted dynamically
    in the page.
    """
    
    __call__ = ViewPageTemplateFile('analytics_async.pt')
    
    def getResults(self):
        """
        Returns a list of AnalyticsReportResults objects for the selected reports.
        """        
        report_ids = self.request.get('report_ids', [])
        profile_id = self.request.get('profile_id', '')
        if type(report_ids) is str:
              report_ids = [report_ids]
        
        if not report_ids and profile_id:
            return []
            
        date_range = self.request.get('date_range', 'month')
        request_url = self.request.get('request_url', None)
        if request_url:
            self.context.request.ACTUAL_URL = request_url
        
        analytics_tool = getToolByName(self.context, 'portal_analytics')
        
        results = []
        for report_id in report_ids:
            try:
                report = analytics_tool[report_id]
            except KeyError:
                continue
                
            try:
                results.append(report.getResults(self.context, profile_id, date_range=date_range))
            except error.BadAuthenticationError:
                return 'BadAuthenticationError'
            except error.MissingCredentialsError:
                return 'MissingCredentialsError'
                
        return results