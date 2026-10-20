from lark.exceptions import (
    UnexpectedInput,
    UnexpectedCharacters,
    UnexpectedToken,
    UnexpectedEOF,
)


class MapError(Exception):
    @staticmethod
    def from_file(error: OSError | UnicodeError, file: str) -> "MapError":
        if isinstance(error, OSError):
            return MapError(f"Could not read file: {file}")
        return MapError(f"File is not valid UTF-8 text: {file}")

    @staticmethod
    def from_lark(error: UnexpectedInput, map_text: str) -> "MapError":
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
            message = "Unexpected end of file."
            return MapError(message)

        return MapError(f"Line {error.line}: unknown parsing error.")
