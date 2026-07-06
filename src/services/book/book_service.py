# ===================================================
#                       imports
# ===================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, or_, func
# Helper functions:
from .book_service_helpers import (
    _check_isbn_unique,
    _validate_existing_ids,
    _create_book,
    _create_copies,
    _link_authors,
    _link_genres,
    _link_languages,
    _create_images
)
# Models:
from models import (
    DimAuthor,
    DimGenre,
    DimLanguage,
    BookAuthor,
    DimBook,
    BookGenre,
    BookLanguage,
    BookImage,
    DimBookCopy,
    BookPosition,
    FactLoan
)
# Schemas:
from schemas.book import BookCreate, BookUpdate
# ===================================================

# ===================================================
#                       functions
# ===================================================

# Create book
async def create_book(
    session: AsyncSession,
    data: BookCreate,
):
    try:
        # 1. ISBN check
        await _check_isbn_unique(session, data.isbn.strip())

        # 2. Validate FK entities (if empty - skip)
        await _validate_existing_ids(session, DimAuthor, data.author, "Author")
        await _validate_existing_ids(session, DimGenre, data.genre, "Genre")
        await _validate_existing_ids(session, DimLanguage, data.language, "Language")

        # 3. Create base book
        book = await _create_book(session, data)

        # 4. Relations
        await _link_authors(session, book.id, data.author)
        await _link_genres(session, book.id, data.genre)
        await _link_languages(session, book.id, data.language)

        # 5. Images (optional)
        if hasattr(data, "images"):
            await _create_images(session, book.id, data.images)

        # 6. Copies + positions (optional but usually important)
        if hasattr(data, "copies"):
            await _create_copies(session, book.id, data.copies)

        # 7. Commit everything
        await session.commit()
        await session.refresh(book)

        return book

    except HTTPException:
        await session.rollback()
        raise

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while creating book: {str(e)}"
        )
    


async def update_book(
    session: AsyncSession,
    book_id: int,
    data: BookUpdate
):
    try:
        # 1. Load book
        book = await session.get(DimBook, book_id)

        if not book:
            raise HTTPException(404, "Book not found")

        # 2. ISBN check (if changing)
        if data.isbn and data.isbn != book.isbn:
            await _check_isbn_unique(session, data.isbn.strip())

        # 3. Basic fields update
        for field in ["title", "isbn", "annotation", "publication_year"]:
            value = getattr(data, field, None)
            if value is not None:
                setattr(book, field, value.strip() if isinstance(value, str) else value)

        # =========================================================
        # 4. RELATIONS (replace strategy)
        # =========================================================

        # AUTHORS
        if data.authors is not None:
            await session.exec(
                select(BookAuthor).where(BookAuthor.book_id == book_id)
            )
            await session.exec(
                select(BookAuthor).where(BookAuthor.book_id == book_id)
            )
            await session.exec(
                BookAuthor.__table__.delete().where(BookAuthor.book_id == book_id)
            )

            await _validate_existing_ids(session, DimAuthor, data.authors, "Author")
            for aid in set(data.authors):
                session.add(BookAuthor(book_id=book_id, author_id=aid))

        # GENRES
        if data.genres is not None:
            await session.exec(
                BookGenre.__table__.delete().where(BookGenre.book_id == book_id)
            )

            await _validate_existing_ids(session, DimGenre, data.genres, "Genre")
            for gid in set(data.genres):
                session.add(BookGenre(book_id=book_id, genre_id=gid))

        # LANGUAGES
        if data.languages is not None:
            await session.exec(
                BookLanguage.__table__.delete().where(BookLanguage.book_id == book_id)
            )

            await _validate_existing_ids(session, DimLanguage, data.languages, "Language")
            for lid in set(data.languages):
                session.add(BookLanguage(book_id=book_id, language_id=lid))

        # =========================================================
        # 5. IMAGES (full replace)
        # =========================================================
        if data.images is not None:
            await session.exec(
                BookImage.__table__.delete().where(BookImage.book_id == book_id)
            )
            await _create_images(session, book_id, data.images)

        # =========================================================
        # 6. COPIES (danger zone — full replace)
        # =========================================================
        if data.copies is not None:

            # delete positions first
            copies = (await session.exec(
                select(DimBookCopy).where(DimBookCopy.book_id == book_id)
            )).all()

            copy_ids = [c.id for c in copies]

            if copy_ids:
                await session.exec(
                    BookPosition.__table__.delete().where(
                        BookPosition.book_copy_id.in_(copy_ids)
                    )
                )

                await session.exec(
                    DimBookCopy.__table__.delete().where(
                        DimBookCopy.id.in_(copy_ids)
                    )
                )

            await _create_copies(session, book_id, data.copies)

        # 7. Commit
        await session.commit()
        await session.refresh(book)

        return book

    except HTTPException:
        await session.rollback()
        raise

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update book: {str(e)}"
        )
    

