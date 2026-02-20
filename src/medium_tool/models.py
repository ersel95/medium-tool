"""Data models for medium-tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Language(Enum):
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    TYPESCRIPT = "TypeScript"
    JAVA = "Java"
    GO = "Go"
    RUST = "Rust"
    CPP = "C++"
    C = "C"
    CSHARP = "C#"
    RUBY = "Ruby"
    PHP = "PHP"
    SWIFT = "Swift"
    KOTLIN = "Kotlin"
    SCALA = "Scala"
    DART = "Dart"
    LUA = "Lua"
    SHELL = "Shell"
    HTML = "HTML"
    CSS = "CSS"
    SQL = "SQL"
    OTHER = "Other"


class ProjectType(Enum):
    WEB_FRONTEND = "Web Frontend"
    WEB_BACKEND = "Web Backend"
    FULLSTACK = "Full-Stack Web"
    MOBILE = "Mobile App"
    CLI = "CLI Tool"
    LIBRARY = "Library/Package"
    API = "API Service"
    DATA_SCIENCE = "Data Science"
    DEVOPS = "DevOps/Infrastructure"
    GAME = "Game"
    EMBEDDED = "Embedded/IoT"
    OTHER = "Other"


class ImageStyle(Enum):
    UNSPLASH = "unsplash"
    DALLE = "dalle"
    BOTH = "both"


@dataclass
class FileInfo:
    path: Path
    relative_path: str
    extension: str
    language: Language | None = None
    line_count: int = 0
    size_bytes: int = 0


@dataclass
class CodeSnippet:
    file_path: str
    language: Language
    content: str
    description: str = ""


@dataclass
class ProjectAnalysis:
    root_path: Path
    name: str
    files: list[FileInfo] = field(default_factory=list)
    languages: dict[Language, int] = field(default_factory=dict)  # lang → file count
    primary_language: Language | None = None
    project_types: list[ProjectType] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    readme_content: str = ""
    snippets: list[CodeSnippet] = field(default_factory=list)
    total_files: int = 0
    total_lines: int = 0
    summary: str = ""


@dataclass
class Topic:
    title: str
    hook: str
    angle: str
    target_audience: str
    estimated_sections: list[str] = field(default_factory=list)


@dataclass
class ImagePlaceholder:
    marker: str  # e.g. "[IMAGE: description of what to show]"
    description: str
    position: int  # character offset in markdown


@dataclass
class ImageInfo:
    url: str
    alt_text: str
    source: str  # "unsplash" or "dalle"
    attribution: str = ""  # for Unsplash credit
    local_path: str | None = None  # temp file for DALL-E uploads


@dataclass
class Article:
    title: str
    subtitle: str
    markdown: str  # raw markdown with image placeholders
    tags: list[str] = field(default_factory=list)
    image_placeholders: list[ImagePlaceholder] = field(default_factory=list)
    images: list[ImageInfo] = field(default_factory=list)
    final_markdown: str = ""  # markdown with images resolved


