import datetime

from django.db import transaction
from django.contrib.auth.models import User
from django.views.generic.edit import FormView
from django.contrib.auth.forms import UserCreationForm
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, HttpResponse

from .models import Vote, VotingAnswer, Voting
from .models import Like, Comment, Profile, Report
from .forms import UserUpdateForm, ProfileUpdateForm, SignUpForm
from .forms import AddCommentForm

from PIL import Image


# @login_required
def voting(request, voting_id):
    context = {}
    context['voting'] = Voting.objects.get(id=voting_id)
    context['form'] = AddCommentForm()
    context['voted_answers'] = []

    try:
        userlike = Like.objects.get(user=request.user, voting_id=context['voting'])
    except:
        userlike = None

    if userlike:
        context['liked_by_user'] = True
    else:
        context['liked_by_user'] = False

    for i in context['voting'].answers():
        for j in i.votes():
            if j.user == request.user or (j.user_ip == get_client_ip(request) and not request.user.is_authenticated):
                context['voted_answers'].append(i)

    if request.method == 'POST':
        form = AddCommentForm(request.POST)
        if not request.user.is_authenticated:
            return redirect('/login/')

        if form.is_valid():
            comment_item = Comment(
                text=form.data['comment'],
                voting=Voting.objects.get(id=voting_id),
                user=request.user
            )
            comment_item.save()

    return render(request, 'voting.html', context)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def vote_registered(request, answer):
    answer_item = VotingAnswer.objects.get(id=answer)
    voting_item = answer_item.voting
    ip = get_client_ip(request)

    if voting_item.is_ended():
        return

    if not voting_item.is_multiple:
        for answer in voting_item.answers():
            if len(answer.votes().filter(user=request.user)) != 0:
                return

    if request.user not in [i.user for i in answer_item.votes()]:
        vote_item = Vote(
            answer=answer_item,
            user=request.user,
            user_ip=ip
        )
        vote_item.save()


def vote_anonymous(request, answer):
    answer_item = VotingAnswer.objects.get(id=answer)
    voting_item = answer_item.voting
    ip = get_client_ip(request)

    if voting_item.is_ended():
        return

    if not voting_item.is_multiple:
        for answer in voting_item.answers():
            if len(answer.votes().filter(user_ip=ip)) != 0:
                return

    if ip not in [i.user_ip for i in answer_item.votes()]:
        vote_item = Vote(
            answer=answer_item,
            user_ip=ip
        )
        vote_item.save()


def vote(request, answer):
    if request.method == 'POST':
        if request.user.is_authenticated:
            vote_registered(request, answer)
        else:
            vote_anonymous(request, answer)
    return redirect('/voting/' + str(VotingAnswer.objects.get(id=answer).voting.id))


@login_required
def like(request, voting_id):
    if request.method == 'POST':
        voting_item = Voting.objects.get(id=voting_id)
        if request.user not in [i.user for i in voting_item.likes()]:
            like_item = Like(
                voting=voting_item,
                user=request.user
            )
            like_item.save()
        else:
            like_item = Like.objects.get(
                voting=voting_item,
                user=request.user
            )
            like_item.delete()

    return redirect('/voting/' + str(voting_id))


def get_voting_errors(request):
    errors = []
    try:
        if not request.POST['question'].strip():
            errors.append('Поле опроса пустое')
        answers = request.POST.getlist('answer')
        if len(answers) < 2 or len(answers) > 25:
            errors.append('Неверное кол-во ответов')
        for i in answers:
            if not i.strip():
                errors.append('Не все поля ответов заполнены')
                break
        if request.POST.get('end_time'):
            date = [int(i) for i in request.POST.get('end_time').split('-')]
            date = datetime.date(date[0], date[1], date[2])
            if date <= datetime.date.today():
                errors.append('Нельзя установить прошедшую дату')
    except KeyError:
        errors.append('Что-то не так, перезагрузите страницу')

    return errors


@login_required
def create_voting(request):
    context = {}

    if request.method == 'POST':
        context['errors'] = get_voting_errors(request)

        if len(context['errors']) == 0:
            voting_item = Voting(
                text=request.POST['question'].strip(),
                user=request.user
            )
            if request.POST.get('end_time'):
                voting_item.end_time = request.POST.get('end_time')
            if request.POST.get('is_multiple', None) is not None:
                voting_item.is_multiple = True
            if request.POST.get('is_anonymous_allowed', None) is not None:
                voting_item.is_anonymous_allowed = True
            voting_item.save()

            for answer in request.POST.getlist('answer'):
                answer_item = VotingAnswer(
                    text=answer,
                    voting=voting_item
                )
                answer_item.save()
            return redirect('/voting/' + str(voting_item.id))

    return render(request, 'createvoting.html', context)


