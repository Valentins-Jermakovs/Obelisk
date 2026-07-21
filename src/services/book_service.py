# =====================================================
#                        Imports
# =====================================================

# Libraries:
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, or_, func

# Helper functions:
from utils.service_utils import (
    _check_isbn_unique,
    _validate_existing_ids,
    _create_book,
    _create_copies,
    _link_authors,
    _link_genres,
    _link_languages,
    _create_images,
    _validate_copies,
    _validate_librarian_access_to_book
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
    FactLoan,
    DimShelf,
    DimLibrary,
    DimPublisher,
    LoanStatus,
    AuditAction, 
    EntityType
)

# Schemas:
from schemas import BookCreate, BookUpdate

# Services:
from services.audit_service import (
    write_audit_log, 
    write_failed_audit_log
)



# =====================================================
#                     Services
# =====================================================

# Create book service
async def create_book(
    session: AsyncSession,
    data: BookCreate,
    payload: dict | None = None
):
    try:
        # 1. ISBN check
        await _check_isbn_unique(session, data.isbn.strip())

        # 2. Validate FK entities (if empty - skip)
        await _validate_existing_ids(session, DimAuthor, data.authors, "Author")
        await _validate_existing_ids(session, DimGenre, data.genres, "Genre")
        await _validate_existing_ids(session, DimLanguage, data.languages, "Language")
        if data.publisher_id is not None:
            await _validate_existing_ids(session, DimPublisher, [data.publisher_id], "Publisher")

        # 3. Validate copies early so the book is not created if copy validation fails
        if hasattr(data, "copies"):
            await _validate_copies(session, data.copies, payload)

        # 4. Create base book
        book = await _create_book(session, data)

        # 5. Set relations
        await _link_authors(session, book.id, data.authors)
        await _link_genres(session, book.id, data.genres)
        await _link_languages(session, book.id, data.languages)

        # 6. Images (optional)
        if data.images:
            await _create_images(session, book.id, data.images)

        # 7. Copies + positions (optional but usually important)
        if data.copies:
            await _create_copies(session, book.id, data.copies, payload)

        
        # Flush to get all generated IDs
        await session.flush()


        # Success audit
        if payload:

            # Write audit
            await write_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.CREATE,
                entity_type=EntityType.BOOK,
                description=f"Created book '{book.title}'",
                book_id=book.id,
                title=book.title,
                isbn=book.isbn,
                publication_year=book.publication_year,
                authors=data.authors,
                genres=data.genres,
                languages=data.languages,
                publisher_id=data.publisher_id,
                pages=data.pages,
                images_count=len(data.images),
                copies_count=len(data.copies),
            )
        
        # Commit everything
        await session.commit()

        await session.refresh(book)

        return book


    # Rollback everything on error
    except HTTPException as e:

        await session.rollback()

        if payload:

            # Write failed audit
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.CREATE,
                entity_type=EntityType.BOOK,
                description="Failed to create book",
                error=str(e.detail),
                title=data.title,
                isbn=data.isbn,
            )

            # Commit log
            await session.commit()

        raise

    # Unexpected error on creation
    except Exception as e:

        await session.rollback()

        if payload:

            # Write failed audit
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.CREATE,
                entity_type=EntityType.BOOK,
                description="Failed to create book",
                error=str(e),
                title=data.title,
                isbn=data.isbn,
            )

            # Commit log
            await session.commit()

        # Unexpected error on creation
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error while creating book: {str(e)}"
        )
    


