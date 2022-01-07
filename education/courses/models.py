from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from .fields import OrderField

class Subject(models.Model):
    """
    Model to create data for Subjects
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ['title']

    def __str__(self) -> str:
        return self.title

class Course(models.Model):
    """
    Model to create data for Courses

    args:
        owner: relation data for who created the course
        subject: connects to the course 
        overview: a textfield column to store an overview of the course
        created: date and time when the course was created
    """
   
    owner = models.ForeignKey(User, related_name='courses_created', on_delete=models.CASCADE)   
    subject = models.ForeignKey(Subject, related_name='courses', on_delete=models.CASCADE)  
    title = models.CharField(max_length=200)    
    slug = models.SlugField(max_length=200, unique=True)    
    overview = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self) -> str:
        return self.title


class Module(models.Model):
    """
    Each course is divided into several modules, this class contains a foreignkey field that points to the Course model
    """
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = OrderField(blank=True, for_fields=['course'])

    class Meta:
        ordering = ['order']

    def __str__(self) -> str:
        return f'{self.order}. {self.title}'


class Content(models.Model):
    """
    Sets up a generic relation to associate objects from different models repersenting different types of content

    args:
        module: ForeignKey pointing to Model contents 
        content_type: ForeignKey field pointing to ContentType
        object_id: an Int to store the primary key of the related object
        item: GenericForeignKey pointing to related object and combining content_type and object_id
    """
    module = models.ForeignKey(Module, related_name='contents', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to={'model_in':('text', 'video', 'image', 'file')})
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['module'])

    class Meta:
        ordering = ['order']

class ItemBase(models.Model):
    """
    Abstract Model that provides the common fields for all content models
    """

    owner = models.ForeignKey(User, related_name='%(class)s_related', on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.title

class Text(ItemBase):
    """
    Inherits from ItemBase class to store text content
    """
    content = models.TextField()

class File(ItemBase):
    """
    Inherits from ItemBase class to store files
    """
    file = models.FileField(upload_to='files')

class Image(ItemBase):
    """
    Inherits from ItemBase class to store image files
    """
    file = models.FileField(upload_to='images')

class Video(ItemBase):
    """
    Inherits from ItemBase class to store videos using URL's to embed videos
    """
    url = models.URLField()