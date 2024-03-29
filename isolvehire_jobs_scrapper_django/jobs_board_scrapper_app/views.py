from django.shortcuts import render, redirect
from django.views import View
from django.core.paginator import Paginator
from .models import Job
from .forms import JobForm
from datetime import datetime
from .tasks import sync_db


def sync_db_view(request):
    sync_db.delay()
    return redirect('home')


class JobsView(View):
    form_class = JobForm
    template_name = 'home.html'

    def get(self, request):
        # sync_db()     # we can sync each time we want to get all jobs
        jobs = Job.objects.all()
        form = self.form_class(request.GET)
        if form.is_valid() and any(form.cleaned_data.values()):
            cd = form.cleaned_data
            my_dict = {k: v.isoformat() for k, v in cd.items() if k in [
                'start_date', 'end_date'] and v}
            cd.update(my_dict)
            request.session['filter_jobs'] = cd
        elif not request.GET.get('page', None):
            request.session['filter_jobs'] = {}

        for key, value in request.session.get('filter_jobs').items():
            if value:
                if key == 'title':
                    jobs = jobs.filter(title__contains=value)
                elif key == 'location':
                    jobs = jobs.filter(location__contains=value)
                elif key == 'payment':
                    jobs = jobs.filter(pay__contains=value)
                elif key == 'payment_type':
                    jobs = jobs.filter(pay_type__contains=value)
                elif key == 'employment_type':
                    jobs = jobs.filter(employment_type__contains=value)
                elif key == 'start_date':
                    jobs = jobs.filter(
                        modified__gte=datetime.strptime(value, '%Y-%m-%d'))
                elif key == 'end_date':
                    jobs = jobs.filter(
                        modified__lte=datetime.strptime(value, '%Y-%m-%d'))

        p = Paginator(jobs, 2)
        page = request.GET.get('page')
        page_jobs = p.get_page(page)
        nums = "a" * page_jobs.paginator.num_pages
        return render(request, self.template_name, {'page_jobs': page_jobs, 'nums': nums, 'form': form})