async def delete_book(
    session: AsyncSession,
    book_id: int,
    force: bool = False
):
    try:
        # 1. Load book
        book = await session.get(DimBook, book_id)

        if not book:
            raise HTTPException(404, "Book not found")

        # ======================================================
        # 2. CHECK ACTIVE LOANS (CRITICAL)
        # ======================================================
        active_loans = (await session.exec(
            select(FactLoan).join(DimBookCopy).where(
                DimBookCopy.book_id == book_id,
                FactLoan.status == "active"
            )
        )).first()

        if active_loans and not force:
            return {
                "warning": "Book has active loans",
                "message": "Set force=true to delete anyway",
                "blocked_reason": "active_loans"
            }

        # ======================================================
        # 3. CHECK OTHER LINKS (optional warning mode)
        # ======================================================
        copies = (await session.exec(
            select(DimBookCopy).where(DimBookCopy.book_id == book_id)
        )).all()

        if copies and not force:
            return {
                "warning": "Book has physical copies",
                "copies_count": len(copies),
                "message": "Set force=true to delete everything"
            }

        # ======================================================
        # 4. FORCE DELETE CASCADE (manual control)
        # ======================================================
        if copies:
            copy_ids = [c.id for c in copies]

            # positions
            await session.exec(
                BookPosition.__table__.delete().where(
                    BookPosition.book_copy_id.in_(copy_ids)
                )
            )

            # loans (historical cleanup if needed)
            await session.exec(
                FactLoan.__table__.delete().where(
                    FactLoan.book_copy_id.in_(copy_ids)
                )
            )

            # copies
            await session.exec(
                DimBookCopy.__table__.delete().where(
                    DimBookCopy.id.in_(copy_ids)
                )
            )

        # relations
        await session.exec(
            BookAuthor.__table__.delete().where(
                BookAuthor.book_id == book_id
            )
        )

        await session.exec(
            BookGenre.__table__.delete().where(
                BookGenre.book_id == book_id
            )
        )

        await session.exec(
            BookLanguage.__table__.delete().where(
                BookLanguage.book_id == book_id
            )
        )

        await session.exec(
            BookImage.__table__.delete().where(
                BookImage.book_id == book_id
            )
        )

        # ======================================================
        # 5. DELETE BOOK ITSELF
        # ======================================================
        await session.delete(book)

        await session.commit()

        return {
            "status": "deleted",
            "book_id": book_id
        }

    except HTTPException:
        await session.rollback()
        raise

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete book: {str(e)}"
        )
    

