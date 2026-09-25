import re

ALIASES = {"js": "javascript", "ts": "typescript", "ml": "machine learning", "py": "python", "postgres": "postgresql"}

def normalize(value: str) -> set[str]:
    values = re.split(r"[,;\n|]+", value.lower())
    return {ALIASES.get(re.sub(r"[^a-z0-9+# ]", "", item).strip(), item.strip()) for item in values if item.strip()}


def match_student_project(student, project) -> dict:
    student_skills = normalize(",".join(student.skills or []))
    required = normalize(",".join(project.required_skills or []))
    matching = student_skills & required
    missing = required - student_skills
    skill_score = len(matching) / len(required) if required else 1
    field_score = 1 if any(normalize(student.field_of_study) & normalize(field) for field in (project.preferred_fields or [])) else 0
    interest_score = 1 if normalize(",".join(student.interests or [])) & (required | normalize(project.description)) else 0
    availability_score = 1 if student.availability and (student.availability.lower() in project.description.lower() or student.availability.lower() in project.project_duration.lower()) else 0.5
    score = round((skill_score * 50) + (field_score * 20) + (interest_score * 15) + (availability_score * 10) + 5)
    explanation = f"Strong overlap in {', '.join(sorted(matching))}." if matching else "This project aligns with your broader interests and is a chance to build relevant skills."
    if missing:
        explanation += f" Build next: {', '.join(sorted(missing))}."
    return {"score": min(score, 100), "matching_skills": sorted(matching), "missing_skills": sorted(missing), "explanation": explanation}
