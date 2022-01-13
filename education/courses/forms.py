from django import forms
from django.forms import fields
from django.forms.models import inlineformset_factory
from .models import Course, Module

"""
In line formsets are small abstractions on top of formsets that simplify working with related objects
This allows me to build a model formset dynamically for the Module objects related to a Course object
"""
ModuleFormSet = inlineformset_factory(Course, Module, fields=['title', 'description'],
                                        extra=2, can_delete=True)