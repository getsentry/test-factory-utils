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


### Document Models
REPORT_TYPE_SDK = "sdk"
REPORT_TYPE_REGULAR = "regular"
REPORT_TYPES = {REPORT_TYPE_SDK, REPORT_TYPE_REGULAR}


class BaseReport(CustomDocument):
    meta = {"abstract": True}

    apiVersion = StringField(required=True)
    name = StringField(required=True, unique=True)
    metadata = EmbeddedDocumentField(MetadataTree)
    context = DictField()
    results = DictField()
    raw = DictField()

    def __str__(self):
        return self.name


class Report(BaseReport):
    """
    Generic load-testing report
    """

    meta = {"collection": "report"}


class SdkReport(BaseReport):
    """
    SDK Performance measurements report
    """

    meta = {"collection": "sdk_report"}
