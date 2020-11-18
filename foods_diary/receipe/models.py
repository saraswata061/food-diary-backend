from django.db import models
from django_mysql.models import Bit1BooleanField

class Rezepte(models.Model):
    id = models.AutoField(primary_key=True)
    namen = models.CharField(
        max_length=255
    )
    beschreibung = models.TextField()
    buch_link = models.TextField()
    buch_author = models.TextField()
    updated = models.IntegerField()
    author = models.IntegerField()
    isPublic = Bit1BooleanField(db_column='is_public')


    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-updated']
        db_table = "rezepte"

class Handicap(models.Model):
    id = models.AutoField(primary_key=True)
    namen = models.TextField()


    def __str__(self):
        return self.namen

    class Meta:
        db_table = "handicap"

class Lebensmittel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    weight = models.FloatField(db_column='gewicht')
    calories = models.FloatField(db_column='kalorien')
    kilojoule = models.FloatField(db_column='kilojoule')
    breadunit = models.FloatField(db_column='broteinheit')
    carbohydrates = models.FloatField(db_column='kolenhydrate')
    bold = models.FloatField(db_column='fett')
    protein = models.FloatField(db_column='eiweiss')
    csalary = models.FloatField(db_column='c_gehalt')
    animal = Bit1BooleanField(db_column='tierisch')
    milk = Bit1BooleanField(db_column='milch')
    fish = Bit1BooleanField(db_column='fisch')
    fruit = Bit1BooleanField(db_column='obst')
    vegetables = Bit1BooleanField(db_column='gemuese')
    spice = Bit1BooleanField(db_column='gewuerz')
    herbs = Bit1BooleanField(db_column='kraeuter')
    court = Bit1BooleanField(db_column='gericht')
    vegan = Bit1BooleanField(db_column='vegan')
    vegetarian = Bit1BooleanField(db_column='vegetarisch')
    shellfish = Bit1BooleanField(db_column='schalentiere')
    sauce = Bit1BooleanField(db_column='sossen')
    raw = Bit1BooleanField(db_column='roh')
    cooked = Bit1BooleanField(db_column='gekocht')
    fried = Bit1BooleanField(db_column='gebraten')
    grilled = Bit1BooleanField(db_column='gegrillt')
    fermented = Bit1BooleanField(db_column='fermentiert')
    basic = Bit1BooleanField(db_column='gedoehrt')
    acidic = Bit1BooleanField(db_column='basisch')
    neutral = Bit1BooleanField(db_column='saeurisch')
    baked = Bit1BooleanField(db_column='gebacken')
    smoked = Bit1BooleanField(db_column='geraeuchert')
    cereals = Bit1BooleanField(db_column='getreide')
    selfmade = Bit1BooleanField(db_column='selfmade')
    ironcontent = Bit1BooleanField(db_column='eisengehalt')
    hasiron = Bit1BooleanField(db_column='has_eisen')
    hasc = Bit1BooleanField(db_column='has_c')
    nuts = Bit1BooleanField(db_column='nuts')
    lactose = Bit1BooleanField(db_column='laktose')
    wheat = Bit1BooleanField(db_column='weizen')
    gluten = Bit1BooleanField(db_column='gluten')
    fructose = Bit1BooleanField(db_column='fructose')


    def __str__(self):
        return self.name

    class Meta:
        db_table = "lebensmittel"



def calculateFoodNutrition():
    pass

class Symptom(models.Model):
    id = models.AutoField(primary_key=True)
    namen = models.TextField()

    def __str__(self):
        return self.namen

    class Meta:
        db_table = "symptome"

class RezepteLebensmittel(models.Model):
    id = models.IntegerField( db_column='id', primary_key=True)
    rezepteId = models.ForeignKey(Rezepte, on_delete=models.DO_NOTHING, db_column='rezepte_id',related_name='rezepte_lebensmittel')
    lebensmittelId = models.ForeignKey(Lebensmittel, on_delete=models.DO_NOTHING, db_column='lebensmittel_id')

    # quantity
    menge = models.CharField(
        max_length=255
    )

    #imagelink
    bild_link = models.TextField()


    class Meta:
        unique_together = (("rezepteId", "lebensmittelId"),)
        db_table = "rezepte_has_lebensmittel"

class RezepteSymptome(models.Model):
    id = models.IntegerField( db_column='id', primary_key=True)
    rezepteId = models.ForeignKey(Rezepte, on_delete=models.DO_NOTHING, db_column='rezepte_id',related_name='rezepte_symptom')
    symptomeId = models.ForeignKey(Symptom, on_delete=models.DO_NOTHING, db_column='symptome_id')

    class Meta:
        unique_together = (("rezepteId", "symptomeId"),)
        db_table = "rezepte_has_symptome"


class RezepteHandicap(models.Model):
    id = models.IntegerField( db_column='id', primary_key=True)
    rezepteId = models.ForeignKey(Rezepte, on_delete=models.DO_NOTHING, db_column='rezepte_id')
    handicapId = models.ForeignKey(Handicap, on_delete=models.DO_NOTHING, db_column='handicap_id')



    class Meta:
        unique_together = (("rezepteId", "handicapId"),)
        db_table = "rezepte_has_handicap"


class HandicapSymptome(models.Model):
    id = models.IntegerField( db_column='id', primary_key=True)
    handicapId = models.ForeignKey(Handicap, on_delete=models.DO_NOTHING, db_column='handicap_id',related_name='handicap_symptom')
    symptomeId = models.ForeignKey(Symptom, on_delete=models.DO_NOTHING, db_column='symptome_id')

    class Meta:
        unique_together = (("handicapId", "symptomeId"),)
        db_table = "handicap_has_symptome"

class HandicapLebensmittel(models.Model):
    id = models.IntegerField( db_column='id', primary_key=True)
    handicapId = models.ForeignKey(Handicap, on_delete=models.DO_NOTHING, db_column='handicap_id',related_name='handicap_lebensmittel')
    lebensmittelId = models.ForeignKey(Lebensmittel, on_delete=models.DO_NOTHING, db_column='lebensmittel_id')
    isGood = Bit1BooleanField(db_column='is_good')
    isBad = Bit1BooleanField(db_column='is_bad')

    class Meta:
        unique_together = (("handicapId", "lebensmittelId"),)
        db_table = "handicap_has_lebensmittel"
