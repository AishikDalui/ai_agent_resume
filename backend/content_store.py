from sqlalchemy import Boolean, Integer, String, Text, inspect, text, select
from sqlalchemy.orm import Mapped, mapped_column, Session

from db import Base


class SiteProfile(Base):
    __tablename__ = "site_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    about_me: Mapped[str] = mapped_column(Text, nullable=False)
    contact_heading: Mapped[str] = mapped_column(String(80), nullable=False, default="Contact")
    demo_video_url: Mapped[str] = mapped_column(String(1200), nullable=False, default="")
    auto_call_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_call_from_number: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    contact_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=(
            "Want to know more about my work or experience? "
            "Use the Chat with me button at the top to start a conversation."
        ),
    )


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(String(800), nullable=False, default="")
    image_file_id: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    project_link: Mapped[str] = mapped_column(String(1200), nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


DEFAULT_ABOUT_ME = (
    "I specialize in data analysis, dashboarding, and storytelling with data. "
    "This portfolio is powered by an AI chat assistant that can answer questions "
    "based on my resume and portfolio PDF."
)
DEFAULT_CONTACT_HEADING = "Contact"
DEFAULT_DEMO_VIDEO_URL = "https://www.youtube.com/watch?v=oJ-AQLMooXU"
DEFAULT_AUTO_CALL_ENABLED = False
DEFAULT_AUTO_CALL_FROM_NUMBER = ""
DEFAULT_CONTACT_MESSAGE = (
    "Want to know more about my work or experience? "
    "Use the Chat with me button at the top to start a conversation."
)

DEFAULT_SKILLS = [
    "SQL",
    "Python (Pandas, NumPy)",
    "Power BI / Tableau",
    "Excel",
    "Statistics",
    "A/B Testing",
    "Data Cleaning",
    "Business Reporting",
    "ETL",
    "Communication",
]

DEFAULT_PROJECTS = [
    {
        "title": "Sales Performance Dashboard",
        "description": (
            "Built an interactive dashboard to track regional sales performance, "
            "using SQL + Power BI, improving reporting speed by 40%."
        ),
        "image_url": "",
    },
    {
        "title": "Customer Churn Analysis",
        "description": (
            "Performed churn modeling using Python and logistic regression, "
            "identifying key drivers of customer retention."
        ),
        "image_url": "",
    },
]


def seed_default_content(db: Session) -> None:
    profile = db.scalar(select(SiteProfile).limit(1))
    if not profile:
        db.add(
            SiteProfile(
                id=1,
                about_me=DEFAULT_ABOUT_ME,
                contact_heading=DEFAULT_CONTACT_HEADING,
                demo_video_url=DEFAULT_DEMO_VIDEO_URL,
                auto_call_enabled=DEFAULT_AUTO_CALL_ENABLED,
                auto_call_from_number=DEFAULT_AUTO_CALL_FROM_NUMBER,
                contact_message=DEFAULT_CONTACT_MESSAGE,
            )
        )

    skill_count = db.query(Skill).count()
    if skill_count == 0:
        for idx, skill_name in enumerate(DEFAULT_SKILLS):
            db.add(Skill(name=skill_name, sort_order=idx))

    project_count = db.query(Project).count()
    if project_count == 0:
        for idx, project_data in enumerate(DEFAULT_PROJECTS):
            db.add(
                Project(
                    title=project_data["title"],
                    description=project_data["description"],
                    image_url=project_data["image_url"],
                    image_file_id="",
                    project_link="",
                    sort_order=idx,
                )
            )

    db.commit()


def migrate_content_schema(db: Session) -> None:
    engine = db.get_bind()
    inspector = inspect(engine)

    if "site_profile" in inspector.get_table_names():
        site_profile_columns = {col["name"] for col in inspector.get_columns("site_profile")}
        if "contact_heading" not in site_profile_columns:
            db.execute(
                text(
                    "ALTER TABLE site_profile "
                    "ADD COLUMN contact_heading VARCHAR(80) NOT NULL DEFAULT 'Contact'"
                )
            )
        if "contact_message" not in site_profile_columns:
            db.execute(
                text(
                    "ALTER TABLE site_profile "
                    "ADD COLUMN contact_message TEXT NOT NULL DEFAULT "
                    "'Want to know more about my work or experience? "
                    "Use the Chat with me button at the top to start a conversation.'"
                )
            )
        if "demo_video_url" not in site_profile_columns:
            db.execute(
                text(
                    "ALTER TABLE site_profile "
                    "ADD COLUMN demo_video_url VARCHAR(1200) NOT NULL DEFAULT "
                    "'https://www.youtube.com/watch?v=oJ-AQLMooXU'"
                )
            )
        if "auto_call_enabled" not in site_profile_columns:
            db.execute(
                text(
                    "ALTER TABLE site_profile "
                    "ADD COLUMN auto_call_enabled BOOLEAN NOT NULL DEFAULT FALSE"
                )
            )
        if "auto_call_from_number" not in site_profile_columns:
            db.execute(
                text(
                    "ALTER TABLE site_profile "
                    "ADD COLUMN auto_call_from_number VARCHAR(40) NOT NULL DEFAULT ''"
                )
            )

    if "projects" in inspector.get_table_names():
        project_columns = {col["name"] for col in inspector.get_columns("projects")}
        if "image_file_id" not in project_columns:
            db.execute(
                text(
                    "ALTER TABLE projects "
                    "ADD COLUMN image_file_id VARCHAR(200) NOT NULL DEFAULT ''"
                )
            )
        if "sort_order" not in project_columns:
            db.execute(
                text(
                    "ALTER TABLE projects "
                    "ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0"
                )
            )
        if "project_link" not in project_columns:
            db.execute(
                text(
                    "ALTER TABLE projects "
                    "ADD COLUMN project_link VARCHAR(1200) NOT NULL DEFAULT ''"
                )
            )

    if "skills" in inspector.get_table_names():
        skills_columns = {col["name"] for col in inspector.get_columns("skills")}
        if "sort_order" not in skills_columns:
            db.execute(
                text(
                    "ALTER TABLE skills "
                    "ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0"
                )
            )

    db.commit()