@login_required
def voting_edit(request, voting_id):
    context = {}
    context['voting'] = Voting.objects.get(id=voting_id)

    if request.method == 'POST':
        context['errors'] = get_voting_errors(request)

        if len(context['errors']) == 0:
            voting_item = Voting.objects.get(id=voting_id)
            question = request.POST['question']
            answers = request.POST.getlist('answer')
            end_time = request.POST['end_time']
            is_multiple = request.POST.get('is_multiple', None)
            is_anonymous_allowed = request.POST.get('is_anonymous_allowed', None)

            if voting_item.text != question:
                voting_item.text = question
                for answer in voting_item.answers():
                    for vote in answer.votes():
                        vote.delete()
                for like_item in voting_item.likes():
                    like_item.delete()

            if not end_time:
                voting_item.end_time = None
            else:
                voting_item.end_time = end_time

            if is_multiple is None:
                voting_item.is_multiple = False
            else:
                voting_item.is_multiple = True

            if is_anonymous_allowed is None:
                voting_item.is_anonymous_allowed = False
            else:
                voting_item.is_anonymous_allowed = True
            voting_item.save()

            for answer_item in voting_item.answers():
                if answer_item.text not in answers:
                    answer_item.delete()

            for answer_item in voting_item.answers():
                if answer_item.text in answers:
                    answers.remove(answer_item.text)

            for answer_text in answers:
                answer_item = VotingAnswer(
                    text=answer_text,
                    voting=voting_item
                )
                answer_item.save()

            return redirect('/voting/' + str(voting_id))

    return render(request, 'voting_edit.html', context)


@login_required
def delete_voting(request, voting_id):
    if request.method == 'POST':
        voting = Voting.objects.get(id=voting_id)
        if request.user == voting.user or request.user.is_superuser:
            voting.delete()

    return redirect('/')


def index(request):
    context = {}
    context['votings'] = Voting.objects.all()
    return render(request, 'index.html', context)


def profile(request, user_id):
    context = {}
    context['ufp'] = User.objects.get(id=user_id)
    context['profile'] = Profile.objects.get(user=user_id)

    return render(request, 'profile.html', context)


@login_required
@transaction.atomic
def edit_profile(request, user_id):
    context = {}
    context['ufp'] = User.objects.get(id=user_id)
    context['profile'] = Profile.objects.get(user=user_id)
    context['errors'] = []
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=User.objects.get(id=user_id))
        p = Profile.objects.get(user=user_id)
        try:
            image = request.FILES['avatar']
            if image.size <= 5000000:
                if image.content_type.split('/')[0] == 'image':
                    # Get file extension
                    i = -1
                    while image.name[i] != '.':
                        i -= 1
                    path = 'avatars/' + str(user_id) + image.name[i:]

                    # Init
                    fs = FileSystemStorage()

                    # Remove old avatar
                    if p.avatar.name != 'avatars/0.png':
                        fs.delete(p.avatar.path)

                    # Save avatar
                    fs.save(path, image)
                    p.avatar = path
                    p.save()

                    # Resize
                    image = Image.open(p.avatar)
                    size = (200, 200)
                    image = image.resize(size, Image.ANTIALIAS)
                    image.save(p.avatar.path)
                else:
                    pass
            else:
                pass
        except Exception:
            pass
        p.show_email = False if request.POST.get('show_email') is None else True
        p.save()
        profile_form = ProfileUpdateForm(request.POST, instance=Profile.objects.get(user=user_id))
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('/profile/' + str(user_id))
    else:
        user_form = UserUpdateForm(instance=User.objects.get(id=user_id))
        profile_form = ProfileUpdateForm(instance=Profile.objects.get(user=user_id))
    context['user_form'] = user_form
    context['profile_form'] = profile_form
    return render(request, 'profile_edit.html', context)


# https://ustimov.org/posts/17/
class RegisterFormView(FormView):
    form_class = SignUpForm
    # Ссылка, на которую будет перенаправляться user
    # в случае успешной регистрации
    success_url = "/login/"

    # Шаблон, который будет использоваться при отображении представления.
    template_name = "register.html"

    def form_valid(self, form):
        # Создаём пользователя, если данные в форму были введены корректно.
        form.save()
        for key in form.fields:
            print(form.fields[key])

        # Вызываем метод базового класса
        return super(RegisterFormView, self).form_valid(form)


@login_required
def send_report(request, voting_id):
    context = {}
    context['errors'] = []

    if request.method == 'POST':
        if request.POST.get('message', None) is None:
            context['errors'].append('Что-то пошло не так, перезагрузите страницу.')
        else:
            if not request.POST['message']:
                context['errors'].append('Заполните все поля.')

        if len(context['errors']) == 0:
            report_item = Report(
                user=request.user,
                voting=Voting.objects.get(id=voting_id),
                message=request.POST['message']
            )
            report_item.save()

            context['thanks'] = 'Спасибо за поддержку! Ваша жалоба будет рассмотрена.'

    return render(request, 'send_report.html', context)


@login_required
def reports(request):
    context = {}
    context['reports'] = Report.objects.filter(closed=False)
    context['user_reports'] = Report.objects.filter(user=request.user)

    return render(request, 'reports.html', context)


@login_required
def close_report(request, report_id):
    if request.method == 'POST' and request.user.is_superuser:
        r = Report.objects.get(id=report_id)
        r.closed = True
        r.save()
        return redirect('/reports/')

    return HttpResponse('Ошибка.')