async def search_books(
    session: AsyncSession,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    try:
        # ======================================================
        # BASE QUERY
        # ======================================================
        stmt = select(DimBook)

        if query:
            q = query.strip().lower()

            if q:
                stmt = stmt.where(
                    or_(
                        DimBook.title.ilike(f"%{q}%"),
                        DimBook.isbn.ilike(f"%{q}%"),
                        DimBook.annotation.ilike(f"%{q}%"),

                        # author join
                        DimBook.id.in_(
                            select(BookAuthor.book_id).join(DimAuthor).where(
                                DimAuthor.name.ilike(f"%{q}%")
                            )
                        ),

                        # genre join
                        DimBook.id.in_(
                            select(BookGenre.book_id).join(DimGenre).where(
                                DimGenre.name.ilike(f"%{q}%")
                            )
                        ),

                        # language join
                        DimBook.id.in_(
                            select(BookLanguage.book_id).join(DimLanguage).where(
                                or_(
                                    DimLanguage.code.ilike(f"%{q}%"),
                                    DimLanguage.name.ilike(f"%{q}%")
                                )
                            )
                        ),
                    )
                )

        # ======================================================
        # TOTAL COUNT
        # ======================================================
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.exec(count_stmt)).one()

        # ======================================================
        # PAGINATION
        # ======================================================
        stmt = stmt.offset(offset).limit(limit)
        books = (await session.exec(stmt)).all()

        # ======================================================
        # ENRICH RESULTS
        # ======================================================
        results = []

        for book in books:

            # copies
            copies = (await session.exec(
                select(DimBookCopy).where(DimBookCopy.book_id == book.id)
            )).all()

            copy_ids = [c.id for c in copies]

            # active loans
            active_loans = 0
            if copy_ids:
                active_loans = (await session.exec(
                    select(func.count(FactLoan.id)).where(
                        FactLoan.book_copy_id.in_(copy_ids),
                        FactLoan.status == "active"
                    )
                )).one()

            total_copies = len(copy_ids)
            available = total_copies - active_loans

            # availability status
            if total_copies == 0:
                status = "no_copies"
            elif available <= 0:
                status = "borrowed"
            elif available < total_copies:
                status = "partially_available"
            else:
                status = "available"

            results.append({
                "id": book.id,
                "title": book.title,
                "isbn": book.isbn,
                "annotation": book.annotation,
                "publication_year": book.publication_year,

                "availability": {
                    "status": status,
                    "total_copies": total_copies,
                    "available_copies": available,
                    "active_loans": active_loans
                }
            })

        return {
            "items": results,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
    

async def get_book(
    session: AsyncSession,
    book_id: int
):
    try:
        # =========================
        # 1. BASE BOOK
        # =========================
        book = await session.get(DimBook, book_id)

        if not book:
            raise HTTPException(404, "Book not found")

        # =========================
        # 2. AUTHORS
        # =========================
        author_rows = (await session.exec(
            select(DimAuthor)
            .join(BookAuthor)
            .where(BookAuthor.book_id == book_id)
        )).all()

        # =========================
        # 3. GENRES
        # =========================
        genre_rows = (await session.exec(
            select(DimGenre)
            .join(BookGenre)
            .where(BookGenre.book_id == book_id)
        )).all()

        # =========================
        # 4. LANGUAGES
        # =========================
        language_rows = (await session.exec(
            select(DimLanguage)
            .join(BookLanguage)
            .where(BookLanguage.book_id == book_id)
        )).all()

        # =========================
        # 5. IMAGES
        # =========================
        images = (await session.exec(
            select(BookImage).where(BookImage.book_id == book_id)
        )).all()

        # =========================
        # 6. COPIES
        # =========================
        copies = (await session.exec(
            select(DimBookCopy).where(DimBookCopy.book_id == book_id)
        )).all()

        copy_ids = [c.id for c in copies]

        # =========================
        # 7. LOANS + AVAILABILITY
        # =========================
        active_loans = 0

        if copy_ids:
            active_loans = (await session.exec(
                select(func.count(FactLoan.id)).where(
                    FactLoan.book_copy_id.in_(copy_ids),
                    FactLoan.status == "active"
                )
            )).one()

        total_copies = len(copy_ids)
        available = total_copies - active_loans

        if total_copies == 0:
            status = "no_copies"
        elif available <= 0:
            status = "borrowed"
        elif available < total_copies:
            status = "partially_available"
        else:
            status = "available"

        # =========================
        # 8. RESPONSE
        # =========================
        return {
            "id": book.id,
            "title": book.title,
            "isbn": book.isbn,
            "annotation": book.annotation,
            "publication_year": book.publication_year,

            "authors": [
                {"id": a.id, "name": a.name}
                for a in author_rows
            ],

            "genres": [
                {"id": g.id, "name": g.name}
                for g in genre_rows
            ],

            "languages": [
                {"id": l.id, "code": l.code, "name": l.name}
                for l in language_rows
            ],

            "images": [
                {
                    "id": i.id,
                    "file_path": i.file_path,
                    "image_type": i.image_type,
                    "display_order": i.display_order
                }
                for i in images
            ],

            "copies": [
                {
                    "id": c.id,
                    "inventory_code": c.inventory_code,
                    "condition": c.condition
                }
                for c in copies
            ],

            "availability": {
                "status": status,
                "total_copies": total_copies,
                "available_copies": available,
                "active_loans": active_loans
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get book: {str(e)}"
        )