# Update book service
async def update_book(
    session: AsyncSession,
    book_id: int,
    data: BookUpdate,
    payload: dict | None = None
):
    try:
        # 1. Load book
        book = await session.get(DimBook, book_id)

        if not book:

            # Write failed audit
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.UPDATE,
                entity_type=EntityType.BOOK,
                description=f"Failed to update book with id {book_id}",
                error="Book not found",
                book_id=book_id,
            )

            # Commit log
            await session.commit()

            # Raise exception
            raise HTTPException(
                status_code=404,
                detail="Book not found"
            )
        
        # Save old data
        old_data = {
            "title": book.title,
            "isbn": book.isbn,
            "annotation": book.annotation,
            "publication_year": book.publication_year,
            "publisher_id": book.publisher_id,
            "pages": book.pages,
        }

        # Access validation
        if payload and "admin" not in payload.get("roles", []):
            await _validate_librarian_access_to_book(session, payload, book_id)

        # 2. ISBN unique check (if changing)
        if data.isbn and data.isbn != book.isbn:
            await _check_isbn_unique(session, data.isbn.strip())

        # 3. Basic fields update
        if data.publisher_id is not None:
            await _validate_existing_ids(session, DimPublisher, [data.publisher_id], "Publisher")

        # Update fields in cycle
        for field in ["title", "isbn", "annotation", "publication_year", "publisher_id", "pages"]:
            value = getattr(data, field, None)
            if value is not None:
                setattr(book, field, value.strip() if isinstance(value, str) else value)


        # 4. RELATIONS (replace strategy)
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


        # 5. IMAGES (full replace)
        if data.images is not None:
            await session.exec(
                BookImage.__table__.delete().where(BookImage.book_id == book_id)
            )
            await _create_images(session, book_id, data.images)


        # 6. COPIES (danger zone — full replace)
        if data.copies is not None:
            await _validate_copies(session, data.copies, payload)

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

            await _create_copies(session, book_id, data.copies, payload)


        await session.flush()


        # New data
        new_data = {
            "title": book.title,
            "isbn": book.isbn,
            "annotation": book.annotation,
            "publication_year": book.publication_year,
            "publisher_id": book.publisher_id,
            "pages": book.pages,
        }

        # Success audit
        await write_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.UPDATE,
            entity_type=EntityType.BOOK,
            description=f"Updated book '{book.title}'",
            book_id=book.id,
            old_data=old_data,
            new_data=new_data,
        )

        # Commit everything
        await session.commit()
        await session.refresh(book)

        return book

    # Return the updated book
    except HTTPException:
        await session.rollback()
        raise

    # Unexpected error handling
    except Exception as e:

        await session.rollback()

        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.UPDATE,
            entity_type=EntityType.BOOK,
            description=f"Failed to update book with id {book_id}",
            error=str(e),
            book_id=book_id,
        )

        await session.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to update book: {str(e)}"
        )
    


