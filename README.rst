django-template-mixins
======================

.. image:: https://img.shields.io/pypi/v/django-template-mixins.svg
    :target: https://pypi.org/project/django-template-mixins


A template filter that allows you to define and use mixins.

Installation
~~~~~~~~~~~~

In your Django project, run::

 pip install django-template-mixins

and add mixin_templatetag to your `INSTALLED_APPS` setting::

 INSTALLED_APPS = [
   ...,
   'mixin_templatetag'
 ]

and from there you can use it as follows::

 {% load mixins %}

 {% mixin foo %}
     <div>
         <div>{{ name }}</div>
         <div>{{ description }}</div>
     </div>
 {% endmixin %}

 {% block content %}
 ...
 {% mix foo with name="hello" description="world" %}
 ...
 {% endblock %}

Why django-template-mixins?
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently in Django, if you want to repeat a block multiple times in separate blocks / areas in the same block, you have to create a separate file. The worst part is that these extracted bits of template tend to be single purpose - you aren't likely to need it anywhere else besides that first template.

Mixins allow you to keep things in one place and allows you to avoid DRY.


Reporting bugs
~~~~~~~~~~~~~~

You can report bugs in https://github.com/benlei/django-template-mixins/issues.


If you believe you've found a bug, please try to identify the root cause and write up some sample code on how to reproduce it.


Author
~~~~~~

Benjamin Lei
