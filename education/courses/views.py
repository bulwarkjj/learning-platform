from django.shortcuts import redirect, get_object_or_404
from django.views.generic.base import TemplateResponseMixin, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.forms.models import modelform_factory
from django.apps import apps
from .models import Course, Module, Content
from .forms import ModuleFormSet

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

class CourseModuleUpdateView(TemplateResponseMixin, View):
    """
    Handles the formset to add, update, and delete modules for a specific course

    params:
        TemplateResponseMixin: takes charge of rendering templates and returning an HTTP response
        View: basic class-based view provided by Django
    """
    template_name = 'course/manage/module/formset.html'
    course = None

    def get_formset(self, data=None):
        """
        Method to avoid repetition of code to build the formset 
        """
        return ModuleFormSet(instance=self.course, data=data)

    def dispatch(self, request, pk):
        """
        Executed for both POST and GET requests
        takes a HTTP request and its params and attempts to delegate to a lowercase method matching HTTP method used
        """
        self.course = get_object_or_404(Course, id=pk, owner=request.user)
        return super().dispatch(request, pk)

    def get(self, request, *args, **kwargs):
        """
        Executed for GET requests
        Building an empty ModuleFormSet formset and render it to the template together with the current Course object
        """
        formset = self.get_formset()
        return self.render_to_response({'course': self.course, 'formset': formset})

    def post(self, request, *args, **kwargs):
        """
        Executed for POST requests
        Builds a ModuleFormSet instance using the submitted data, executes vaildation of all forms, if valid, save it, if not show errors
        redirects users to manage_course_list URL
        """
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('manage_course_list')
        return self.render_to_response({'course': self.course, 'formset': formset})


class ContentCreateUpdateView(TemplateResponseMixin, View):
    """
    Generic approach to handle creating and updating view objects of any content model (text, image, video,file)
    """
    module = None
    model = None
    obj = None
    template_name = 'courses/manage/content/form.html'

    def get_model(self, model_name):
        """
        Checks given model name is of one content type than obtain class for given model name
        """
        if model_name in ['text', 'video', 'image', 'file']:
            return apps.get_model(app_label='courses', model_name=model_name)
        return None

    def get_form(self, model, *args, **kwargs):
        """
        Building dynamic form which excludes common fields and let other attributes be automatically included
        """
        Form = modelform_factory(model, exclude=['owner', 'order', 'created', 'updated'])
        return Form(*args, **kwargs)

    def dispatch(self, request, module_id, model_name, id=None):
        """
        Receives URL parameters and stores them to the corresponding module, model, and content object as class attribute
        """
        self.module = get_object_or_404(Module, id=module_id, course_owner=request.user)
        self.model = self.get_model(model_name)
        if id:
            self.obj = get_object_or_404(self.model, id=id, owner=request.user)

        return super().dispatch(request, module_id, model_name, id)

    def get(self, request, module_id, model_name, id=None):
        """
        Executes when a GET request is received, builds the model form, otherwise create new object
        """
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({'form': form, 'object': self.obj})

    def post(self, request, module_id, model_name, id=None):
        """
        Executes when a POST request is received, builds the model form passing any data/files to it, then validates it
        if form is valid, create a new object and assign request.user as it's owner
        if no ID is provided, creates a new object and associates the new content
        """
        form = self.get_form(self.model, instance=self.obj, data=request.POST, files=request.FILES)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                # new content
                Content.objects.create(module=self.module, item=obj)
            return redirect('module_content_list', self.module.id)
        return self.render_to_response({'form': form, 'object': self.obj})

class ContentDeleteView(View):
    """
    Retrieves Content object with given ID and deletes related Content objects
    """
    def post(self, request, id):
        """
        Deletes Content Object and redirects user to module_content_list URL to list other contents in the module
        """
        content =get_object_or_404(Content, id=id, module_course_owner=request.user)
        module = content.module
        content.item.delete()
        content.delete()
        return redirect('module_content_list', module.id)

class ModuleContentListView(TemplateResponseMixin, View):
    """
    Displays all modules for a course and list the content of a specific module
    """
    template_name = 'courses/manage/module/content_list.html'

    def get(self, request, module_id):
        """
        Gets the Module object with the given ID of current user and renders the template with the 
        given module
        """
        module = get_object_or_404(Module, id=module_id, course_owner=request.user)

        return self.render_to_response({'module': module})