# Delete book service
async def delete_book(
    session: AsyncSession,
    book_id: int,
    force: bool = False,
    payload: dict | None = None
):
    try:
        # 1. Load book
        book = await session.get(DimBook, book_id)

        if not book:

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.DELETE,
                entity_type=EntityType.BOOK,
                description=f"Failed to delete book with id {book_id}",
                error="Book not found",
                book_id=book_id,
            )

            # Commit log
            await session.commit()

            # Raise 404 error
            raise HTTPException(
                status_code=404, 
                detail="Book not found"
            )

        # Save old data
        old_data = {
            "id": book.id,
            "title": book.title,
            "isbn": book.isbn,
            "annotation": book.annotation,
            "publication_year": book.publication_year,
        }

        # Access validation
        if payload and "admin" not in payload.get("roles", []):

            # Check if the book is linked to any library
            library_rows = (await session.exec(
                select(DimShelf.library_id)
                .join(BookPosition, BookPosition.shelf_id == DimShelf.id)
                .join(DimBookCopy, DimBookCopy.id == BookPosition.book_copy_id)
                .where(DimBookCopy.book_id == book_id)
                .distinct()
            )).all()
            library_ids = [row[0] if isinstance(row, tuple) else row for row in library_rows]


            # If book not assigned to any library, only administrator can delete it
            if not library_ids:

                # Write failed audit log
                await write_failed_audit_log(
                    session=session,
                    payload=payload,
                    action=AuditAction.DELETE,
                    entity_type=EntityType.BOOK,
                    description=f"Failed to delete book '{book.title}'",
                    error="Book has no library assignment",
                    book_id=book.id,
                )

                # Commit log
                await session.commit()

                # Return error response
                raise HTTPException(
                    status_code=403,
                    detail="Book has no library assignment and cannot be deleted by a librarian"
                )

            # Validate librarian access to book
            await _validate_librarian_access_to_book(session, payload, book_id)


        # 2. CHECK ACTIVE LOANS (CRITICAL)
        active_loans = (await session.exec(
            select(FactLoan).join(DimBookCopy).where(
                DimBookCopy.book_id == book_id,
                FactLoan.status.in_([
                    LoanStatus.ACTIVE,
                    LoanStatus.OVERDUE,
                    LoanStatus.LOST
                ])
            )
        )).first()

        # Warning mode: if there are active loans, we can't delete the book
        if active_loans and not force:

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.DELETE,
                entity_type=EntityType.BOOK,
                description=f"Failed to delete book '{book.title}'",
                error="Book has active loans",
                book_id=book.id,
                force=force,
            )

            # Commit log
            await session.commit()

            # Return warning
            return {
                "warning": "Book has active loans",
                "message": "Set force=true to delete anyway",
                "blocked_reason": "active_loans"
            }


        # 3. CHECK OTHER LINKS (optional warning mode)
        copies = (await session.exec(
            select(DimBookCopy).where(DimBookCopy.book_id == book_id)
        )).all()

        copy_count = len(copies)


        if copies and not force:

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.DELETE,
                entity_type=EntityType.BOOK,
                description=f"Failed to delete book '{book.title}'",
                error="Book has physical copies",
                book_id=book.id,
                copies_count=copy_count,
            )

            # Commit log
            await session.commit()

            # Return warning
            return {
                "warning": "Book has physical copies",
                "copies_count": len(copies),
                "message": "Set force=true to delete everything"
            }


        # 4. FORCE DELETE CASCADE (manual control)
        if copies:
            copy_ids = [c.id for c in copies]

            # positions
            await session.exec(
                BookPosition.__table__.delete().where(
                    BookPosition.book_copy_id.in_(copy_ids)
                )
            )

            # Loans (historical cleanup if needed)
            await session.exec(
                FactLoan.__table__.delete().where(
                    FactLoan.book_copy_id.in_(copy_ids)
                )
            )

            # Copies
            await session.exec(
                DimBookCopy.__table__.delete().where(
                    DimBookCopy.id.in_(copy_ids)
                )
            )

        # Relations
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


        # 5. DELETE BOOK ITSELF
        await session.delete(book)

        await session.flush()

        # Success audit
        await write_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.BOOK,
            description=f"Deleted book '{book.title}'",
            book_id=book_id,
            title=book.title,
            isbn=book.isbn,
            deleted_copies=copy_count,
            force=force,
            old_data=old_data,
        )


        await session.commit()

        return {
            "status": "deleted",
            "book_id": book_id
        }

    # Rollback if an exception occurs during the transaction
    except HTTPException:
        await session.rollback()
        raise

    # Unexpected error occurred during the transaction
    except Exception as e:

        await session.rollback()

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.BOOK,
            description=f"Failed to delete book with id {book_id}",
            error=str(e),
            book_id=book_id,
        )

        # Commit log
        await session.commit()

        # Raise an HTTPException with a 500 status code and the error message
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete book: {str(e)}"
        )
    


