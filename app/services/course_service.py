from app.models.course import LearningPath, Chapter, Unit
from app.repositories.course_repository import CourseRepository

class CourseService:
    def __init__(self):
        self.repo = CourseRepository()

    def create_learning_path(self, name):
        new_path = LearningPath(path_name=name)
        return self.repo.save(new_path)

    def add_chapter_to_path(self, path_id, chapter_title, rule_type, threshold):
        path = LearningPath.objects.get(id=path_id)
    
    # Save the rule details into the object
        new_chapter = Chapter(
            title=chapter_title, 
            unlock_rule_type=rule_type, 
            unlock_threshold=threshold
        )
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
    
    def delete_path(self, chapter_id, unit_id):
        self.repo.delete_path(chapter_id, unit_id)
    
    def delete_unit(self, chapter_id, unit_id):
        self.repo.remove_unit_from_chapter(chapter_id, unit_id)

    def delete_chapter(self, path_id, chapter_id):
        self.repo.remove_chapter_from_path(path_id, chapter_id)