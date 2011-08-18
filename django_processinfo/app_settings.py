# coding:utf-8

"""   
    django-processinfo app settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    All own settings for the django-processinfo app.
    
    **IMPORTANT:**
        You should not edit this file!
        
    Add this into your settings.py:
    
        from django_processinfo import app_settings as PROCESSINFO
        PROCESSINFO.ADD_INFO = True # e.g. to change a settings    

    
    :copyleft: 2011 by the django-processinfo team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

# Should the django-processinfo "time cost" info inserted in a html page?
ADD_INFO = False

# Substring for replace with INFO_FORMATTER
INFO_SEARCH_STRING = "</body>"
INFO_FORMATTER = "<small><p>django-processinfo: %.1f ms</p></small></body>"

