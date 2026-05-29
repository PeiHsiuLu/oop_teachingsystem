from app.models.course import LearningPath, Chapter, Unit
from app.models.analytics import Progress
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
    
    def delete_path(self, path_id):
        path = LearningPath.objects(id=path_id).first()
        if not path:
            raise ValueError("Learning Path not found")
        path.delete()
        return True
    
    def update_path(self, path_id, new_name):
        path = LearningPath.objects(id=path_id).first()
        if not path:
            raise ValueError("Learning Path not found")
        path.path_name = new_name
        path.save()
        return path

    def update_chapter_title(self, chapter_id, new_title):
        chapter = Chapter.objects(id=chapter_id).first()
        if chapter:
            chapter.title = new_title
            chapter.save()
        return chapter

    def update_unit_title(self, unit_id, new_title):
        unit = Unit.objects(id=unit_id).first()
        if unit:
            unit.title = new_title
            unit.save()
        return unit

    def delete_unit(self, chapter_id, unit_id):
        self.repo.remove_unit_from_chapter(chapter_id, unit_id)
    
    def update_unit(self, unit_id, new_content):
        unit = Unit.objects.get(id=unit_id)
        unit.content = new_content
        unit.save()

    def delete_chapter(self, path_id, chapter_id):
        self.repo.remove_chapter_from_path(path_id, chapter_id)

    def get_chapter_status(self, student, chapter):
        # Get all units in this chapter
        unit_ids = [u.id for u in chapter.units]
        # Count how many of these units the student has in Progress
        completed_count = Progress.objects(student=student, unit__in=unit_ids).count()
    
        return completed_count >= len(unit_ids)

    def is_chapter_finished(self, student, chapter):
        # Get all unit IDs for this chapter
        chapter_unit_ids = [unit.id for unit in chapter.units]
    
        # Get all units this student has completed
        completed_units = Progress.objects(student=student, unit__in=chapter_unit_ids)
    
        # If the counts match, the chapter is finished!
        return len(completed_units) >= len(chapter_unit_ids)
    
    def mark_unit_complete(self, student_id, unit_id):
        # Check if already completed to avoid duplicate logs
        existing = Progress.objects(student=student_id, unit=unit_id).first()
        if not existing:
            progress = Progress(student=student_id, unit=unit_id)
            progress.save()