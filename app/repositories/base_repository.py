from abc import ABC, abstractmethod

class BaseRepository(ABC):
    def __init__(self, model):
        self.model = model

    def save(self, obj):
        return obj.save()

    def delete_by_id(self, id):
        return self.model.objects(id=id).delete()

    def find_by_id(self, id):
        return self.model.objects(id=id).first()

    def find_all(self):
        return self.model.objects.all()