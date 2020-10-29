from django.db import models
from django_mysql.models import Bit1BooleanField

class Person(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.TextField()
    pwd = models.TextField()
    vname = models.TextField()
    nname = models.TextField()
    is_user = Bit1BooleanField(null=True)
    is_coach = Bit1BooleanField(null=True)
    stripe_user_id = models.TextField(null=True)
    stripe_access_token = models.TextField(null=True)



    def __str__(self):
        return self.email

    class Meta:
        db_table = "person"

class CoachProfile(models.Model):
    id = models.AutoField(primary_key=True)
    person_id = models.ForeignKey(Person, on_delete=models.DO_NOTHING, db_column='person_id')
    profile_pic = models.TextField()
    price = models.IntegerField()

    def __str__(self):
        return self.person_id

    class Meta:
        db_table = "persondaten_coach"

class ClientProfile(models.Model):
    id = models.AutoField(primary_key=True)
    person_id = models.ForeignKey(Person, on_delete=models.DO_NOTHING, db_column='person_id')
    profile_pic = models.TextField()

    def __str__(self):
        return self.person_id

    class Meta:
        db_table = "persondaten"


class StripePaymentDetail(models.Model):
    id = models.AutoField(primary_key=True)
    client_id = models.ForeignKey(Person, on_delete=models.DO_NOTHING,related_name='stripe_client', null=True,db_column='client_id')
    coach_id = models.ForeignKey(Person, on_delete=models.DO_NOTHING,related_name='stripe_coach', null=True,db_column='coach_id')
    payment_detail = models.TextField()


    def __str__(self):
        return self.id

    class Meta:
        db_table = "stripe_payment_det"




