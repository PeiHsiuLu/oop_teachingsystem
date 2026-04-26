from app.repositories.base_repository import BaseRepository
from app.models.course import LearningPath, Chapter, Unit

class CourseRepository(BaseRepository):
    def __init__(self):
        super().__init__(LearningPath)

    def find_path_by_id(self, path_id):
        return LearningPath.objects(id=path_id).first()
    
    def find_chapter_by_id(self, chapter_id):
        return Chapter.objects(id=chapter_id).first()