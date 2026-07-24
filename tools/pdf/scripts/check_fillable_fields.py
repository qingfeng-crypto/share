import sys
from pypdf import PdfReader


def has_fillable_fields(pdf_path: str) -> bool:
    reader = PdfReader(pdf_path)
    return reader.get_fields() is not None


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python check_fillable_fields.py <pdf_path>")
        return 1
    try:
        path = sys.argv[1]
        if has_fillable_fields(path):
            print("This PDF has fillable form fields")
        else:
            print("This PDF does not have fillable form fields; you will need to visually determine where to enter data")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
