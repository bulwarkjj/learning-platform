from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Course

class OwnerMixin(object):
    """
    allows views to get the base QuerySet and interacts with any model that contains 'owner' attribute
    """
    def get_queryset(self):
        """
        override get_queryset() to retrieve only courses created by current user 
        """
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)

class OwnerEditMixin(object):
    """
    allows views to be updated
    """
    def form_valid(self, form):
        """
        used by views with forms or model forms for submitting valid forms
        """
        form.instance.owner = self.request.user
        return super().form_valid(form)

class OwnerCourseMixin(OwnerMixin, LoginRequiredMixin, PermissionRequiredMixin):
    """
    inherits OwnerMixin for child views

    args:
        model: model used for QuerySet, used by all views
        fields: fields of the model to build model form of the CreateView and UpdateView views
        success_url: used by CreateView, UpdateView, DeleteView to redirect the user after the form is successfully submitted or object deleted
    """
    model = Course
    fields = ['subject', 'title', 'slug', 'overview']
    success_url = reverse_lazy('manage_course_list')

class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    """
    allows editing of course

    args:
        template_name: template used for the CreateView and UpdateView views
    """
    template_name = 'courses/manage/course/form.html'


class ManageCourseListView(OwnerCourseMixin, ListView):
    """
    Lists the courses created by the user

    args:
        template_name: template to list courses
        permission_required: restricts views to only users with proper permissions
    """
    template_name = 'courses/manage/course/list.html'
    permission_required = 'courses.view_course'

class CourseCreateView(OwnerCourseEditMixin, CreateView):
    """
    Uses a model form to create a new Course object

    args:
        permission_required: restricts views to only users with proper permissions
    """
    permission_required = 'courses.add_course'

class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    """
    Allows editing of an existing Course object

    args: 
        permission_required: restricts views to only users with proper permissions
    """
    permission_required = 'courses.change_course'

class CourseDeleteView(OwnerCourseMixin, DeleteView):
    """
    Allows deletion of an existing Course object

    args:
        template_name: confirms the course deletion 
        permission_required: restricts views to only users with proper permissions
    """
    template_name = 'courses/manage/course/delete.html'
    permission_required = 'courses.delete_course'

