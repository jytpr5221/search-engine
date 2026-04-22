import json
from pathlib import Path
from fastapi import HTTPException


class FilterController:
    """Handle filter options extraction from books data"""
    
    def __init__(self):
        self.books_json_path = Path(__file__).parent.parent.parent / "books.json"
    
    async def get_filter_options(self):
        """
        Extract and return all unique authors, publishers, categories, and languages from books.json
        Returns: {
            "authors": [...],
            "publishers": [...],
            "categories": [...],
            "languages": [...]
        }
        """
        try:
            with open(self.books_json_path, 'r') as f:
                books = json.load(f)
            
            authors = set()
            publishers = set()
            categories = set()
            languages = set()
            
            for book in books:
                # Extract authors (handle both string and list)
                book_authors = book.get('authors', [])
                if isinstance(book_authors, list):
                    # Filter out empty strings and None values
                    authors.update([a for a in book_authors if a])
                elif isinstance(book_authors, str) and book_authors:
                    authors.add(book_authors)
                
                # Extract publisher
                publisher = book.get('publisher')
                if publisher:
                    publishers.add(str(publisher))
                
                # Extract categories (handle both string and list)
                book_categories = book.get('categories', [])
                if isinstance(book_categories, list):
                    # Filter out empty strings and None values
                    categories.update([c for c in book_categories if c])
                elif isinstance(book_categories, str) and book_categories:
                    categories.add(book_categories)
                
                # Extract language
                language = book.get('language')
                if language:
                    languages.add(language)
            
            return {
                "authors": sorted(list(authors)),
                "publishers": sorted(list(publishers)),
                "categories": sorted(list(categories)),
                "languages": sorted(list(languages))
            }
        
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="Books data file not found")
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Error parsing books data")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving filter options: {str(e)}")


filter_controller = FilterController()
