# Create your views here.

# GENERIC VIEWS
# https://docs.djangoproject.com/en/3.1/ref/class-based-views/generic-display/
# https://docs.djangoproject.com/en/3.1/topics/class-based-views/generic-display/


# FORM FROM MODEL
# https://docs.djangoproject.com/en/3.1/topics/forms/modelforms/
# https://tutorial.djangogirls.org/en/django_forms/

# CUSTOM USER MODEL
# https://docs.djangoproject.com/en/dev/topics/auth/customizing/#substituting-a-custom-user-model


# Signals
# https://simpleisbetterthancomplex.com/tutorial/2016/07/28/how-to-create-django-signals.html

from django.shortcuts import redirect
from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from .forms import ContactForm, EducationForm, StudentForm
from .models import Contact, Education, Student, Offer, Company, Application
from django.contrib import messages

from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Max, Min, Sum
from app.analytics import pie_dream_open_offer, pie_branch_offer
from django.db.models.functions import Coalesce

def home(request):
    return render(request, 'app/home.html')

@login_required
def dashboard(request):
    user = request.user
    student = request.user.student
    contact = student.contact
    education = student.education

    context = {}
    context['user'] = user
    context['student'] = student
    context['contact'] = contact
    context['education'] = education

    # test = Offer.objects.all() \
    # .values('offer_type') \
    # .annotate(package = Sum('package'))

    # print(test)

    context['analytics'] = {}


    context['analytics']['chart1'] = pie_dream_open_offer()
    context['analytics']['chart2'] = pie_branch_offer()
    # print(">>>>>>>>>>>>",context['test_data'])

    return render(request, 'app/dashboard.html', context=context)






@login_required 
def edit_profile(request):

    user = request.user.student
    # user = Student.objects.get(user=user)


    # c = Contact.objects.get(user=user)
    # e = Education.objects.get(user=user)

    c = user.contact
    e = user.education


    studentForm = StudentForm(instance=user)
    contactForm = ContactForm(instance=c)
    educationForm = EducationForm(instance=e)
    return render(request, 'app/view_profile.html', {'contact_form':contactForm, 'edu_form':educationForm , 'student_form':studentForm })

@login_required 
def edit_contact_details(request):

    if request.method == 'POST':
        
        student = request.user.student
        contact = student.contact

        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()

            msg = "Message"
            error = "Successfully saved"
            messages.error(request, f"{msg}: {error}")
        else:
            for msg in form.error_messages:
                messages.error(request, f"{msg}: {form.error_messages[msg]}")

        # form.user = request.user.student 
        
        return redirect('dashboard')


@login_required 
def edit_education_details(request):

    if request.method == 'POST':
        
        student = request.user.student
        education = student.education

        form = EducationForm(request.POST, instance=education)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()

            msg = "Message"
            error = "Successfully saved"
            messages.error(request, f"{msg}: {error}")
        else:
            for msg in form.error_messages:
                messages.error(request, f"{msg}: {form.error_messages[msg]}")

        return redirect('dashboard')


@login_required 
def edit_profile_details(request):

    if request.method == 'POST':
        
        student = request.user.student
        # education = student.education
        print(request.FILES)
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()

            msg = "Message"
            error = "Successfully saved"
            messages.error(request, f"{msg}: {error}")
        else:
            for msg in form.error_messages:
                messages.error(request, f"{msg}: {form.error_messages[msg]}")

        return redirect('dashboard')


def CheckElegibleForApplication(student, offer):

    errors = []

    is_elegible = student.is_eligible



    if not is_elegible:
        errors.append("Student is not elegible or already placed in open Dream Company")

    if Application.objects.filter(student=student, offer=offer).count() >0:
        is_elegible = False
        errors.append("Already Applied")


    if datetime.datetime.now().astimezone(timezone.utc) > offer.deadline:
        is_elegible = False
        errors.append("deadline already passed")

    if student.education.graduation_year != offer.required_batch:
        is_elegible = False
        errors.append("required batch is "+ str(offer.required_batch))

    if student.education.department not in offer.eligible_branches.all():
        is_elegible = False
        errors.append("Your branch is not elegible.")

    if student.education.cgpa < offer.cgpa_cutoff :
        is_elegible = False
        errors.append("CGPA Cutoff requirement not met.")

    if student.education.X_percentage < offer.X_cutoff :
        is_elegible = False
        errors.append("X percentage Cutoff requirement not met.")

    if student.education.X_percentage < offer.XII_cutoff :
        is_elegible = False
        errors.append("XII / Diploma percentage Cutoff requirement not met.")


    if student.gender not in offer.eligible_gender and "OTHER" not in offer.eligible_gender:
        is_elegible = False
        errors.append("your Gender is not elegible")

    

    return is_elegible, errors
    


class OfferListView(ListView):

    model = Offer
    paginate_by = 10  # if pagination is desired


    def get_queryset(self):
        qs = super(OfferListView, self).get_queryset()
        # name = self.kwargs.get('name', '')
        filters = self.request.GET
        print(filters)
        # print(filters)
        if 'name' in filters.keys():
            # print(True)
            # print(filters['name'])
            qs1 =  qs.filter(company__name__icontains=filters['name'] )
            qs2 = qs.filter(note__icontains=filters['name'])
            qs = qs1 | qs2
        
        if "eligible_only" in filters.keys():
            print("eligible_only")
            ids = []
            for q in qs:
                is_elegible, errors = CheckElegibleForApplication(self.request.user.student,q )
                if is_elegible:
                    ids.append(q.id)
            print(len(qs))
            qs = qs.filter(pk__in=ids) 
            print(len(qs))


        if 'dream_only' in filters.keys():
            qs =qs.filter(offer_type='DREAM')

        if 'open_dream_only' in filters.keys():
            qs =qs.filter(offer_type='OPEN')



        return qs.order_by('-id')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class OfferDetailView(DetailView):

    model = Offer


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        student = self.request.user.student
        offer = self.object
        
        is_elegible, errors = CheckElegibleForApplication(student, offer)


        context['elegible'] = is_elegible
        context['elegiblity_reasons'] = errors

        return context


class CompanyListView(ListView):

    model = Company
    paginate_by = 5  # if pagination is desired

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class CompanyDetailView(DetailView):

    model = Company

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ApplicationListView(ListView):

    model = Application
    # paginate_by = 5  # if pagination is desired

    def get_queryset(self):
        qs = super(ApplicationListView, self).get_queryset()
        return qs.filter(student=self.request.user.student).order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# class CompanyDetailView(DetailView):

#     model = Company

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         return context

@login_required
def AddApplication(request, id):
    student = request.user.student
    offer = get_object_or_404(Offer, pk=id)
    is_elegible, errors = CheckElegibleForApplication(student, offer)    

    if is_elegible:
        Application.objects.create(student = student,offer = offer)
        return redirect('my_applications')
    else:
        return redirect('offer_details', pk=id)



#TODO Add gender in elegibility criteria