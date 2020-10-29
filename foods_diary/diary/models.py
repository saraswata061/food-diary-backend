from django.db import models

from user.models import Person;
from receipe.models import Lebensmittel;


class Mahlzeiten(models.Model):
    id = models.AutoField(primary_key=True)
    mahlzeit = models.TextField()


    def __str__(self):
        return self.mahlzeit

    class Meta:
        db_table = "mahlzeiten"

class Emotion(models.Model):
    id = models.AutoField(primary_key=True)
    namen = models.TextField()


    def __str__(self):
        return self.namen

    class Meta:
        db_table = "emotion"


class Buch(models.Model):
    id = models.AutoField(primary_key=True)
    person_id = models.ForeignKey(Person, on_delete=models.DO_NOTHING, db_column='person_id')
    mahlzeiten_id = models.ForeignKey(Mahlzeiten, on_delete=models.DO_NOTHING, db_column='mahlzeiten_id')
    emotion_id = models.ForeignKey(Emotion, on_delete=models.DO_NOTHING, db_column='emotion_id')
    uhrzeit = models.TextField()
    updated = models.IntegerField()


    def __str__(self):
        return self.id

    class Meta:
        db_table = "buch"
        ordering = ['-updated']

class BuchLebensmittel(models.Model):
    id = models.IntegerField(db_column='id', primary_key=True)
    buchId = models.ForeignKey(Buch, on_delete=models.DO_NOTHING, db_column='buch_id')
    lebensmittelId = models.ForeignKey(Lebensmittel, on_delete=models.DO_NOTHING, db_column='lebensmittel_id')

    # quantity
    menge = models.CharField(
        max_length=255
    )

    # imagelink
    bild_link = models.TextField()

    class Meta:
        unique_together = (("buchId", "lebensmittelId"),)
        db_table = "buch_has_lebensmittel"