# Search service
async def search_books(
    session: AsyncSession,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    try:

        # BASE QUERY
        stmt = select(DimBook)

        if query:
            # Normalize query to lowercase and strip whitespace
            q = query.strip().lower()

            if q:
                # Search by title, ISBN, or annotation
                stmt = stmt.where(
                    or_(
                        DimBook.title.ilike(f"%{q}%"),
                        DimBook.isbn.ilike(f"%{q}%"),
                        DimBook.annotation.ilike(f"%{q}%"),

                        DimBook.publisher_id.in_(
                            select(DimPublisher.id).where(
                                DimPublisher.name.ilike(f"%{q}%")
                            )
                        ),

                        # Author join
                        DimBook.id.in_(
                            select(BookAuthor.book_id).join(DimAuthor).where(
                                DimAuthor.name.ilike(f"%{q}%")
                            )
                        ),

                        # Genre join
                        DimBook.id.in_(
                            select(BookGenre.book_id).join(DimGenre).where(
                                DimGenre.name.ilike(f"%{q}%")
                            )
                        ),

                        # Language join
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


        # TOTAL COUNT
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.exec(count_stmt)).one()


        # PAGINATION
        stmt = stmt.offset(offset).limit(limit)
        books = (await session.exec(stmt)).all()


        # ENRICH RESULTS
        results = []

        for book in books:
            # Copies
            copies = (await session.exec(
                select(DimBookCopy).where(DimBookCopy.book_id == book.id)
            )).all()

            copy_ids = [c.id for c in copies]

            # Active loans
            active_loans = 0
            if copy_ids:
                active_loans = (await session.exec(
                    select(func.count(FactLoan.id)).where(
                        FactLoan.book_copy_id.in_(copy_ids),
                        FactLoan.status.in_([
                            LoanStatus.ACTIVE,
                            LoanStatus.OVERDUE,
                            LoanStatus.LOST
                        ])
                    )
                )).one()

            total_copies = len(copy_ids)
            available = total_copies - active_loans

            # Availability status
            if total_copies == 0:
                status = "no_copies"
            elif available <= 0:
                status = "borrowed"
            elif available < total_copies:
                status = "partially_available"
            else:
                status = "available"

            # Libraries breakdown
            libraries_list = []

            if copy_ids:
                # Which copy ids are currently loaned
                active_loan_rows = (await session.exec(
                    select(FactLoan.book_copy_id).where(
                        FactLoan.book_copy_id.in_(copy_ids),
                        FactLoan.status.in_([
                            LoanStatus.ACTIVE,
                            LoanStatus.OVERDUE,
                            LoanStatus.LOST
                        ])
                    )
                )).all()

                active_loan_copy_ids = set(active_loan_rows)

                # Positions with shelf + library
                pos_rows = (await session.exec(
                    select(BookPosition, DimShelf, DimLibrary)
                    .join(DimShelf, BookPosition.shelf_id == DimShelf.id)
                    .join(DimLibrary, DimShelf.library_id == DimLibrary.id)
                    .where(BookPosition.book_copy_id.in_(copy_ids))
                )).all()

                # Aggregate per library
                lib_map: dict[int, dict] = {}
                for pos, shelf, lib in pos_rows:
                    copy_id = pos.book_copy_id
                    entry = lib_map.setdefault(lib.id, {
                        "id": lib.id,
                        "name": lib.name,
                        "city": lib.city,
                        "address": lib.address,
                        "total_copies": 0,
                        "active_loans": 0
                    })

                    entry["total_copies"] += 1
                    if copy_id in active_loan_copy_ids:
                        entry["active_loans"] += 1

                # Aggregate per library
                for lid, v in lib_map.items():
                    av = v["total_copies"] - v["active_loans"]
                    libraries_list.append({
                        "id": v["id"],
                        "name": v["name"],
                        "city": v["city"],
                        "address": v["address"],
                        "total_copies": v["total_copies"],
                        "available_copies": av,
                        "active_loans": v["active_loans"]
                    })

            # Aggregate per book
            publisher = None
            if book.publisher_id is not None:
                publisher_row = await session.get(DimPublisher, book.publisher_id)
                if publisher_row is not None:
                    publisher = {"id": publisher_row.id, "name": publisher_row.name}

            results.append({
                "id": book.id,
                "title": book.title,
                "isbn": book.isbn,
                "annotation": book.annotation,
                "publication_year": book.publication_year,
                "publisher_id": book.publisher_id,
                "pages": book.pages,
                "publisher": publisher,

                "availability": {
                    "status": status,
                    "total_copies": total_copies,
                    "available_copies": available,
                    "active_loans": active_loans
                },

                "libraries": libraries_list
            })

        has_more = offset + len(results) < total

        return {
            "items": results,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
        }

    # Unexpected error handling
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
    
    

# Get book by id service
async def get_book(
    session: AsyncSession,
    book_id: int
):
    try:

        # 1. BASE BOOK
        book = await session.get(DimBook, book_id)

        if not book:
            raise HTTPException(404, "Book not found")


        # 2. AUTHORS
        author_rows = (await session.exec(
            select(DimAuthor)
            .join(BookAuthor)
            .where(BookAuthor.book_id == book_id)
        )).all()


        # 3. GENRES
        genre_rows = (await session.exec(
            select(DimGenre)
            .join(BookGenre)
            .where(BookGenre.book_id == book_id)
        )).all()


        # 4. LANGUAGES
        language_rows = (await session.exec(
            select(DimLanguage)
            .join(BookLanguage)
            .where(BookLanguage.book_id == book_id)
        )).all()


        # 5. IMAGES
        images = (await session.exec(
            select(BookImage).where(BookImage.book_id == book_id)
        )).all()


        # 6. COPIES
        copies = (await session.exec(
            select(DimBookCopy).where(DimBookCopy.book_id == book_id)
        )).all()

        copy_ids = [c.id for c in copies]

        # Copy positions and shelves
        copy_positions = {}
        if copy_ids:
            pos_rows = (await session.exec(
                select(BookPosition, DimShelf)
                .join(DimShelf, BookPosition.shelf_id == DimShelf.id)
                .where(BookPosition.book_copy_id.in_(copy_ids))
            )).all()

            for pos, shelf in pos_rows:
                copy_positions[pos.book_copy_id] = {
                    "shelf": {
                        "id": shelf.id,
                        "code": shelf.code,
                        "section": shelf.section
                    },
                    "position": {
                        "row": pos.row,
                        "column": pos.column,
                        "depth": pos.depth
                    }
                }


        # 7. LOANS + AVAILABILITY
        active_loans = 0

        if copy_ids:
            active_loans = (await session.exec(
                select(func.count(FactLoan.id)).where(
                    FactLoan.book_copy_id.in_(copy_ids),
                    FactLoan.status.in_([
                        LoanStatus.ACTIVE,
                        LoanStatus.OVERDUE,
                        LoanStatus.LOST
                    ])
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


        # 8. RESPONSE
        # Libraries breakdown
        libraries_list = []

        if copy_ids:
            active_loan_rows = (await session.exec(
                select(FactLoan.book_copy_id).where(
                    FactLoan.book_copy_id.in_(copy_ids),
                    FactLoan.status.in_([
                        LoanStatus.ACTIVE,
                        LoanStatus.OVERDUE,
                        LoanStatus.LOST
                    ])
                )
            )).all()

            active_loan_copy_ids = set([r[0] if isinstance(r, tuple) else r for r in active_loan_rows])

            pos_rows = (await session.exec(
                select(BookPosition, DimShelf, DimLibrary)
                .join(DimShelf, BookPosition.shelf_id == DimShelf.id)
                .join(DimLibrary, DimShelf.library_id == DimLibrary.id)
                .where(BookPosition.book_copy_id.in_(copy_ids))
            )).all()

            lib_map: dict[int, dict] = {}
            # Create library map
            for pos, shelf, lib in pos_rows:
                copy_id = pos.book_copy_id
                entry = lib_map.setdefault(lib.id, {
                    "id": lib.id,
                    "name": lib.name,
                    "city": lib.city,
                    "address": lib.address,
                    "total_copies": 0,
                    "active_loans": 0
                })

                entry["total_copies"] += 1
                if copy_id in active_loan_copy_ids:
                    entry["active_loans"] += 1

            # Create the response
            for lid, v in lib_map.items():
                av = v["total_copies"] - v["active_loans"]
                libraries_list.append({
                    "id": v["id"],
                    "name": v["name"],
                    "city": v["city"],
                    "address": v["address"],
                    "total_copies": v["total_copies"],
                    "available_copies": av,
                    "active_loans": v["active_loans"]
                })

        publisher = None
        if book.publisher_id is not None:
            publisher_row = await session.get(DimPublisher, book.publisher_id)
            if publisher_row is not None:
                publisher = {"id": publisher_row.id, "name": publisher_row.name}

        return {
            "id": book.id,
            "title": book.title,
            "isbn": book.isbn,
            "annotation": book.annotation,
            "publication_year": book.publication_year,
            "publisher_id": book.publisher_id,
            "pages": book.pages,
            "publisher": publisher,

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
                    "condition": c.condition,
                    "shelf": copy_positions.get(c.id, {}).get("shelf"),
                    "position": copy_positions.get(c.id, {}).get("position")
                }
                for c in copies
            ],

            "availability": {
                "status": status,
                "total_copies": total_copies,
                "available_copies": available,
                "active_loans": active_loans
            },

            "libraries": libraries_list
        }

    # Raise an exception
    except HTTPException:
        raise

    # Unexpected error
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get book: {str(e)}"
        )