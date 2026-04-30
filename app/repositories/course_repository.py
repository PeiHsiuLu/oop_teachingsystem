from app.repositories.base_repository import BaseRepository
from app.models.course import LearningPath, Chapter, Unit

class CourseRepository(BaseRepository):
    def __init__(self):
        super().__init__(LearningPath)

    def find_path_by_id(self, path_id):
        return LearningPath.objects(id=path_id).first()
    
    def find_chapter_by_id(self, chapter_id):
        return Chapter.objects(id=chapter_id).first()
    
    def remove_unit_from_chapter(self, chapter_id, unit_id):
        chapter = Chapter.objects.get(id=chapter_id)
        # 1. Remove reference from the list
        chapter.units = [u for u in chapter.units if str(u.id) != unit_id]
        chapter.save()
        # 2. Delete the actual unit
        Unit.objects(id=unit_id).delete()

    def remove_chapter_from_path(self, path_id, chapter_id):
        path = LearningPath.objects.get(id=path_id)
        # 1. Remove reference
        path.chapters = [c for c in path.chapters if str(c.id) != chapter_id]
        path.save()
        # 2. Delete the actual chapter
        Chapter.objects(id=chapter_id).delete()

    def delete_path(self, path_id):
        LearningPath.objects(id=path_id).delete()