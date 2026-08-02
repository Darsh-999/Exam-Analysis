from pydantic import BaseModel, Field


class SyllabusUnit(BaseModel):
    topic: str = Field(description="Title of the Unit/Module/Chapter, no trailing punctuation")
    subtopics: list[str] = Field(
        default_factory=list, description="Individual subtopics listed under this unit"
    )
    weightage: int = Field(
        default=0, description="Marks/weightage assigned to this unit; 0 if not stated"
    )
    hours: int = Field(
        default=0, description="Teaching hours allocated to this unit; 0 if not stated"
    )


class SyllabusExtraction(BaseModel):
    degree: str = Field(
        description='Degree/program name as seen on the syllabus, e.g. "B.Tech"; "" if not determined'
    )
    subject_name: str = Field(description='Subject/course name as seen; "" if not determined')
    subject_code: str = Field(description='Subject/course code as seen; "" if not determined')
    semester: int = Field(description="Semester number, 1-24; 0 if not determined")
    total_marks: int = Field(description="Total marks for the subject; 0 if not determined")
    content: list[SyllabusUnit] = Field(
        default_factory=list, description="Units/Modules that make up the syllabus content"
    )
