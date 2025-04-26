#!/bin/bash

# Script to normalize PDF filenames in the docs directory
# - Replace all special characters with whitespaces
# - Replace all whitespaces with dashes
# - Convert all characters to lowercase
# - Creates new files and keeps originals
# - Shows all planned changes and asks for confirmation once with y/n
# - Option to delete original files after successful renaming
# - Handles edge cases for file conflicts

DOCS_DIR="docs"

# Check if docs directory exists
if [ ! -d "$DOCS_DIR" ]; then
    echo "Error: Directory '$DOCS_DIR' not found."
    exit 1
fi

# Create temporary files to store the file paths
temp_original=$(mktemp)
temp_normalized=$(mktemp)
temp_success=$(mktemp)

# Find all PDF files and prepare rename list
find "$DOCS_DIR" -type f -name "*.pdf" | while read -r file; do
    # Get the directory and filename parts
    dir=$(dirname "$file")
    filename=$(basename "$file")
    extension="${filename##*.}"
    filename="${filename%.*}"
    
    # Normalize the filename:
    # 1. Convert to lowercase
    new_filename=$(echo "$filename" | tr '[:upper:]' '[:lower:]')
    
    # 2. Replace all special characters (including dashes) with spaces
    new_filename=$(echo "$new_filename" | sed 's/[^a-z0-9\.]/ /g')
    
    # 3. Replace multiple spaces with a single space
    new_filename=$(echo "$new_filename" | tr -s ' ')
    
    # 4. Replace all spaces with dashes
    new_filename=$(echo "$new_filename" | sed 's/ /-/g')
    
    # 5. Remove leading and trailing dashes
    new_filename=$(echo "$new_filename" | sed 's/^-//; s/-$//')
    
    # Create the new file path
    new_file="$dir/$new_filename.$extension"
    
    # Only add to list if the name would change
    if [ "$file" != "$new_file" ]; then
        echo "$file" >> "$temp_original"
        echo "$new_file" >> "$temp_normalized"
    fi
done

# Check for potential conflicts
potential_conflicts=false
declare -A normalized_count
while read -r new_file; do
    normalized_count["$new_file"]=$((normalized_count["$new_file"] + 1))
    # Also check if file already exists but is not in our original list
    if [ -f "$new_file" ] && ! grep -q "^$new_file$" "$temp_original"; then
        echo "Warning: '$new_file' already exists and will be overwritten."
        potential_conflicts=true
    fi
done < "$temp_normalized"

# Check for duplicates in normalized names
for new_file in "${!normalized_count[@]}"; do
    if [ "${normalized_count[$new_file]}" -gt 1 ]; then
        echo "Warning: Multiple files will normalize to '$new_file'"
        potential_conflicts=true
    fi
done

# Display all planned changes
echo "The following changes will be made:"
echo "------------------------------------"
paste -d '\n' "$temp_original" "$temp_normalized" | while read -r orig && read -r norm; do
    echo "Original:   '$orig'"
    echo "Normalized: '$norm'"
    echo "------------------------------------"
done

# If there are conflicts, warn the user
if [ "$potential_conflicts" = true ]; then
    echo
    echo "CAUTION: Potential file conflicts detected (see warnings above)."
    echo "Proceeding may result in data loss as some files may be overwritten."
    echo
fi

# Ask for confirmation once for all changes
echo
read -p "Do you want to apply all these changes? (y/n): " -r REPLY
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Apply all changes
    paste "$temp_original" "$temp_normalized" | while read -r orig norm; do
        # Only proceed if destination doesn't match source
        if [ "$orig" != "$norm" ]; then
            # Handle case where normalized name already exists
            if [ -f "$norm" ] && [ "$orig" != "$norm" ]; then
                echo "Warning: '$norm' already exists. Creating backup with timestamp."
                timestamp=$(date +%Y%m%d%H%M%S)
                mv "$norm" "${norm%.pdf}_backup_${timestamp}.pdf"
            fi
            
            echo "Creating new file: '$norm'"
            if cp "$orig" "$norm"; then
                # Record successful copy
                echo "$orig" >> "$temp_success"
            else
                echo "Error: Failed to copy '$orig' to '$norm'"
            fi
        fi
    done
    
    # Count successful operations
    success_count=$(wc -l < "$temp_success")
    total_count=$(wc -l < "$temp_original")
    
    echo "Normalized $success_count out of $total_count files."
    
    # Ask if user wants to remove original files
    if [ "$success_count" -gt 0 ]; then
        echo
        read -p "Do you want to remove the original files? (y/n): " -r REPLY
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Only remove files that were successfully copied
            cat "$temp_success" | while read -r orig; do
                echo "Removing original file: '$orig'"
                rm "$orig"
            done
            echo "Original files have been removed."
        else
            echo "Original files preserved."
        fi
    fi
else
    echo "Operation cancelled. No files were modified."
fi

# Clean up temporary files
rm "$temp_original" "$temp_normalized" "$temp_success"

echo "PDF filename normalization complete."
