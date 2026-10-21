from lark.exceptions import (
    UnexpectedInput,
    UnexpectedCharacters,
    UnexpectedToken,
    UnexpectedEOF,
)


class MapError(Exception):
    """Report a map read or syntax error in user-facing terms."""

    @staticmethod
    def from_file(error: OSError | UnicodeError, file: str) -> "MapError":
        """Convert a file read or decoding failure into a map error."""
        if isinstance(error, OSError):
            return MapError(f"Could not read file: {file}")
        return MapError(f"File is not valid UTF-8 text: {file}")

    @staticmethod
    def from_lark(error: UnexpectedInput, map_text: str) -> "MapError":
        """Return a map error for ``error`` with context from ``map_text``."""
        if isinstance(error, UnexpectedCharacters):
            if error.allowed == {"SIGNED_INT"}:
                context = error.get_context(map_text)
                message = f"Line {error.line}: expected an int.\n{context}"
                return MapError(message)
            elif error.allowed == {"CNAME"}:
                context = error.get_context(map_text)
                message = (
                        f"Line {error.line}: expected a valid name.\n{context}"
                        )
                return MapError(message)
            else:
                context = error.get_context(map_text)
                message = (
                    f"Line {error.line}: invalid syntax.\n{context}")
                return MapError(message)

        elif isinstance(error, UnexpectedToken):
            context = error.get_context(map_text)
            message = (
                f"Line {error.line}: invalid syntax.\n"
                f"{context}"
            )
            return MapError(message)

        elif isinstance(error, UnexpectedEOF):
            line = 1 if not map_text.strip() else map_text.count("\n") + 1
            has_content = any(
                text.split("#", 1)[0].strip()
                for text in map_text.splitlines()
            )
            if not has_content:
                message = (
                    f"Line {line}: expected 'nb_drones: <positive_integer>' "
                    "before end of file."
                )
            else:
                message = (
                    f"Line {line}: unexpected end of file; "
                    "expected a hub or connection definition."
                )
            return MapError(message)

        return MapError(f"Line {error.line}: unknown parsing error.")
