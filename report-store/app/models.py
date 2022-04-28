from mongoengine import (
    StringField,
    DictField,
    DateTimeField,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
)

from app.db import CustomDocument, CustomEmbeddedDocument

### Helper Models


class NameValuePair(CustomEmbeddedDocument):
    name = StringField()
    value = StringField()


class MetadataTree(CustomEmbeddedDocument):
    timeCreated = DateTimeField()
    timeUpdated = DateTimeField()
    labels = EmbeddedDocumentListField(NameValuePair, default=[])
    internalLabels = EmbeddedDocumentListField(NameValuePair, default=[])


class ResultsTree(CustomEmbeddedDocument):
    measurements = DictField()
    # Arbitrary unstructured data, in the form of key-value pairs
    data = DictField()


### Document Models


class Report(CustomDocument):
    apiVersion = StringField(required=True)
    name = StringField(required=True, unique=True)
    metadata = EmbeddedDocumentField(MetadataTree)
    context = DictField()
    results = EmbeddedDocumentField(ResultsTree)
    raw = DictField()

    def __str__(self):
        return self.name
