# =====================================================
#                        Imports
# =====================================================

# This file contain all project schemas:

from .author import (
    AuthorCreate, 
    AuthorUpdate, 
    AuthorRead, 
    AuthorSearchResponse, 
    AuthorDeleteResponse, 
    AuthorDeleteWarning
)

from .book_copy import (
    BookCopyCreate,
    BookCopyUpdate,
    BookCopyRead,
    BookCopyDeleteResponse,
    BookCopyShelfRead,
    BookCopySearchItem,
    BookCopySearchResponse
)

from .book import (
    BookImageCreate,
    BookPositionCreate,
    BookCopyCreate,
    BookCreate,
    BookUpdate,
    PublisherShort,
    AuthorShort,
    GenreShort,
    LanguageShort,
    ImageRead,
    BookPositionRead,
    ShelfShort,
    CopyRead,
    BookAvailability,
    BookRead,
    LibraryShort,
    LibraryAvailability,
    BookSearchItem,
    BookSearchResponse,
    BookDeleteResponse,
    BookDeleteWarning
)

from .genre import (
    GenreCreate,
    GenreUpdate,
    GenreRead,
    GenreWithBooks,
    GenreSearchResponse,
    GenreDeleteResponse
)

from .language import (
    LanguageCreate,
    LanguageUpdate,
    LanguageRead,
    LanguageSearchResponse,
    LanguageDeleteResponse
)

from .librarian import (
    LibrarianCreate,
    LibrarianUpdate,
    LibraryShort,
    LibrarianRead,
    LibrarianWithLibraries,
    LibrarianSearchResponse,
    LibrarianLibraryLinkResponse,
    LibrarianLibraryUnlinkResponse,
    LibrarianDeleteResponse
)

from .library import (
    LibraryCreate,
    LibraryUpdate,
    LibraryRead,
    LibrarySearchResponse,
    LibraryDeleteResponse,
    LibraryDeleteWarning
)

from .loan import (
    LoanCreate,
    LoanUpdate,
    LoanBook,
    LoanReader,
    LoanLibrary,
    LoanRead,
    LoanSearchRead,
    LoanSearchResponse,
    LoanDeleteResponse,
    LoanDeleteWarning,
    ReaderLoanRead,
    ReaderLoanSearchResponse,
    LoanDeleteResponse
)

from .metrics import (
    SystemMetrics,
    AuditLogResponse,
    AuditLogsResponse
)

from .publisher import (
    PublisherCreate,
    PublisherUpdate,
    PublisherRead,
    PublisherSearch,
    PublisherListResponse,
    PublisherDeleteResponse
)

from .reader import (
    ReaderCreate,
    ReaderUpdate,
    ReaderRead,
    ReaderSearchResponse,
    ReaderDeleteResponse
)

from .shelf import (
    ShelfCreate,
    ShelfUpdate,
    ShelfRead,
    ShelfSearchResponse,
    ShelfDeleteResponse
)