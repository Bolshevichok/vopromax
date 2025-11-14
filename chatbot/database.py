from datetime import datetime, timedelta
from typing import Optional, List
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Engine,
    ForeignKey,
    Text,
    Boolean,
    func,
    select,
    and_,
)
from sqlalchemy.orm import (
    Mapped,
    Session,
    declarative_base,
    mapped_column,
    relationship,
)
from datetime import timedelta, date

Base = declarative_base()


class User(Base):
    """Пользователь чат-бота

    Args:
        id (int): id пользователя
        vk_id (int | None): id пользователя ВКонтакте
        telegram_id (int | None): id пользователя Telegram
        is_subscribed (bool): состояние подписки пользователя
        question_answers (List[QuestionAnswer]): вопросы пользователя
        created_at (datetime): время создания модели
        updated_at (datetime): время обновления модели
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    max_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    is_subscribed: Mapped[bool] = mapped_column()

    question_answers: Mapped[List["QuestionAnswer"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(QuestionAnswer.created_at)",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class QuestionAnswer(Base):
    """Вопрос пользователя с ответом на него

    Args:
        id (int): id ответа
        question (str): вопрос пользователя
        answer (str | None): ответ на вопрос пользователя
        confluence_url (str | None): ссылка на страницу в вики-системе, содержащую ответ
        score (int | None): оценка пользователем ответа
        user_id (int): id пользователя, задавшего вопрос
        user (User): пользователь, задавший вопрос
        created_at (datetime): время создания модели
        updated_at (datetime): время обновления модели
        stop_point (bool): флаг, указывающий что это конечная точка диалога (True - диалог завершен, False - продолжается, по умолчанию False)
    """

    __tablename__ = "question_answer"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text())
    answer: Mapped[Optional[str]] = mapped_column(Text())
    confluence_url: Mapped[Optional[str]] = mapped_column(Text(), index=True)
    score: Mapped[Optional[int]] = mapped_column()
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    user: Mapped["User"] = relationship(back_populates="question_answers")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    stop_point: Mapped[bool] = mapped_column(Boolean(), default=False)


def add_user(
    engine: Engine,
    max_id: int | None = None,
) -> tuple[bool, int]:
    """Функция добавления в БД пользователя виртуального помощника

    Args:
        engine (Engine): подключение к БД
        max_id (int | None): id пользователя MAX

    Returns:
        tuple[bool, int]: добавился пользователь или нет, какой у него id в БД
    """

    with Session(engine) as session:
        if max_id is not None:
            user = session.scalar(select(User).where(User.max_id == max_id))

        if user is None:
            user = User(
                max_id=max_id,
                is_subscribed=True,
            )
            session.add(user)
            session.commit()
            return True, user.id

        return False, user.id


def get_user_id(engine: Engine, max_id: int | None = None) -> int | None:
    """Функция получения из БД пользователя

    Args:
        engine (Engine): подключение к БД
        max_id (int | None): id пользователя МАХ

    Returns:
        int | None: id пользователя или None
    """

    with Session(engine) as session:
        if max_id is not None:
            user = session.scalar(select(User).where(User.max_id == max_id))

        return user.id if user else None


def subscribe_user(engine: Engine, user_id: int) -> bool:
    """Функция оформления подписки пользователя на рассылку

    Args:
        engine (Engine): подключение к БД
        user_id (int): id пользователя

    Returns:
        bool: подписан пользователь или нет
    """

    with Session(engine) as session:
        user = session.scalars(select(User).where(User.id == user_id)).first()
        if user is None:
            return False
        user.is_subscribed = not user.is_subscribed
        session.commit()
        return user.is_subscribed


def check_spam(engine: Engine, user_id: int) -> bool:
    """Функция проверки на спам

    Args:
        engine (Engine): подключение к БД
        user_id (int): id пользователя

    Returns:
        bool: пользователь задал пять вопросов за последнюю минуту
    """

    with Session(engine) as session:
        user = session.scalars(select(User).where(User.id == user_id)).first()
        if user is None:
            return False
        if len(user.question_answers) > 5:
            minute_ago = datetime.now() - timedelta(minutes=1)
            fifth_message_date = user.question_answers[4].created_at
            return minute_ago < fifth_message_date.replace(tzinfo=None)
        return False


def add_question_answer(
    engine: Engine, question: str, answer: str, confluence_url: str | None, user_id: int
) -> int:
    """Функция добавления в БД вопроса пользователя с ответом на него

    Args:
        engine (Engine): подключение к БД
        question (str): вопрос пользователя
        answer (str): ответ на вопрос пользователя
        confluence_url (str | None): ссылка на страницу в вики-системе, содержащую ответ
        user_id (int): id пользователя

    Returns:
        int: id вопроса с ответом на него
    """

    with Session(engine) as session:
        question_answer = QuestionAnswer(
            question=question,
            answer=answer,
            confluence_url=confluence_url,
            user_id=user_id,
        )
        session.add(question_answer)
        session.flush()
        session.refresh(question_answer)
        session.commit()
        if question_answer.id is None:
            return 0
        return question_answer.id


def rate_answer(engine: Engine, question_answer_id: int, score: int) -> bool:
    """Функция оценивания ответа на вопрос

    Args:
        engine (Engine): подключение к БД
        question_answer_id (int): id вопроса с ответом
        score (int): оценка ответа

    Returns:
        bool: удалось добавить в БД оценку ответа или нет
    """

    with Session(engine) as session:
        question_answer = session.scalars(
            select(QuestionAnswer).where(QuestionAnswer.id == question_answer_id)
        ).first()
        if question_answer is None:
            return False
        question_answer.score = score
        session.commit()
        return True


def get_history_of_chat(
    engine: Engine, user_id: int, time: int = 30, limit_pairs: int = 5
) -> List[QuestionAnswer]:
    """Получает историю чата с пользователем за последние время

    Args:
        user (User): пользователь, для которого получаем историю чата
        session (Session): сессия базы данных
        time (int): время в минутах, за которое получаем историю чата
        limit_pairs (int): максимальное количество пар вопросов-ответов

    Returns:
       List[QuestionAnswer]: список пар вопросов-ответов и вопросов без ответов
    """
    with Session(engine) as session:
        user = session.query(User).get(user_id)
        if not user:
            return []

        now = datetime.now()
        cutoff_time = now - timedelta(minutes=time)

        recent_qa = (
            session.query(QuestionAnswer)
            .filter(
                QuestionAnswer.user_id == user.id,
                QuestionAnswer.created_at >= cutoff_time,
            )
            .order_by(QuestionAnswer.created_at.asc())
            .all()
        )

        full_pairs = [qa for qa in recent_qa if qa.answer != ""]
        if len(full_pairs) > limit_pairs:
            full_pairs = full_pairs[-limit_pairs:]

        unanswered = [qa for qa in recent_qa if qa.answer == ""]

        result = full_pairs + unanswered
        return result


def filter_chat_history(
    history: List[QuestionAnswer],
) -> tuple[List[QuestionAnswer], List[QuestionAnswer]]:
    """Фильтрует историю чата, оставляя:
    - Все пары вопрос-ответ
    - Неотвеченные вопросы, которые появились после последнего ответа.

    Args:
        history (List[QuestionAnswer]): Список вопросов и ответов из get_history_of_chat.

    Returns:
        Tuple[List[QuestionAnswer], List[QuestionAnswer]]:
        (отвеченные_пары, актуальные_неотвеченные)
    """
    if not history:
        return [], []

    stop_indices = [i for i, qa in enumerate(history) if qa.stop_point]
    last_stop_idx = stop_indices[-1] if stop_indices else -1

    trimmed_history = history[last_stop_idx + 1 :] if last_stop_idx != -1 else history

    pairs = [qa for qa in trimmed_history if qa.answer != ""]
    unanswered = [qa for qa in trimmed_history if qa.answer == ""]

    if not pairs:
        return [], unanswered

    last_answer_time = max(qa.created_at for qa in pairs)
    filtered_unanswered = [qa for qa in unanswered if qa.created_at > last_answer_time]  # type: ignore

    return pairs, filtered_unanswered


def set_stop_point(engine: Engine, user_id: int, valbool: bool):
    """Функция устанавливает значение stop_point для последнего сообщения пользователя.

    Args:
        engine (Engine): подключение к БД
        user_id (int): id пользователя
        valbool (bool): значение для stop_point
    """
    with Session(engine) as session:
        last_message = session.scalars(
            select(QuestionAnswer)
            .where(QuestionAnswer.user_id == user_id)
            .order_by(QuestionAnswer.created_at.desc())
        ).first()

        if last_message is not None:
            last_message.stop_point = valbool
            session.commit()
