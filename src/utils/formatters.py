# ==============================================
#  Formatters help functions to work with data
# ==============================================

# Format the full name
def format_full_name(name: str) -> str:
    return " ".join(part.capitalize() for part in name.strip().split())


# Format the library
def format_library(lib):
    return {
        "id": lib.id,
        "name": " ".join(part.capitalize() for part in lib.name.strip().split()),
        "city": lib.city.strip().title(),
    }


# Format the librarian
def format_librarian(l):
    return {
        "id": l.id,
        "full_name": format_full_name(l.full_name),
        "email": l.email,
    }