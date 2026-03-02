from pydantic import BaseModel
from typing import List


class Page(BaseModel):
    page_number: int
    page_text: str


class BookInput(BaseModel):
    book_title: str
    pages: List[Page]


class SceneCharacter(BaseModel):
    name: str
    actions: List[str]
    emotions: List[str]


class ScenePage(BaseModel):
    page_number: int
    page_text: str
    setting: str
    time_of_day: str
    mood: str
    characters: List[SceneCharacter]
    props: List[str]
    composition_notes: str
    continuity_notes: str
