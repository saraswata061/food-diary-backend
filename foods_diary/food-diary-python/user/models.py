from django.db import models
from django_mysql.models import Bit1BooleanField

class Person(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.TextField()
    pwd = models.TextField()
    is_user = Bit1BooleanField()
    is_coach = Bit1BooleanField()
    stripe_user_id = models.TextField()
    stripe_access_token = models.TextField()



    def __str__(self):
        return self.email

    class Meta:
        db_table = "person"




