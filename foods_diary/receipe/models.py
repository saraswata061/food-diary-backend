from django.db import models

class Rezepte(models.Model):
    id = models.AutoField(primary_key=True)
    namen = models.CharField(
        max_length=255
    )
    beschreibung = models.TextField()
    buch_link = models.TextField()
    buch_author = models.TextField()
    updated = models.IntegerField()


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

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lebensmittel"


class Symptom(models.Model):
    id = models.AutoField(primary_key=True)
    namen = models.TextField()

    def __str__(self):
        return self.namen

    class Meta:
        db_table = "symptome"

class RezepteLebensmittel(models.Model):
    id = models.IntegerField( db_column='id', primary_key=True)
    rezepteId = models.ForeignKey(Rezepte, on_delete=models.DO_NOTHING, db_column='rezepte_id')
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
    rezepteId = models.ForeignKey(Rezepte, on_delete=models.DO_NOTHING, db_column='rezepte_id')
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
