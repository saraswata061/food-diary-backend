from django.db import models
from django_mysql.models import Bit1BooleanField
from receipe.models import Symptom, Handicap;

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
    description = models.TextField()



    def __str__(self):
        return self.email

    class Meta:
        db_table = "person"

class CoachProfile(models.Model):
    id = models.AutoField(primary_key=True)
    person_id = models.ForeignKey(Person, on_delete=models.DO_NOTHING, db_column='person_id',related_name='coach_profile')
    profile_pic = models.TextField()
    price = models.IntegerField()
    land = models.TextField()  # country
    ort = models.TextField() # region
    bday = models.DateTimeField()


    def __str__(self):
        return self.person_id

    class Meta:
        db_table = "persondaten_coach"

class ClientProfile(models.Model):
    id = models.AutoField(primary_key=True)
    person_id = models.ForeignKey(Person, on_delete=models.DO_NOTHING, db_column='person_id',related_name='client_profile')
    profile_pic = models.TextField()
    bday = models.DateTimeField()
    telefon = models.IntegerField()
    groesse = models.IntegerField() #height
    gewicht = models.FloatField()  # weight
    plz = models.TextField()  # zip code
    ort = models.TextField()  # region
    gender = models.TextField()  # region
    land = models.TextField()  # country
    smoking = Bit1BooleanField(db_column="smoking")  # smoking
    menopause = models.BooleanField()  # menopause
    pregnant = Bit1BooleanField(db_column="pregnant")  # pregnant
    job_activity = models.IntegerField()  # sprt activity
    sport_activity = models.IntegerField()  # sprt activity
    stillen = Bit1BooleanField(db_column="stillen")  # breastfeeding

    def __str__(self):
        return self.person_id

    class Meta:
        db_table = "persondaten"


class CoachingRequest(models.Model):
    id = models.AutoField( db_column='id', primary_key=True)
    personIdCoach = models.ForeignKey(Person, on_delete=models.DO_NOTHING, db_column='person_id_coach',
                                    related_name='person_id_coach')
    personIdClient = models.ForeignKey(Person, on_delete=models.DO_NOTHING, db_column='person_id_client',
                                    related_name='person_id_client')
    title = models.TextField( db_column='title')
    description = models.TextField(db_column='description')
    comments = models.TextField(db_column='comments')
    requestCost = models.FloatField(db_column='requestcost')
    feedbackCoach = models.TextField(db_column='feedbackcoach')
    ratingCoach = models.FloatField(db_column='ratingcoach')
    feedbackClient = models.TextField(db_column='feedbackclient')
    ratingClient = models.FloatField(db_column='ratingclient')
    requestStatus = models.IntegerField(db_column="request_status")
    paymentStatus = Bit1BooleanField(db_column="payment_status")  # pregnant

    class Meta:
        db_table = "coaching_request"


class StripePaymentDetail(models.Model):
    id = models.AutoField(primary_key=True)
    client_id = models.ForeignKey(Person, on_delete=models.DO_NOTHING,related_name='stripe_client', null=True,db_column='client_id')
    coach_id = models.ForeignKey(Person, on_delete=models.DO_NOTHING,related_name='stripe_coach', null=True,db_column='coach_id')
    payment_detail = models.TextField()
    payment_type = models.TextField()
    coaching_id = models.ForeignKey(CoachingRequest, on_delete=models.DO_NOTHING, related_name='coaching_request', null=True,
                                  db_column='coaching_id')

    def __str__(self):
        return self.id

    class Meta:
        db_table = "stripe_payment_det"

class PersonSymptome(models.Model):
    id = models.IntegerField( db_column='id', primary_key=True)
    personId = models.ForeignKey(Person, on_delete=models.DO_NOTHING, db_column='person_id',related_name='person_symptom')
    symptomeId = models.ForeignKey(Symptom, on_delete=models.DO_NOTHING, db_column='symptome_id')

    class Meta:
        unique_together = (("personId", "symptomeId"),)
        db_table = "person_has_symptome"

class PersonHandicap(models.Model):
    id = models.IntegerField( db_column='id', primary_key=True)
    personId = models.ForeignKey(Person, on_delete=models.DO_NOTHING, db_column='person_id',related_name='person_handicap')
    handicapId = models.ForeignKey(Handicap, on_delete=models.DO_NOTHING, db_column='handicap_id')

    class Meta:
        unique_together = (("personId", "handicapId"),)
        db_table = "person_has_handicap"



class UserChatHistory(models.Model):
    id = models.TextField( db_column='id', primary_key=True)
    date = models.DateTimeField(db_column='date')
    personIdOne = models.ForeignKey(Person, on_delete=models.DO_NOTHING, db_column='person_id_one',related_name='person_id_one')
    personIdTwo = models.ForeignKey(Person, on_delete=models.DO_NOTHING, db_column='person_id_two',related_name='person_id_two')
    chatMessages = models.TextField(db_column='chat_messages')

    class Meta:
        unique_together = (("date", "personIdOne", "personIdTwo","id"),)
        db_table = "user_chat_history"


class FAQ(models.Model):
    id = models.AutoField( db_column='id', primary_key=True)
    question = models.TextField(db_column='frage')
    private = Bit1BooleanField(db_column='private')

    class Meta:
        db_table = "faq"

class FAQAnswer(models.Model):
    id = models.AutoField( db_column='id', primary_key=True)
    faq = models.ForeignKey(FAQ, on_delete=models.DO_NOTHING, db_column='faq_id',related_name='answer_faq_id')
    answer = models.TextField( db_column='antwort')


    class Meta:
        db_table = "faq_antworten"







