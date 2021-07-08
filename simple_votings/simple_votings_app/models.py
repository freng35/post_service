# -*- coding: utf-8 -*-
import datetime
from django.contrib.auth.models import User
from django.db import models
from django.contrib import admin
from django.db.models.signals import post_save
from django.dispatch import receiver


class Voting(models.Model):
    text = models.CharField(max_length=500)
    start_time = models.DateTimeField(auto_now=True)
    end_time = models.DateField(null=True, default=None)
    is_multiple = models.BooleanField(default=False)
    is_anonymous_allowed = models.BooleanField(default=False)

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, default="anonymous")

    def __str__(self):
        return "%s" % (self.text)

    def __unicode__(self):
        return u'%s' % (self.text)

    def answers(self):
        return VotingAnswer.objects.filter(voting=self)

    def like(self):
        return "/like/" + str(self.id) + '/'

    def likes(self):
        return Like.objects.filter(voting=self)

    def likes_count(self):
        return len(self.likes())

    def comments(self):
        return Comment.objects.filter(voting=self)

    def is_ended(self):
        if self.end_time is None:
            return False
        return datetime.date.today() >= self.end_time

    def comments_count(self):
        return len(self.comments())

    def votes_count(self):
        return sum([i.votes_count() for i in self.answers()])

    def type(self):
        if self.is_multiple and self.end_time:
            return 'Множественный выбор с окончанием'
        if self.is_multiple:
            return 'Множественный выбор'
        if self.end_time:
            return 'Обыкновенное с окончанием'
        return 'Обыкновенное'

    def get_end_time(self):
        return '{}-{:02}-{:02}'.format(self.end_time.year, self.end_time.month, self.end_time.day)


class Like(models.Model):
    date = models.DateTimeField(auto_now=True)

    voting = models.ForeignKey(to=Voting, on_delete=models.CASCADE)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)


class VotingAnswer(models.Model):
    text = models.CharField(max_length=500)

    voting = models.ForeignKey(to=Voting, on_delete=models.CASCADE)

    def __unicode__(self):
        return self.text

    def action(self):
        return "/vote/" + str(self.id) + '/'

    def votes(self):
        return Vote.objects.filter(answer=self)

    def votes_count(self):
        return len(self.votes())


class Vote(models.Model):
    date = models.DateTimeField(auto_now=True)

    answer = models.ForeignKey(to=VotingAnswer, on_delete=models.CASCADE)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, blank=True, null=True)
    user_ip = models.CharField(max_length=16, default="")


class Comment(models.Model):
    date = models.DateTimeField(auto_now=True)
    text = models.CharField(max_length=500)

    voting = models.ForeignKey(to=Voting, on_delete=models.CASCADE)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)


class VotingAdmin(admin.ModelAdmin):
    list_display = ('text', 'user', 'start_time', 'end_time')


class VotingAnswerAdmin(admin.ModelAdmin):
    list_display = ('text', )


class Profile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Мужчина'),
        ('F', 'Женщина'),
        (None, 'Не указано')
    )

    user = models.OneToOneField(to=User, on_delete=models.CASCADE)

    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, default='avatars/0.png')

    job = models.CharField(null=True, max_length=100)
    biography = models.CharField(max_length=500, null=True)

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True)
    country = models.CharField(null=True, max_length=60)
    birth = models.DateField(null=True)
    show_email = models.BooleanField(default=False)

    def good_date(self, date):
        return '{}.{}.{} {}:{}'.format(date.day, date.month, date.year, date.hour, date.minute)

    def good_joined_date(self):
        return self.good_date(self.user.date_joined)

    def good_login_date(self):
        return self.good_date(self.user.last_login)

    def votings(self):
        return Voting.objects.filter(user=self.user)

    def votings_count(self):
        return len(self.votings())

    def likes_on_votings(self):
        count = 0
        for i in self.votings():
            count += i.likes_count()
        return count

    def votes_on_votings(self):
        count = 0
        for voting in self.votings():
            for answer in voting.answers():
                count += answer.votes_count()
        return count

    def comments(self):
        return Comment.objects.filter(user=self.user)

    def comments_count(self):
        return len(self.comments())

    def votes(self):
        return Vote.objects.filter(user=self.user)

    def votes_count(self):
        return len(self.votes())

    def likes(self):
        return Like.objects.filter(user=self.user)

    def likes_count(self):
        return len(self.likes())


class Report(models.Model):
    voting = models.ForeignKey(to=Voting, on_delete=models.CASCADE)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    closed = models.BooleanField(default=False)

    message = models.CharField(max_length=500)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


admin.site.register(Voting, VotingAdmin)
admin.site.register(VotingAnswer, VotingAnswerAdmin)
