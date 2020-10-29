from django.db import models

class Rezepte(models.Model):
    id = models.AutoField(primary_key=True)
    namen = models.CharField(
        max_length=255
    )
    beschreibung = models.TextField()


    def __str__(self):
        return self.name

    class Meta:
        db_table = "rezepte"

class Lebensmittel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = "lebensmittel"

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
