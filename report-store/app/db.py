import json
from typing import Iterable, List

from mongoengine import (
    Document,
    EmbeddedDocument,
)
from mongoengine.base import BaseDocument
from flask_mongoengine import BaseQuerySet


def _document_to_json_dict(document: BaseDocument) -> dict:
    return json.loads(document.to_json())


def _queryset_to_json_list(document_list: Iterable[BaseDocument]) -> List[dict]:
    return [_document_to_json_dict(doc) for doc in document_list]


class CustomQuerySet(BaseQuerySet):
    def to_dict(self) -> List[dict]:
        return _queryset_to_json_list(self)


class CustomDocument(Document):
    meta = {"abstract": True, "queryset_class": CustomQuerySet}

    # The functions below can be moved to a mixin
    def to_dict(self) -> dict:
        return _document_to_json_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "CustomDocument":
        return cls.from_json(json.dumps(d))


class CustomEmbeddedDocument(EmbeddedDocument):
    meta = {"abstract": True, "queryset_class": CustomQuerySet}

    # The functions below can be moved to a mixin
    def to_dict(self) -> dict:
        return _document_to_json_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "CustomDocument":
        return cls.from_json(json.dumps(d))
