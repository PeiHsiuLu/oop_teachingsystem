from app.models.course import LearningPath, Chapter, Unit
from app.repositories.course_repository import CourseRepository

class CourseService:
    def __init__(self):
        self.repo = CourseRepository()

    def create_learning_path(self, name):
        new_path = LearningPath(path_name=name)
        return self.repo.save(new_path)

    def add_chapter_to_path(self, path_id, chapter_title):
        path = self.repo.find_path_by_id(path_id)
        new_chapter = Chapter(title=chapter_title)
        new_chapter.save()
        
        path.chapters.append(new_chapter)
        path.save()
        return new_chapter

    def add_unit_to_chapter(self, chapter_id, unit_title, content):
        chapter = self.repo.find_chapter_by_id(chapter_id)
        new_unit = Unit(title=unit_title, content=content)
        new_unit.save()
        
        chapter.units.append(new_unit)
        chapter.save()
        return new_unit