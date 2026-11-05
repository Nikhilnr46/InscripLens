with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    text = f.read()

old_snippet = """>
                              \u0c95\u0ca8\u0ccd\u0ca8\u0ca1
                            </button>"""

new_snippet = """>
                              Kannada
                            </button>"""

assert old_snippet in text, "old_snippet not found"
text = text.replace(old_snippet, new_snippet, 1)

with open("frontend/src/App.jsx", "w", encoding="utf-8", newline="\r\n") as f:
    f.write(text)

print("Updated button text successfully")

