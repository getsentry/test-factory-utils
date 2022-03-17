from mongoengine import (
    StringField,
    DictField,
    DateTimeField,
    EmbeddedDocumentField,
    ListField,
)

from app.db import CustomDocument, CustomEmbeddedDocument

### Helper Models
class MetadataTree(CustomEmbeddedDocument):
    timeCreated = DateTimeField()
    timeUpdated = DateTimeField()
    # labels
    # internalLabels


### Document Models
class Report(CustomDocument):
    apiVersion = StringField(required=True)
    name = StringField(required=True, unique=True)
    metadata = EmbeddedDocumentField(MetadataTree)
    context = DictField()
    results = DictField()
    raw = DictField()

    def __str__(self):
        return self.name
