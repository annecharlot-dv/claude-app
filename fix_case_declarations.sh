#!/bin/bash
FILE="frontend/src/components/cms/CoworkingPageBuilder.js"

# Make a backup
cp "$FILE" "$FILE.backup"

# Fix each case by adding braces
sed -i '
/case.*:$/{
  N
  s/case \([^:]*\):\n        const/case \1: {\n        const/
}
' "$FILE"

# Add closing braces before the next case or default
sed -i '
/^        return ($/,/^        );$/{
  /^        );$/{
    a\        }
  }
}
' "$FILE"

echo "Fixed case declarations. Original backed up as $FILE.backup"
